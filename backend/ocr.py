"""Hướng B — OCR quét Căn cước công dân (CCCD) để đăng ký khám nhanh.

Pipeline (đúng các bước đề yêu cầu), bản cơ bản, KHÔNG train model:

  (1) TIỀN XỬ LÝ   : đọc ảnh, xoay theo EXIF, thu nhỏ nếu quá lớn, tăng tương phản.
  (2) MODEL (OCR)  : PaddleOCR (PP-OCRv*, tiếng Việt) đọc toàn bộ chữ trên ảnh.
  (3) HẬU XỬ LÝ    : làm sạch các dòng text (bỏ khoảng trắng thừa, dòng rỗng).
  (4) TRÍCH XUẤT   : dùng heuristic/regex lấy 4 trường: số CCCD, họ tên, ngày sinh, địa chỉ.
  (5) OUTPUT       : trả JSON các trường + danh sách dòng OCR thô (để đối chiếu).

      Ảnh CCCD ─►(1)tiền xử lý─►(2)PaddleOCR─► dòng text ─►(3)làm sạch─►(4)regex ─► JSON

Vì PaddlePaddle CHƯA có bản cho Python 3.14, engine được import "lười" (lazy): nếu chưa
cài được, endpoint /scan trả lỗi rõ ràng nhưng phần đăng ký (điền tay) vẫn dùng được.

Endpoints (đăng ký dưới /api/ocr):
  POST /api/ocr/scan      (multipart: image)  -> { fields, raw_lines }
  POST /api/ocr/register  (JSON form + reason) -> { queue_number, department, directions }
"""

from __future__ import annotations

import io
import os
import re
import tempfile

from flask import Blueprint, jsonify, request

import repository as repo
from text_utils import normalize, strip_accents

ocr_bp = Blueprint("ocr", __name__)

OCR_LANG = os.environ.get("OCR_LANG", "vi")  # PaddleOCR hỗ trợ tiếng Việt
MAX_SIDE = 1600  # giới hạn cạnh dài của ảnh để OCR nhanh, ổn định


# ==========================================================================
# (2) MODEL — PaddleOCR (khởi tạo lười, dùng lại 1 lần để khỏi load lại)
# ==========================================================================
_engine = None
_engine_error = ""


def _get_engine():
    """Tạo PaddleOCR một lần. Nếu chưa cài được thư viện -> trả None + lưu lý do."""
    global _engine, _engine_error
    if _engine is None and not _engine_error:
        try:
            from paddleocr import PaddleOCR

            _engine = PaddleOCR(lang=OCR_LANG, use_textline_orientation=False)
        except Exception as e:  # ImportError (chưa cài) hoặc lỗi khởi tạo
            _engine_error = (
                "Chưa cài được PaddleOCR (cần Python <= 3.13 + `pip install -r "
                "requirements-ocr.txt`). Bạn vẫn có thể nhập tay thông tin để đăng ký. "
                f"Chi tiết: {e}"
            )
    return _engine


# ==========================================================================
# (1) TIỀN XỬ LÝ — chuẩn hoá ảnh trước khi đưa vào OCR
# ==========================================================================
def preprocess_pil(image_bytes: bytes):
    """Trả về ảnh PIL đã tiền xử lý (để tái dùng cho cả OCR lẫn trang debug)."""
    from PIL import Image, ImageOps

    img = Image.open(io.BytesIO(image_bytes))
    img = ImageOps.exif_transpose(img)      # ảnh chụp điện thoại thường xoay theo EXIF
    img = img.convert("RGB")

    # Thu nhỏ nếu cạnh dài vượt ngưỡng (ảnh quá to làm OCR chậm mà không lợi thêm).
    long_side = max(img.size)
    if long_side > MAX_SIDE:
        scale = MAX_SIDE / long_side
        img = img.resize((int(img.width * scale), int(img.height * scale)))

    img = ImageOps.autocontrast(img)        # kéo giãn tương phản cho chữ rõ hơn
    return img


def preprocess(image_bytes: bytes) -> str:
    """Tiền xử lý rồi lưu ra file PNG tạm để PaddleOCR đọc, trả về đường dẫn."""
    img = preprocess_pil(image_bytes)
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    img.save(tmp.name)
    return tmp.name


def _to_data_url(pil_img) -> str:
    """Mã hoá ảnh PIL thành data URL base64 để trả thẳng cho frontend hiển thị."""
    import base64

    buf = io.BytesIO()
    pil_img.save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


# ==========================================================================
# (3) HẬU XỬ LÝ — làm sạch danh sách dòng text
# ==========================================================================
def postprocess(lines: list[str]) -> list[str]:
    cleaned = []
    for ln in lines:
        ln = re.sub(r"\s+", " ", ln).strip()
        if ln:
            cleaned.append(ln)
    return cleaned


# ==========================================================================
# (4) TRÍCH XUẤT THÔNG TIN — heuristic/regex cho các trường CCCD
# ==========================================================================
# Mẫu ngày dd/mm/yyyy (chấp nhận dấu ngăn cách / - .). Dùng cho ngày sinh.
_DATE_RE = re.compile(r"\b(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})\b")


