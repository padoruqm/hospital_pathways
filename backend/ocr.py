"""Hướng B — OCR quét Căn cước công dân (CCCD) để đăng ký khám nhanh.

Pipeline (đúng các bước đề yêu cầu), bản cơ bản, KHÔNG train model:

  (1) TIỀN XỬ LÝ   : đọc ảnh, xoay theo EXIF, thu nhỏ nếu quá lớn, tăng tương phản.
  (2) MODEL (OCR)  : PaddleOCR (PP-OCRv*, tiếng Việt) đọc toàn bộ chữ trên ảnh.
  (3) HẬU XỬ LÝ    : làm sạch các dòng text (bỏ khoảng trắng thừa, dòng rỗng).
  (4) TRÍCH XUẤT   : dùng heuristic/regex lấy các trường: số CCCD, họ tên, ngày sinh,
                     giới tính, quốc tịch, quê quán, nơi thường trú.
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
def preprocess(image_bytes: bytes) -> str:
    """Mở ảnh, xoay đúng chiều (EXIF), thu nhỏ nếu quá lớn, tăng tương phản.

    Trả về đường dẫn file PNG tạm để PaddleOCR đọc (đường dẫn ổn định hơn ndarray).
    """
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

    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    img.save(tmp.name)
    return tmp.name


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
_DATE_RE = re.compile(r"\b(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})\b")


def _after_label(lines: list[str], labels: list[str]) -> str:
    """Tìm dòng có chứa một trong các nhãn (so khớp không dấu), trả phần SAU dấu ':'.

    Nếu không có ':' thì trả phần text sau nhãn. Trả "" nếu không tìm thấy.
    """
    for ln in lines:
        norm = strip_accents(ln)
        for label in labels:
            pos = norm.find(label)
            if pos != -1:
                rest = ln[pos + len(label):]
                if ":" in rest:
                    rest = rest.split(":", 1)[1]
                return rest.strip(" :.-")
    return ""


def extract_fields(lines: list[str]) -> dict:
    """Lấy các trường chính từ các dòng OCR (bản heuristic, đủ dùng để demo)."""
    full_text = "\n".join(lines)

    # Số CCCD: dòng nào gồm toàn chữ số sau khi bỏ ký tự khác, dài 9 hoặc 12.
    id_number = ""
    for ln in lines:
        digits = re.sub(r"\D", "", ln)
        if len(digits) in (9, 12):
            id_number = digits
            break

    # Ngày sinh: mẫu dd/mm/yyyy đầu tiên trong toàn văn bản.
    dob = ""
    m = _DATE_RE.search(full_text)
    if m:
        dob = f"{int(m.group(1)):02d}/{int(m.group(2)):02d}/{m.group(3)}"

    # Họ tên: theo nhãn "Họ và tên / Họ tên / Full name".
    full_name = _after_label(lines, ["ho va ten", "ho ten", "full name"])

    # Giới tính: lấy đoạn ngay sau nhãn "Giới tính/Sex" để tránh dính "VIỆT NAM".
    sex = ""
    sex_seg = _after_label(lines, ["gioi tinh", "sex"])
    seg_norm = strip_accents(sex_seg)
    if seg_norm.startswith("nu") or " nu" in f" {seg_norm}":
        sex = "Nữ"
    elif "nam" in seg_norm or "male" in seg_norm:
        sex = "Nam"

    nationality = _after_label(lines, ["quoc tich", "nationality"])
    # Nếu quốc tịch dính chung dòng với giới tính, cắt lại cho gọn.
    nationality = re.split(r"\s{2,}", nationality)[0].strip()

    hometown = _after_label(lines, ["que quan", "place of origin"])
    residence = _after_label(lines, ["noi thuong tru", "thuong tru", "noi cu tru", "place of residence", "residence"])

    return {
        "id_number": id_number,
        "full_name": full_name,
        "dob": dob,
        "sex": sex,
        "nationality": nationality,
        "hometown": hometown,
        "residence": residence,
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
