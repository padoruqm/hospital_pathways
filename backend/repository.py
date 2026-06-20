"""Lớp truy cập dữ liệu (repository) — mọi thao tác trên dữ liệu khoa/phòng.

``app.py`` (tầng web) chỉ gọi các hàm ở đây, không đụng trực tiếp vào danh sách dữ
liệu. Repository thao tác trên ``hospital_data.DEPARTMENTS`` và dùng ``text_utils`` để
chuẩn hoá chuỗi khi tìm kiếm.

Gồm 4 nhóm việc:
  1. Đọc dữ liệu       : get_all, get_by_id
  2. Tìm kiếm          : search
  3. Thêm/sửa/xoá      : validate, create_department, update_department, delete_department
  4. Thống kê lượt xem : record_view, get_stats

Dữ liệu nằm trong bộ nhớ nên thay đổi (CRUD) có hiệu lực ngay trong phiên chạy và sẽ
reset khi khởi động lại server — đủ cho demo và giữ code đơn giản.
"""

from __future__ import annotations

from hospital_data import BUILDINGS, DEPARTMENTS
from text_utils import normalize, strip_accents

# Đếm số lượt xem chi tiết theo từng khoa (phục vụ thống kê ở admin).
_view_counts: dict[str, int] = {}

REQUIRED_FIELDS = ("name", "category", "building", "floor", "room", "hours", "description")


# --- 1. Đọc dữ liệu -------------------------------------------------------
def get_all() -> list[dict]:
    return DEPARTMENTS


def get_by_id(dep_id: str) -> dict | None:
    return next((d for d in DEPARTMENTS if d["id"] == dep_id), None)


def building_name(code: str) -> str:
    return BUILDINGS.get(code, code)


# --- 2. Tìm kiếm ----------------------------------------------------------
def _searchable_text(dep: dict) -> str:
    """Gộp các trường tìm kiếm của một khoa rồi chuẩn hoá thành 1 chuỗi để so khớp."""
    parts = [dep["name"], dep["category"], dep["room"], *dep["keywords"], *dep.get("symptoms", [])]
    return normalize(" ".join(parts))


def search(query: str, limit: int = 10) -> list[dict]:
    """Tìm kiếm đơn giản: khoa nào CHỨA cụm tìm kiếm thì khớp.

    Quy tắc gọn, dễ giải thích:
      1. Chuẩn hoá truy vấn và dữ liệu như nhau (bỏ dấu, bỏ khoảng trắng/ký tự đặc biệt).
      2. Khoa khớp nếu chuỗi truy vấn là **chuỗi con** trong phần dữ liệu tìm kiếm được.
      3. Khoa khớp ngay ở **tên** thì xếp lên trước.

    Nhờ so khớp nguyên cụm, "đau đầu" chỉ khớp khoa có cụm "đau đầu" (Nội thần kinh),
    còn "đau bụng" khớp khoa có cụm "đau bụng" (Nội tổng quát, Sản) — không lẫn nhau.
    """
    q = normalize(query)
    if not q:
        return []

    matches: list[tuple[int, dict]] = []
    for dep in DEPARTMENTS:
        if q in _searchable_text(dep):
            in_name = q in normalize(dep["name"])
            matches.append((0 if in_name else 1, dep))  # 0 = khớp ở tên -> ưu tiên

    matches.sort(key=lambda pair: pair[0])
    return [dep for _, dep in matches[:limit]]


# --- 3. Thêm / sửa / xoá --------------------------------------------------
def validate(payload: dict) -> list[str]:
    """Kiểm tra dữ liệu đầu vào, trả về danh sách lỗi (rỗng nếu hợp lệ)."""
    errors: list[str] = []
    for field in REQUIRED_FIELDS:
        value = payload.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            errors.append(f"Thiếu trường bắt buộc: {field}")
    floor = payload.get("floor")
    if floor is not None and not isinstance(floor, bool):
        try:
            int(floor)
        except (TypeError, ValueError):
            errors.append("Trường 'floor' phải là số")
    return errors


def _slugify(text: str) -> str:
    """Sinh id (slug) từ tên: 'Khoa Tim mạch' -> 'khoa-tim-mach'."""
    base = strip_accents(text)
    slug = "".join(ch if ch.isalnum() else "-" for ch in base)
    slug = "-".join(part for part in slug.split("-") if part)  # gộp dấu - thừa
    return slug or "khoa"


def _unique_id(base_slug: str) -> str:
    """Đảm bảo id không trùng bằng cách thêm hậu tố số nếu cần."""
    slug = base_slug
    i = 2
    while get_by_id(slug) is not None:
        slug = f"{base_slug}-{i}"
        i += 1
    return slug


def _normalize_payload(payload: dict) -> dict:
    """Chuẩn hoá payload thành 1 bản ghi khoa đầy đủ trường."""
    return {
        "name": str(payload["name"]).strip(),
        "category": str(payload["category"]).strip(),
        "building": str(payload["building"]).strip(),
        "floor": int(payload["floor"]),
        "room": str(payload["room"]).strip(),
        "hours": str(payload["hours"]).strip(),
        "description": str(payload["description"]).strip(),
        "keywords": [s.strip() for s in payload.get("keywords", []) if str(s).strip()],
        "symptoms": [s.strip() for s in payload.get("symptoms", []) if str(s).strip()],
        "directions": [s.strip() for s in payload.get("directions", []) if str(s).strip()],
        "pos": {
            "x": float(payload.get("pos", {}).get("x", 50)),
            "y": float(payload.get("pos", {}).get("y", 30)),
        },
    }


def create_department(payload: dict) -> dict:
    dep = _normalize_payload(payload)
    dep["id"] = _unique_id(_slugify(dep["name"]))
    DEPARTMENTS.append(dep)
    return dep


def update_department(dep_id: str, payload: dict) -> dict | None:
    dep = get_by_id(dep_id)
    if dep is None:
        return None
    updated = _normalize_payload(payload)
    updated["id"] = dep_id  # giữ nguyên id cũ
    dep.clear()
    dep.update(updated)
    return dep


def delete_department(dep_id: str) -> bool:
    dep = get_by_id(dep_id)
    if dep is None:
        return False
    DEPARTMENTS.remove(dep)
    _view_counts.pop(dep_id, None)
    return True


# --- 4. Thống kê lượt xem -------------------------------------------------
def record_view(dep_id: str) -> None:
    _view_counts[dep_id] = _view_counts.get(dep_id, 0) + 1


def get_stats() -> list[dict]:
    """Thống kê lượt xem theo khoa, sắp giảm dần."""
    rows = [
        {"id": d["id"], "name": d["name"], "views": _view_counts.get(d["id"], 0)}
        for d in DEPARTMENTS
    ]
    rows.sort(key=lambda r: r["views"], reverse=True)
    return rows
