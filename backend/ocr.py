"""
  (1) TIỀN XỬ LÝ   : đọc ảnh, xoay theo EXIF, thu nhỏ nếu quá lớn, tăng tương phản.
  (2) MODEL (OCR)  : PaddleOCR model đọc toàn bộ chữ trên ảnh.
  (3) HẬU XỬ LÝ    : làm sạch các dòng text (bỏ khoảng trắng thừa, dòng rỗng).
  (4) TRÍCH XUẤT   : Lấy 4 trường: số CCCD, họ tên, ngày sinh, địa chỉ.
  (5) OUTPUT       : trả JSON các trường + danh sách dòng OCR thô (để đối chiếu).

      Ảnh CCCD ─► Tiền xử lý─► PaddleOCR ─► Dòng text ─► Làm sạch ─► Regex ─► JSON

Endpoints:
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

OCR_LANG = os.environ.get("OCR_LANG", "vi") 
MAX_SIDE = 1600  # giới hạn cạnh dài của ảnh để OCR nhanh

# PaddleOCR model lazy loads
_engine = None
_engine_error = ""


def _get_engine():
    global _engine, _engine_error
    if _engine is None and not _engine_error:
        try:
            from paddleocr import PaddleOCR

            _engine = PaddleOCR(lang=OCR_LANG, use_textline_orientation=False)
        except Exception as e: 
            _engine_error = (
                "Chưa cài được PaddleOCR (cần Python <= 3.13 + `pip install -r "
                "requirements-ocr.txt`). Bạn vẫn có thể nhập tay thông tin để đăng ký. "
                f"Chi tiết: {e}"
            )
    return _engine


# Tiền xl ảnh
def preprocess_pil(image_bytes: bytes):
    from PIL import Image, ImageOps

    img = Image.open(io.BytesIO(image_bytes))
    img = ImageOps.exif_transpose(img)      # ảnh chụp điện thoại thường xoay theo EXIF
    img = img.convert("RGB")

    # Thu nhỏ nếu cạnh dài vượt ngưỡng, tránh OCR chậm
    long_side = max(img.size)
    if long_side > MAX_SIDE:
        scale = MAX_SIDE / long_side
        img = img.resize((int(img.width * scale), int(img.height * scale)))

    img = ImageOps.autocontrast(img)        # kéo giãn tương phản cho chữ rõ hơn
    return img


def preprocess(image_bytes: bytes) -> str:
    img = preprocess_pil(image_bytes)
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    img.save(tmp.name)
    return tmp.name


# HẬU XỬ LÝ — làm sạch danh sách dòng text
def postprocess(lines: list[str]) -> list[str]:
    cleaned = []
    for ln in lines:
        ln = re.sub(r"\s+", " ", ln).strip()
        if ln:
            cleaned.append(ln)
    return cleaned


# (4) TRÍCH XUẤT THÔNG TIN — heuristic/regex cho các trường CCCD
_DATE_RE = re.compile(r"\b(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})\b")


def _value_below_label(lines: list[str], keywords: list[str]) -> str:
    """Lấy giá trị 1 trường CCCD: nhãn đứng riêng dòng, giá trị nằm ở DÒNG DƯỚI
    (hoặc sau dấu ':' nếu cùng dòng). Khớp nhãn không dấu."""
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
    """Lấy 4 trường: số CCCD (dãy 9/12 số), ngày sinh (dd/mm/yyyy), họ tên & địa chỉ
    (giá trị nằm dưới nhãn)."""
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
        lines, ["noi thuong tru", "thuong tru", "noi cu tru", "place of residence"]
    )

    return {
        "id_number": id_number,
        "full_name": full_name,
        "dob": dob,
        "address": address,
    }


# (5) OUTPUT — endpoint quét ảnh
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


# ĐĂNG KÝ KHÁM — gợi ý khoa theo lý do + cấp số thứ tự ảo
_queue_counters: dict[str, int] = {}


def _suggest_department(reason: str) -> dict:
    """Gợi ý khoa từ lý do khám: đếm từ khoá/triệu chứng mỗi khoa xuất hiện trong lý do,
    chọn khoa nhiều nhất; không khớp -> Quầy Tiếp đón."""
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
