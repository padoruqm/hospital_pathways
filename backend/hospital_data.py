"""Dữ liệu bệnh viện (mock) + tiện ích tìm kiếm.

Đây là "nguồn sự thật" cho toàn bộ web ở Giai đoạn 1. Dữ liệu được mock thủ công
nhưng có cấu trúc đầy đủ để các giai đoạn sau dùng lại được:

- ``keywords`` / ``symptoms``  -> phục vụ tìm kiếm và RAG chatbot (Hướng A).
- ``floor`` / ``pos``          -> phục vụ vẽ sơ đồ tầng SVG và đồ thị tìm đường (điểm cộng).
- ``directions``               -> hướng dẫn đường đi từng bước dạng text.

Mỗi phòng có toạ độ ``pos`` (x, y) trong hệ 0..100 của từng tầng để frontend vẽ
sơ đồ mà không cần ảnh thật — sơ đồ chỉ mang tính minh hoạ, có thể thay sau.
"""

from __future__ import annotations

import unicodedata

# Tên các toà nhà trong khuôn viên
BUILDINGS = {
    "A": "Nhà A — Khu khám & chẩn đoán",
    "B": "Nhà B — Khu điều trị & xét nghiệm",
}

# ---------------------------------------------------------------------------
# Danh sách khoa / phòng (mock). Tối thiểu đề yêu cầu 10–15, ở đây để 20 cho
# việc test tìm kiếm có ý nghĩa hơn.
# ---------------------------------------------------------------------------
DEPARTMENTS = [
    {
        "id": "tiep-don",
        "name": "Quầy Tiếp đón & Lấy số",
        "category": "Hành chính",
        "building": "A",
        "floor": 1,
        "room": "101",
        "pos": {"x": 15, "y": 20},
        "hours": "06:30 – 17:00 (T2–T7)",
        "description": "Nơi bệnh nhân đăng ký khám, lấy số thứ tự và được hướng dẫn ban đầu.",
        "keywords": ["tiếp đón", "lấy số", "đăng ký", "thủ tục", "hướng dẫn", "quầy"],
        "symptoms": [],
        "directions": [
            "Vào cửa chính Nhà A",
            "Quầy Tiếp đón nằm ngay bên phải sảnh, cạnh bảng thông tin",
        ],
    },
    {
        "id": "cap-cuu",
        "name": "Khoa Cấp cứu",
        "category": "Cấp cứu",
        "building": "A",
        "floor": 1,
        "room": "110",
        "pos": {"x": 80, "y": 20},
        "hours": "24/7",
        "description": "Tiếp nhận và xử trí các trường hợp khẩn cấp, nguy kịch suốt ngày đêm.",
        "keywords": ["cấp cứu", "khẩn cấp", "tai nạn", "nguy kịch", "ngất", "khó thở nặng"],
        "symptoms": ["đau ngực dữ dội", "khó thở nặng", "chấn thương", "ngất xỉu", "chảy máu nhiều"],
        "directions": [
            "Vào cửa chính Nhà A",
            "Đi thẳng hết sảnh đến cuối hành lang bên phải",
            "Khoa Cấp cứu có lối vào riêng, biển đỏ phòng 110",
        ],
    },
    {
        "id": "noi-tong-quat",
        "name": "Khoa Nội tổng quát",
        "category": "Khám bệnh",
        "building": "A",
        "floor": 2,
        "room": "201",
        "pos": {"x": 20, "y": 30},
        "hours": "07:00 – 16:30 (T2–T7)",
        "description": "Khám và điều trị các bệnh nội khoa thường gặp: tiêu hoá, hô hấp, nội tiết...",
        "keywords": ["nội", "nội tổng quát", "khám tổng quát", "mệt mỏi", "sốt"],
        "symptoms": ["sốt", "mệt mỏi", "đau bụng", "ăn không tiêu", "sút cân"],
        "directions": [
            "Vào cửa chính Nhà A, đi tới thang máy giữa sảnh",
            "Lên tầng 2",
            "Ra khỏi thang máy rẽ trái, phòng 201 ở đầu hành lang",
        ],
    },
    {
        "id": "tim-mach",
        "name": "Khoa Tim mạch",
        "category": "Khám bệnh",
        "building": "A",
        "floor": 2,
        "room": "205",
        "pos": {"x": 45, "y": 30},
        "hours": "07:00 – 16:30 (T2–T7)",
        "description": "Khám, đo điện tim, siêu âm tim và điều trị các bệnh lý tim mạch.",
        "keywords": ["tim", "tim mạch", "huyết áp", "điện tim", "đau ngực", "hồi hộp"],
        "symptoms": ["đau ngực", "hồi hộp đánh trống ngực", "khó thở khi gắng sức", "huyết áp cao", "phù chân"],
        "directions": [
            "Vào cửa chính Nhà A, đi tới thang máy giữa sảnh",
            "Lên tầng 2",
            "Ra khỏi thang máy rẽ trái, đi qua phòng 201, phòng 205 nằm bên phải",
        ],
    },
    {
        "id": "noi-than-kinh",
        "name": "Khoa Nội thần kinh",
        "category": "Khám bệnh",
        "building": "A",
        "floor": 2,
        "room": "208",
        "pos": {"x": 70, "y": 30},
        "hours": "07:00 – 16:30 (T2–T7)",
        "description": "Khám và điều trị đau đầu, đột quỵ, động kinh, rối loạn thần kinh.",
        "keywords": ["thần kinh", "đau đầu", "chóng mặt", "đột quỵ", "động kinh", "tê tay chân"],
        "symptoms": ["đau đầu kéo dài", "chóng mặt", "tê bì tay chân", "co giật", "mất ngủ"],
        "directions": [
            "Vào cửa chính Nhà A, đi tới thang máy giữa sảnh",
            "Lên tầng 2",
            "Ra khỏi thang máy rẽ phải, phòng 208 ở cuối hành lang",
        ],
    },
    {
        "id": "co-xuong-khop",
        "name": "Khoa Cơ xương khớp",
        "category": "Khám bệnh",
        "building": "A",
        "floor": 3,
        "room": "301",
        "pos": {"x": 20, "y": 30},
        "hours": "07:00 – 16:30 (T2–T7)",
        "description": "Khám và điều trị đau khớp, thoái hoá, viêm khớp, đau lưng, cột sống.",
        "keywords": ["cơ xương khớp", "khớp", "đau lưng", "thoái hoá", "cột sống", "đau vai gáy"],
        "symptoms": ["đau khớp", "đau lưng", "đau vai gáy", "cứng khớp buổi sáng", "sưng khớp"],
        "directions": [
            "Vào cửa chính Nhà A, đi tới thang máy giữa sảnh",
            "Lên tầng 3",
            "Ra khỏi thang máy rẽ trái, phòng 301 ngay bên trái",
        ],
    },
    {
        "id": "da-lieu",
        "name": "Khoa Da liễu",
        "category": "Khám bệnh",
        "building": "A",
        "floor": 3,
        "room": "305",
        "pos": {"x": 45, "y": 30},
        "hours": "07:30 – 16:00 (T2–T6)",
        "description": "Khám và điều trị các bệnh về da, dị ứng, mụn, nấm, rụng tóc.",
        "keywords": ["da liễu", "da", "dị ứng", "mẩn ngứa", "mụn", "nấm da"],
        "symptoms": ["nổi mẩn ngứa", "phát ban", "mụn nhọt", "nám", "rụng tóc"],
        "directions": [
            "Vào cửa chính Nhà A, đi tới thang máy giữa sảnh",
            "Lên tầng 3",
            "Ra khỏi thang máy rẽ trái, đi qua phòng 301, phòng 305 bên phải",
        ],
    },
    {
        "id": "tai-mui-hong",
        "name": "Khoa Tai – Mũi – Họng",
        "category": "Khám bệnh",
        "building": "A",
        "floor": 3,
        "room": "308",
        "pos": {"x": 70, "y": 30},
        "hours": "07:00 – 16:30 (T2–T7)",
        "description": "Khám viêm họng, viêm xoang, ù tai, nội soi tai mũi họng.",
        "keywords": ["tai mũi họng", "tmh", "viêm họng", "viêm xoang", "ù tai", "nghẹt mũi"],
        "symptoms": ["đau họng", "nghẹt mũi", "ù tai", "ho kéo dài", "chảy nước mũi"],
        "directions": [
            "Vào cửa chính Nhà A, đi tới thang máy giữa sảnh",
            "Lên tầng 3",
            "Ra khỏi thang máy rẽ phải, phòng 308 ở cuối hành lang",
        ],
    },
    {
        "id": "mat",
        "name": "Khoa Mắt",
        "category": "Khám bệnh",
        "building": "A",
        "floor": 3,
        "room": "310",
        "pos": {"x": 85, "y": 30},
        "hours": "07:00 – 16:30 (T2–T7)",
        "description": "Khám thị lực, đo khúc xạ, điều trị các bệnh về mắt.",
        "keywords": ["mắt", "thị lực", "cận thị", "đau mắt", "khúc xạ", "mờ mắt"],
        "symptoms": ["mờ mắt", "đau mắt đỏ", "nhức mắt", "chảy nước mắt", "nhìn đôi"],
        "directions": [
            "Vào cửa chính Nhà A, đi tới thang máy giữa sảnh",
            "Lên tầng 3",
            "Ra khỏi thang máy rẽ phải, phòng 310 cạnh khoa Tai Mũi Họng",
        ],
    },
    {
        "id": "san-phu-khoa",
        "name": "Khoa Sản – Phụ khoa",
        "category": "Khám bệnh",
        "building": "A",
        "floor": 4,
        "room": "401",
        "pos": {"x": 25, "y": 30},
        "hours": "07:00 – 16:30 (T2–T7)",
        "description": "Khám thai, khám phụ khoa, siêu âm sản và tư vấn sức khoẻ sinh sản.",
        "keywords": ["sản", "phụ khoa", "khám thai", "thai sản", "siêu âm thai"],
        "symptoms": ["khám thai", "rối loạn kinh nguyệt", "đau bụng dưới", "khí hư bất thường"],
        "directions": [
            "Vào cửa chính Nhà A, đi tới thang máy giữa sảnh",
            "Lên tầng 4",
            "Ra khỏi thang máy rẽ trái, phòng 401 ngay đầu hành lang",
        ],
    },
    {
        "id": "nhi",
        "name": "Khoa Nhi",
        "category": "Khám bệnh",
        "building": "A",
        "floor": 4,
        "room": "405",
        "pos": {"x": 55, "y": 30},
        "hours": "07:00 – 16:30 (T2–CN)",
        "description": "Khám và điều trị bệnh cho trẻ em: sốt, ho, tiêu chảy, dinh dưỡng.",
        "keywords": ["nhi", "trẻ em", "em bé", "sốt trẻ", "tiêm chủng"],
        "symptoms": ["trẻ sốt", "trẻ ho", "trẻ tiêu chảy", "trẻ biếng ăn", "trẻ phát ban"],
        "directions": [
            "Vào cửa chính Nhà A, đi tới thang máy giữa sảnh",
            "Lên tầng 4",
            "Ra khỏi thang máy rẽ phải, phòng 405 có khu chờ riêng cho trẻ",
        ],
    },
    {
        "id": "rang-ham-mat",
        "name": "Khoa Răng – Hàm – Mặt",
        "category": "Khám bệnh",
        "building": "A",
        "floor": 4,
        "room": "408",
        "pos": {"x": 80, "y": 30},
        "hours": "07:30 – 16:00 (T2–T7)",
        "description": "Khám và điều trị răng, nhổ răng, niềng răng, bệnh lý hàm mặt.",
        "keywords": ["răng hàm mặt", "rhm", "răng", "sâu răng", "nhổ răng", "đau răng"],
        "symptoms": ["đau răng", "sâu răng", "chảy máu chân răng", "sưng nướu"],
        "directions": [
            "Vào cửa chính Nhà A, đi tới thang máy giữa sảnh",
            "Lên tầng 4",
            "Ra khỏi thang máy rẽ phải, phòng 408 ở cuối hành lang",
        ],
    },
    {
        "id": "x-quang",
        "name": "Phòng X-quang",
        "category": "Chẩn đoán hình ảnh",
        "building": "B",
        "floor": 1,
        "room": "B102",
        "pos": {"x": 25, "y": 35},
        "hours": "07:00 – 17:00 (T2–T7)",
        "description": "Chụp X-quang xương khớp, lồng ngực theo chỉ định của bác sĩ.",
        "keywords": ["x quang", "x-quang", "chụp phim", "chẩn đoán hình ảnh", "xray"],
        "symptoms": [],
        "directions": [
            "Từ Nhà A đi qua hành lang nối sang Nhà B",
            "Phòng X-quang B102 nằm bên trái ngay tầng 1 Nhà B",
        ],
    },
    {
        "id": "sieu-am",
        "name": "Phòng Siêu âm",
        "category": "Chẩn đoán hình ảnh",
        "building": "B",
        "floor": 1,
        "room": "B105",
        "pos": {"x": 50, "y": 35},
        "hours": "07:00 – 17:00 (T2–T7)",
        "description": "Siêu âm ổ bụng, tuyến giáp, mạch máu, sản khoa theo chỉ định.",
        "keywords": ["siêu âm", "echo", "chẩn đoán hình ảnh", "ổ bụng"],
        "symptoms": [],
        "directions": [
            "Từ Nhà A đi qua hành lang nối sang Nhà B",
            "Phòng Siêu âm B105 nằm giữa hành lang tầng 1 Nhà B",
        ],
    },
    {
        "id": "ct-mri",
        "name": "Phòng CT – MRI",
        "category": "Chẩn đoán hình ảnh",
        "building": "B",
        "floor": 1,
        "room": "B108",
        "pos": {"x": 75, "y": 35},
        "hours": "07:00 – 17:00 (T2–T7)",
        "description": "Chụp cắt lớp vi tính (CT) và cộng hưởng từ (MRI) theo chỉ định chuyên khoa.",
        "keywords": ["ct", "mri", "cắt lớp", "cộng hưởng từ", "chẩn đoán hình ảnh"],
        "symptoms": [],
        "directions": [
            "Từ Nhà A đi qua hành lang nối sang Nhà B",
            "Đi hết hành lang tầng 1 Nhà B, phòng CT-MRI B108 ở cuối",
        ],
    },
    {
        "id": "xet-nghiem",
        "name": "Phòng Xét nghiệm",
        "category": "Xét nghiệm",
        "building": "B",
        "floor": 2,
        "room": "B201",
        "pos": {"x": 30, "y": 35},
        "hours": "06:30 – 16:00 (T2–T7)",
        "description": "Lấy mẫu máu, nước tiểu và thực hiện các xét nghiệm cận lâm sàng.",
        "keywords": ["xét nghiệm", "lấy máu", "máu", "nước tiểu", "cận lâm sàng", "lab"],
        "symptoms": [],
        "directions": [
            "Từ Nhà A đi qua hành lang nối sang Nhà B, lên thang máy tầng 2",
            "Phòng Xét nghiệm B201 nằm ngay bên phải khi ra thang máy",
        ],
    },
    {
        "id": "nha-thuoc",
        "name": "Nhà thuốc bệnh viện",
        "category": "Dịch vụ",
        "building": "A",
        "floor": 1,
        "room": "120",
        "pos": {"x": 50, "y": 20},
        "hours": "07:00 – 18:00 (T2–CN)",
        "description": "Cấp phát và bán thuốc theo đơn của bác sĩ trong bệnh viện.",
        "keywords": ["nhà thuốc", "thuốc", "mua thuốc", "đơn thuốc", "pharmacy"],
        "symptoms": [],
        "directions": [
            "Vào cửa chính Nhà A",
            "Nhà thuốc nằm giữa sảnh tầng 1, đối diện thang máy",
        ],
    },
    {
        "id": "thu-ngan",
        "name": "Quầy Thu ngân & BHYT",
        "category": "Hành chính",
        "building": "A",
        "floor": 1,
        "room": "103",
        "pos": {"x": 30, "y": 20},
        "hours": "06:30 – 17:00 (T2–T7)",
        "description": "Thanh toán viện phí, làm thủ tục bảo hiểm y tế (BHYT).",
        "keywords": ["thu ngân", "viện phí", "thanh toán", "bảo hiểm", "bhyt", "đóng tiền"],
        "symptoms": [],
        "directions": [
            "Vào cửa chính Nhà A",
            "Quầy Thu ngân nằm bên trái sảnh, cạnh quầy Tiếp đón",
        ],
    },
    {
        "id": "noi-tiet",
        "name": "Khoa Nội tiết – Đái tháo đường",
        "category": "Khám bệnh",
        "building": "A",
        "floor": 2,
        "room": "210",
        "pos": {"x": 85, "y": 30},
        "hours": "07:00 – 16:30 (T2–T7)",
        "description": "Khám và quản lý tiểu đường, tuyến giáp, rối loạn nội tiết.",
        "keywords": ["nội tiết", "tiểu đường", "đái tháo đường", "tuyến giáp", "đường huyết"],
        "symptoms": ["khát nước nhiều", "tiểu nhiều", "sút cân nhanh", "mệt mỏi", "bướu cổ"],
        "directions": [
            "Vào cửa chính Nhà A, đi tới thang máy giữa sảnh",
            "Lên tầng 2",
            "Ra khỏi thang máy rẽ phải, phòng 210 cạnh khoa Nội thần kinh",
        ],
    },
    {
        "id": "phuc-hoi-chuc-nang",
        "name": "Khoa Phục hồi chức năng",
        "category": "Điều trị",
        "building": "B",
        "floor": 2,
        "room": "B205",
        "pos": {"x": 60, "y": 35},
        "hours": "07:00 – 16:30 (T2–T7)",
        "description": "Vật lý trị liệu, phục hồi vận động sau chấn thương, tai biến.",
        "keywords": ["phục hồi chức năng", "vật lý trị liệu", "tập vận động", "phcn", "trị liệu"],
        "symptoms": ["yếu liệt sau tai biến", "cứng khớp sau bó bột", "đau sau chấn thương"],
        "directions": [
            "Từ Nhà A đi qua hành lang nối sang Nhà B, lên thang máy tầng 2",
            "Ra thang máy rẽ trái, phòng B205 ở giữa hành lang",
        ],
    },
]

