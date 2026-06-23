import unicodedata


def strip_accents(text: str) -> str:
    """Bỏ dấu tiếng Việt + chuyển chữ thường.

    Ví dụ: "Tim mạch" -> "tim mach".
    """
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text.replace("đ", "d")


def normalize(text: str) -> str:
    """Chuẩn hoá để so khớp tìm kiếm: bỏ dấu, chỉ giữ lại chữ và số.

    Bỏ luôn khoảng trắng, dấu gạch nối… nên "X-quang", "x quang", "xquang" đều quy
    về cùng một chuỗi "xquang". Đây là phép chuẩn hoá duy nhất mà tìm kiếm dựa vào.
    """
    return "".join(ch for ch in strip_accents(text) if ch.isalnum())
