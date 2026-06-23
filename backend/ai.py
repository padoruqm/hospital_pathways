"""
Ý tưởng: nhồi toàn bộ danh sách khoa/phòng vào **System Instruction** rồi để model tự
tư vấn dựa trên đó. 
Endpoint: POST /api/ai/chat   body { "message": str, "history": [{role, text}]? }
          -> { "status": "success", "reply": str }
"""

import os

from flask import Blueprint, jsonify, request
from dotenv import load_dotenv

import repository as repo

load_dotenv()

ai_bp = Blueprint("ai", __name__)

# Cho phép đổi model qua biến môi trường GEMINI_MODEL mà không phải sửa code.
MODEL = os.environ.get(
                        "GEMINI_MODEL",
                        "gemini-3.1-flash-lite"
                        )

def _friendly_error(raw: str) -> str:
    if "PERMISSION_DENIED" in raw or "403" in raw:
        return (
            f"Khoá Gemini không có quyền dùng model '{MODEL}'. Hãy thử đặt "
            "GEMINI_MODEL=gemini-3.1-flash-lite trong backend/.env, hoặc tạo API key mới "
            "(chuẩn bắt đầu bằng 'AIza') tại Google AI Studio."
        )
    if "RESOURCE_EXHAUSTED" in raw or "429" in raw:
        return (
            "Đã hết hạn mức (quota) miễn phí của khoá Gemini. Vui lòng đợi quota reset."
        )
    return raw

def _departments_context() -> str:
    """Sinh danh sách khoa/phòng dạng text từ dữ liệu thật (luôn đồng bộ với repository)."""
    lines = []
    for d in repo.get_all():
        symptoms = ", ".join(d.get("symptoms", [])) or "—"
        lines.append(
            f"- {d['name']} | nhóm: {d['category']} | {repo.building_name(d['building'])}"
            f" | tầng {d['floor']}, phòng {d['room']} | giờ: {d['hours']}"
            f" | khám/triệu chứng: {symptoms}"
        )
    return "\n".join(lines)

def _system_instruction() -> str:
    return (
        "Bạn là trợ lý điều hướng của bệnh viện, nói tiếng Việt thân thiện, ngắn gọn.\n"
        "Nhiệm vụ: nghe triệu chứng hoặc câu hỏi của bệnh nhân rồi tư vấn nên đến khoa/phòng nào.\n\n"
        "CHỈ được chỉ định bệnh nhân đến các khoa/phòng trong danh sách dưới đây:\n"
        f"{_departments_context()}\n\n"
        "Quy tắc trả lời:\n"
        "- Phân tích ngắn gọn triệu chứng, rồi nêu rõ tên khoa kèm TẦNG, SỐ PHÒNG và GIỜ LÀM VIỆC.\n"
        "- Nếu là trường hợp nguy hiểm/khẩn cấp, hướng dẫn tới Khoa Cấp cứu ngay.\n"
        "- Nếu không chắc chắn, khuyên bệnh nhân tới Quầy Tiếp đón để được hướng dẫn.\n"
        "- Không chẩn đoán bệnh chắc chắn, không kê đơn thuốc; chỉ gợi ý nơi khám phù hợp.\n"
        "- Trả lời gọn trong vài câu, dễ đọc trên điện thoại."
    )

# Tạo client một lần, chỉ khi có API key. Nhờ vậy server vẫn chạy bình thường khi chưa
_client = None

def _get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return None
        from google import genai

        _client = genai.Client(api_key=api_key)
    return _client


@ai_bp.route("/chat", methods=["POST"])
def chat_with_gemini():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Thiếu tin nhắn người dùng!"}), 400

    client = _get_client()
    if client is None:
        return jsonify({
            "status": "error",
            "message": "Server chưa cấu hình GEMINI_API_KEY. Thêm khoá vào backend/.env rồi khởi động lại.",
        }), 503

    from google.genai import types

    # Ghép lịch sử hội thoại vào câu promt
    contents = []
    for turn in data.get("history", []):
        role = "model" if turn.get("role") == "assistant" else "user"
        text = (turn.get("text") or "").strip()
        if text:
            contents.append(types.Content(role=role, parts=[types.Part(text=text)]))
    contents.append(types.Content(role="user", parts=[types.Part(text=message)]))

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=_system_instruction(),
                temperature=0.3,
            ),
        )
        return jsonify({"status": "success", "reply": response.text})
    except Exception as e:
        return jsonify({"status": "error", "message": _friendly_error(str(e))}), 502