# Sảnh / điểm mốc dùng cho hướng dẫn đường đi và (sau này) đồ thị tìm đường.
# Chưa dùng nhiều ở GĐ1 nhưng khai báo sẵn để các phòng tham chiếu vị trí thang máy.
LANDMARKS = {
    "cua-chinh": {"name": "Cửa chính Nhà A", "floor": 1, "building": "A", "pos": {"x": 50, "y": 90}},
    "thang-may-A": {"name": "Thang máy Nhà A", "floor": 1, "building": "A", "pos": {"x": 50, "y": 55}},
    "hanh-lang-noi": {"name": "Hành lang nối A–B", "floor": 1, "building": "A", "pos": {"x": 50, "y": 70}},
}


# ---------------------------------------------------------------------------
# Tiện ích
# ---------------------------------------------------------------------------
def strip_accents(text: str) -> str:
    """Bỏ dấu tiếng Việt + về chữ thường để tìm kiếm 'gần đúng'.

    Ví dụ: "Tim mạch" -> "tim mach". Nhờ vậy gõ không dấu vẫn tìm được.
    """
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text.replace("đ", "d")


def _haystack(dep: dict) -> str:
    """Gộp các trường có thể tìm kiếm của một khoa thành 1 chuỗi không dấu."""
    parts = [dep["name"], dep["category"], dep["room"], *dep["keywords"], *dep.get("symptoms", [])]
    return strip_accents(" ".join(parts))