def _value_below_label(lines: list[str], keywords: list[str]) -> str:
    """Lấy GIÁ TRỊ của một trường có nhãn trên CCCD.

    Mấu chốt về bố cục CCCD: dòng NHÃN (vd "Họ và tên / Full name", "Nơi thường trú / ...")
    đứng riêng một dòng, còn GIÁ TRỊ thật nằm ở DÒNG NGAY DƯỚI. Vì vậy hàm làm 3 việc:

      1. Tìm dòng có chứa nhãn — so khớp KHÔNG DẤU (nhờ ``strip_accents``) nên "Họ và tên",
         "ho va ten", "HO VA TEN" đều khớp.
      2. Nếu dòng đó viết kiểu "nhãn: giá trị" (giá trị nằm cùng dòng) -> lấy phần sau ':'.
      3. Nếu không có -> lấy luôn DÒNG KẾ TIẾP làm giá trị.

    Cách này tránh được lỗi cũ (lấy nhầm phần nhãn tiếng Anh "Full name") mà vẫn rất gọn.
    """
    for i, line in enumerate(lines):
        line_no_accent = strip_accents(line)
        if not any(kw in line_no_accent for kw in keywords):
            continue
        if ":" in line:                          # (2) giá trị cùng dòng, sau dấu ':'
            after = line.split(":", 1)[1].strip()
            if after:
                return after
        if i + 1 < len(lines):                   # (3) giá trị ở dòng kế tiếp
            return lines[i + 1].strip()
        return ""
    return ""


def extract_fields(lines: list[str]) -> dict:
    """Lấy 4 trường cần cho đăng ký khám: số CCCD, họ tên, ngày sinh, địa chỉ.

    Mỗi trường một cách lấy đơn giản, dễ giải thích:
      - Số CCCD  : dòng nào (sau khi bỏ ký tự không phải số) còn đúng 9 hoặc 12 chữ số.
      - Ngày sinh: mẫu ngày dd/mm/yyyy đầu tiên trong toàn bộ chữ đọc được.
      - Họ tên   : giá trị nằm dưới nhãn "Họ và tên / Full name".
      - Địa chỉ  : giá trị nằm dưới nhãn "Nơi thường trú / Place of residence".
    """
    # Số CCCD: CMND cũ 9 số, CCCD 12 số.
    id_number = ""
    for line in lines:
        digits = re.sub(r"\D", "", line)         # bỏ mọi ký tự không phải chữ số
        if len(digits) in (9, 12):
            id_number = digits
            break

    # Ngày sinh: tìm mẫu ngày đầu tiên trong toàn văn bản.
    dob = ""
    match = _DATE_RE.search("\n".join(lines))
    if match:
        day, month, year = match.groups()
        dob = f"{int(day):02d}/{int(month):02d}/{year}"

    # Họ tên & Địa chỉ: giá trị nằm ở dòng dưới nhãn (xem _value_below_label).
    full_name = _value_below_label(lines, ["ho va ten", "ho ten", "full name"])
    address = _value_below_label(
        lines, ["noi thuong tru", "thuong tru", "noi cu tru", "place of residence", "dia chi"]
    )

    return {
        "id_number": id_number,
        "full_name": full_name,
        "dob": dob,
        "address": address,
    }


# ==========================================================================
# (5) OUTPUT — endpoint quét ảnh
# ==========================================================================
@ocr_bp.route("/scan", methods=["POST"])
def scan():
    file = request.files.get("image")
    if file is None or not file.filename:
        return jsonify({"error": "Chưa có ảnh. Gửi file ở trường 'image'."}), 400

    engine = _get_engine()
    if engine is None:
        return jsonify({"status": "error", "message": _engine_error}), 503

    tmp_path = preprocess(file.read())
    try:
        result = engine.predict(tmp_path)          # (2) chạy OCR
        raw = list(result[0]["rec_texts"]) if result else []
    except Exception as e:
        return jsonify({"status": "error", "message": f"Lỗi OCR: {e}"}), 500
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    lines = postprocess(raw)                        # (3) làm sạch
    fields = extract_fields(lines)                  # (4) trích xuất
    return jsonify({"status": "success", "fields": fields, "raw_lines": lines})


