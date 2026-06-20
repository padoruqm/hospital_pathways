"""Tiện ích xử lý chuỗi tiếng Việt — dùng chung cho việc tìm kiếm.

Tách riêng vì đây là hàm thuần (không phụ thuộc dữ liệu), dễ tái sử dụng và dễ test.
"""

import unicodedata


def strip_accents(text: str) -> str:
    """Bỏ dấu tiếng Việt + chuyển chữ thường.

    Ví dụ: "Tim mạch" -> "tim mach". Nhờ vậy gõ không dấu vẫn tìm được.
    """
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text.replace("đ", "d")


def normalize(text: str) -> str:
    """Chuẩn hoá để so khớp tìm kiếm: bỏ dấu, rồi CHỈ giữ lại chữ và số.

    Bỏ luôn khoảng trắng, dấu gạch nối… nên "X-quang", "x quang", "xquang" đều quy
    về cùng một chuỗi "xquang". Đây là phép chuẩn hoá duy nhất mà tìm kiếm dựa vào.
    """
    return "".join(ch for ch in strip_accents(text) if ch.isalnum())