def _compact(text: str) -> str:
    """Bỏ mọi ký tự không phải chữ/số: 'x-quang' -> 'xquang', giúp khớp khi
    người dùng gõ liền không khoảng trắng hay dấu gạch nối."""
    return "".join(ch for ch in strip_accents(text) if ch.isalnum())


def get_all() -> list[dict]:
    return DEPARTMENTS


def get_by_id(dep_id: str) -> dict | None:
    return next((d for d in DEPARTMENTS if d["id"] == dep_id), None)


def search(query: str, limit: int = 10) -> list[dict]:
    """Tìm kiếm khoa/phòng theo từ khoá (có hỗ trợ gõ không dấu).

    Cho điểm đơn giản: khớp ở tên > khớp ở từ khoá/triệu chứng. Trả về danh sách
    đã sắp xếp theo độ liên quan. Đây là tìm kiếm 'cứng' ở GĐ1; phần hiểu ngôn ngữ
    tự nhiên sẽ do chatbot RAG đảm nhiệm ở GĐ2.
    """
    q = strip_accents(query).strip()
    if not q:
        return []

    q_compact = _compact(q)
    scored: list[tuple[int, dict]] = []
    for dep in DEPARTMENTS:
        name = strip_accents(dep["name"])
        haystack = _haystack(dep)
        score = 0
        if q in name:
            score += 10
        if name.startswith(q):
            score += 5
        if q in haystack:
            score += 3
        # khớp khi gõ liền không dấu/khoảng trắng (vd "xquang" ~ "x-quang")
        elif q_compact and q_compact in _compact(haystack):
            score += 2
        # khớp theo từng từ trong query
        for word in q.split():
            if word and word in haystack:
                score += 1
        if score > 0:
            scored.append((score, dep))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [dep for _, dep in scored[:limit]]