def _poly_to_points(poly) -> list[list[int]]:
    """Đưa 1 vùng (polygon 4 điểm, hoặc box [x1,y1,x2,y2]) về danh sách điểm [[x,y],...]."""
    pts = list(poly)
    if len(pts) == 4 and all(not hasattr(p, "__len__") for p in pts):
        x1, y1, x2, y2 = (int(v) for v in pts)  # box dạng [x1,y1,x2,y2]
        return [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
    return [[int(p[0]), int(p[1])] for p in pts]  # polygon 4 điểm


@ocr_bp.route("/debug", methods=["POST"])
def debug():
    """Trả về TỪNG BƯỚC của pipeline để xem trực quan trên UI:

    - preprocessed_image : ảnh sau tiền xử lý (data URL)
    - annotated_image    : ảnh có vẽ bounding box + số thứ tự từng vùng chữ
    - boxes              : [{index, text, score, box}] — kết quả model (chưa làm sạch)
    - raw_lines          : các dòng chữ thô từ model
    - cleaned_lines      : sau hậu xử lý
    - fields             : sau trích xuất
    """
    file = request.files.get("image")
    if file is None or not file.filename:
        return jsonify({"error": "Chưa có ảnh. Gửi file ở trường 'image'."}), 400

    engine = _get_engine()
    if engine is None:
        return jsonify({"status": "error", "message": _engine_error}), 503

    from PIL import ImageDraw

    # (1) Tiền xử lý — giữ lại ảnh PIL để vừa OCR vừa vẽ minh hoạ.
    pre_img = preprocess_pil(file.read())
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    pre_img.save(tmp.name)
    try:
        result = engine.predict(tmp.name)           # (2) chạy OCR
    except Exception as e:
        return jsonify({"status": "error", "message": f"Lỗi OCR: {e}"}), 500
    finally:
        try:
            os.remove(tmp.name)
        except OSError:
            pass

    res = result[0] if result else {}
    texts = list(res.get("rec_texts", []))
    scores = list(res.get("rec_scores", []))
    polys = list(res.get("rec_polys", [])) or list(res.get("rec_boxes", []))

    # Vẽ bounding box + số thứ tự lên bản sao ảnh tiền xử lý.
    annotated = pre_img.copy()
    draw = ImageDraw.Draw(annotated)
    boxes = []
    for i, text in enumerate(texts):
        score = float(scores[i]) if i < len(scores) else 0.0
        pts = _poly_to_points(polys[i]) if i < len(polys) else []
        if pts:
            draw.line([tuple(p) for p in pts] + [tuple(pts[0])], fill=(2, 132, 199), width=3)
            draw.text((pts[0][0], max(0, pts[0][1] - 12)), str(i + 1), fill=(220, 38, 38))
        boxes.append({"index": i + 1, "text": text, "score": round(score, 3), "box": pts})

    # (3) hậu xử lý + (4) trích xuất
    cleaned = postprocess(texts)
    fields = extract_fields(cleaned)

    return jsonify({
        "status": "success",
        "preprocessed_image": _to_data_url(pre_img),
        "annotated_image": _to_data_url(annotated),
        "boxes": boxes,
        "raw_lines": texts,
        "cleaned_lines": cleaned,
        "fields": fields,
    })


# ==========================================================================
# ĐĂNG KÝ KHÁM — gợi ý khoa theo lý do + cấp số thứ tự ảo
# ==========================================================================
# Bộ đếm số thứ tự theo từng khoa (trong bộ nhớ, reset khi restart — đủ cho demo).
_queue_counters: dict[str, int] = {}


def _suggest_department(reason: str) -> dict:
    """Gợi ý khoa từ lý do khám (thường là cả câu).

    Đếm xem từ khoá/triệu chứng của mỗi khoa xuất hiện trong lý do bao nhiêu lần,
    chọn khoa nhiều nhất. Cách này hợp với câu dài (vd "tôi bị đau ngực, khó thở")
    hơn so với tìm-kiếm-chuỗi-con vốn cần khớp nguyên cụm. Không khớp -> Quầy Tiếp đón.
    """
    reason_norm = normalize(reason)  # bỏ dấu + bỏ khoảng trắng
    best, best_score = None, 0
    for dep in repo.get_all():
        score = 0
        for kw in [*dep.get("keywords", []), *dep.get("symptoms", [])]:
            kw_norm = normalize(kw)
            if kw_norm and kw_norm in reason_norm:
                score += 1
        if score > best_score:
            best, best_score = dep, score
    return best or repo.get_by_id("tiep-don")


@ocr_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    full_name = (data.get("full_name") or "").strip()
    reason = (data.get("reason") or "").strip()
    if not full_name:
        return jsonify({"error": "Thiếu họ tên."}), 400
    if not reason:
        return jsonify({"error": "Thiếu lý do khám."}), 400

    # Gợi ý khoa từ lý do khám (khớp theo từ khoá/triệu chứng); không thấy -> Tiếp đón.
    dep = _suggest_department(reason)

    # Cấp số thứ tự ảo theo khoa.
    _queue_counters[dep["id"]] = _queue_counters.get(dep["id"], 0) + 1
    number = _queue_counters[dep["id"]]
    queue_number = f"{dep['building']}{dep['floor']}-{number:03d}"

    return jsonify({
        "status": "success",
        "queue_number": queue_number,
        "patient": {"full_name": full_name, "reason": reason},
        "department": {
            "id": dep["id"],
            "name": dep["name"],
            "buildingName": repo.building_name(dep["building"]),
            "floor": dep["floor"],
            "room": dep["room"],
            "hours": dep["hours"],
        },
        "directions": dep.get("directions", []),
    })
