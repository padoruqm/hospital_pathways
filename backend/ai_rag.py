"""Chatbot RAG (Retrieval-Augmented Generation) tư vấn khoa khám.

==========================================================================
RAG LÀ GÌ & VÌ SAO CẦN?
==========================================================================
Bản chatbot ở ``ai.py`` nhồi TOÀN BỘ 20 khoa vào System Instruction. Cách đó đơn giản
nhưng không mở rộng được: khi bệnh viện có hàng trăm khoa/quy định, prompt sẽ quá dài,
tốn token và model dễ "lạc". RAG giải quyết bằng cách: **chỉ lấy vài đoạn tài liệu liên
quan nhất tới câu hỏi rồi mới đưa cho LLM trả lời.**    

Luồng RAG trong file này gồm 5 bước (đọc theo thứ tự các phần đánh số bên dưới):

  (1) TÀI LIỆU      : đọc file kiến thức ``data_hospital.md`` (sinh từ hospital_data).
  (2) CHUNKING      : cắt tài liệu thành các "đoạn" (chunk) — ở đây mỗi khoa = 1 chunk.
  (3) EMBEDDING     : biến mỗi chunk thành 1 vector số (Gemini text-embedding-004).
  (4) VECTOR STORE  : lưu các vector trong bộ nhớ + tìm theo độ tương đồng cosine.
  (5) LLM           : ghép các chunk liên quan vào prompt rồi để Gemini soạn câu trả lời.

      Câu hỏi ─► embed query ─► so cosine với kho vector ─► lấy top-K chunk
                                                              │
                       prompt = (chunk liên quan) + câu hỏi ──┘─► Gemini ─► trả lời

Endpoint:  POST /api/ai/rag/chat   { "message": str, "history": [{role,text}]? }
              -> { status, reply, sources: [{id, name}] }  (id để liên kết sang trang chi tiết)
           GET  /api/ai/rag/status -> tình trạng index (đã build chưa, số chunk…)
"""

from __future__ import annotations

import math
import os
from pathlib import Path

from flask import Blueprint, jsonify, request
from dotenv import load_dotenv

import repository as repo

load_dotenv()

ai_rag_bp = Blueprint("ai_rag", __name__)

# Model có thể đổi qua biến môi trường, không cần sửa code.
CHAT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite")
EMBED_MODEL = os.environ.get("GEMINI_EMBED_MODEL", "gemini-embedding-001")
TOP_K = int(os.environ.get("RAG_TOP_K", "4"))  # số chunk lấy ra cho mỗi câu hỏi

# File tài liệu kiến thức của RAG. Sinh từ hospital_data nếu chưa có (xem build_document).
DOC_PATH = Path(__file__).with_name("data_hospital.md")


def _friendly_error(raw: str) -> str:
    if "PERMISSION_DENIED" in raw or "403" in raw:
        return (
            f"Khoá Gemini không có quyền dùng model '{CHAT_MODEL}'/'{EMBED_MODEL}'. "
            "Thử đổi GEMINI_MODEL trong backend/.env hoặc tạo API key mới tại Google AI Studio."
        )
    if "RESOURCE_EXHAUSTED" in raw or "429" in raw:
        return "Đã hết hạn mức (quota) miễn phí của khoá Gemini. Đợi reset, dùng khoá khác, hoặc bật billing."
    return raw


# (1) TÀI LIỆU — sinh file kiến thức từ dữ liệu gốc
def build_document() -> str:
    """Tạo nội dung tài liệu markdown đầy đủ từ toàn bộ dữ liệu khoa/phòng."""
    parts: list[str] = ["# Cẩm nang khoa/phòng bệnh viện\n"]

    # Một chunk giới thiệu các toà nhà.
    building_lines = ["## Thông tin chung về toà nhà"]
    for code, name in repo.BUILDINGS.items():
        building_lines.append(f"- Toà {code}: {name}")
    parts.append("\n".join(building_lines))

    # Mỗi khoa = một mục (sẽ trở thành 1 chunk khi chunking).
    for d in repo.get_all():
        keywords = ", ".join(d.get("keywords", [])) or "—"
        symptoms = ", ".join(d.get("symptoms", [])) or "—"
        directions = " → ".join(d.get("directions", [])) or "—"
        block = [
            f"## {d['name']}",
            f"- Mã (id): {d['id']}",
            f"- Nhóm: {d['category']}",
            f"- Toà nhà: {repo.building_name(d['building'])} (mã {d['building']})",
            f"- Tầng: {d['floor']}",
            f"- Phòng: {d['room']}",
            f"- Giờ làm việc: {d['hours']}",
            f"- Mô tả: {d['description']}",
            f"- Từ khoá: {keywords}",
            f"- Triệu chứng thường gặp: {symptoms}",
            f"- Hướng dẫn đường đi: {directions}",
        ]
        parts.append("\n".join(block))

    return "\n\n".join(parts) + "\n"

def ensure_document() -> str:
    """Đảm bảo file data_hospital.md tồn tại (tự sinh nếu thiếu) rồi trả nội dung."""
    if not DOC_PATH.exists():
        DOC_PATH.write_text(build_document(), encoding="utf-8")
    return DOC_PATH.read_text(encoding="utf-8")


# ==========================================================================
# (2) CHUNKING — cắt tài liệu thành các đoạn
# --------------------------------------------------------------------------
# Vì sao cắt theo từng khoa (mỗi mục "## ...")? Vì mỗi khoa là một đơn vị ngữ nghĩa
# trọn vẹn, độ dài vừa phải. Chunk quá to -> nhiễu, kém chính xác; quá nhỏ (vd từng
# dòng) -> mất ngữ cảnh. Cắt theo mục là điểm cân bằng tự nhiên cho dữ liệu này.
# ==========================================================================
def chunk_document(text: str) -> list[str]:
    """Tách markdown thành các chunk theo mỗi tiêu đề cấp 2 (dòng bắt đầu bằng '## ')."""
    chunks: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            if current:
                chunks.append("\n".join(current).strip())
            current = [line]
        elif current:  # bỏ phần tiêu đề "# " ở đầu file, chỉ gom từ "## " đầu tiên
            current.append(line)
    if current:
        chunks.append("\n".join(current).strip())
    return [c for c in chunks if c]


def _chunk_title(chunk: str) -> str:
    """Lấy tên mục (dòng '## ...') để hiển thị 'nguồn' đã truy hồi."""
    first = chunk.splitlines()[0]
    return first.replace("## ", "").strip()


def _chunk_id(chunk: str) -> str:
    """Lấy mã khoa (id) từ dòng '- Mã (id): ...' để frontend liên kết sang trang chi tiết.

    Đoạn 'Thông tin chung về toà nhà' không có id -> trả về "" (không liên kết được).
    """
    for line in chunk.splitlines():
        if line.startswith("- Mã (id):"):
            return line.split(":", 1)[1].strip()
    return ""

    
# ==========================================================================
# (3) EMBEDDING — biến văn bản thành vector số
# --------------------------------------------------------------------------
# Embedding ánh xạ một đoạn text -> vector ~768 chiều, sao cho các đoạn có nghĩa
# gần nhau thì vector gần nhau. Ta dùng model text-embedding-004 của Gemini.
# Dùng task_type khác nhau cho tài liệu (RETRIEVAL_DOCUMENT) và câu hỏi (RETRIEVAL_QUERY)
# để chất lượng truy hồi tốt hơn (đây là khuyến nghị của Google).
# ==========================================================================
_client = None

def _get_client():
    """Tạo Gemini client một lần. Thiếu API key -> trả None (server vẫn chạy)."""
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return None
        from google import genai

        _client = genai.Client(api_key=api_key)
    return _client


def _embed(texts: list[str], task_type: str) -> list[list[float]]:
    """Gọi Gemini để lấy vector embedding cho một danh sách văn bản."""
    from google.genai import types

    client = _get_client()
    resp = client.models.embed_content(
        model=EMBED_MODEL,
        contents=texts,
        config=types.EmbedContentConfig(task_type=task_type),
    )
    return [e.values for e in resp.embeddings]


# ==========================================================================
# (4) VECTOR STORE — kho vector trong bộ nhớ + tìm theo cosine
# --------------------------------------------------------------------------
# Với 20 chunk, một danh sách trong bộ nhớ là quá đủ; không cần CSDL vector nặng.
# (Khi dữ liệu lớn, có thể thay bằng FAISS / Chroma / pgvector — phần còn lại giữ nguyên.)
# Độ tương đồng dùng COSINE: đo góc giữa 2 vector, càng gần 1 càng giống nhau.
# ==========================================================================
# Mỗi phần tử: {"title": str, "text": str, "vector": list[float]}
_index: list[dict] | None = None


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def build_index() -> list[dict]:
    """Xây kho vector: đọc tài liệu -> chunk -> embed -> lưu. Chỉ chạy 1 lần rồi cache."""
    global _index
    chunks = chunk_document(ensure_document())
    vectors = _embed(chunks, "RETRIEVAL_DOCUMENT")
    _index = [
        {"id": _chunk_id(c), "title": _chunk_title(c), "text": c, "vector": v}
        for c, v in zip(chunks, vectors)
    ]
    return _index


def retrieve(query: str, k: int = TOP_K) -> list[dict]:
    """Truy hồi k chunk liên quan nhất tới câu hỏi (theo độ tương đồng cosine)."""
    if _index is None:
        build_index()
    assert _index is not None
    query_vec = _embed([query], "RETRIEVAL_QUERY")[0]
    scored = [
        {
            "id": item["id"],
            "title": item["title"],
            "text": item["text"],
            "score": _cosine(query_vec, item["vector"]),
        }
        for item in _index
    ]
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:k]


# ==========================================================================
# (5) LLM — sinh câu trả lời từ ngữ cảnh đã truy hồi
# --------------------------------------------------------------------------
# Chỉ đưa các chunk liên quan vào prompt và YÊU CẦU model chỉ dựa vào đó (grounding),
# hạn chế "bịa". Câu hỏi + lịch sử hội thoại đi trong `contents`.
# ==========================================================================
def _system_instruction(context_chunks: list[dict]) -> str:
    context = "\n\n".join(c["text"] for c in context_chunks)
    return (
        "Bạn là trợ lý điều hướng của bệnh viện, nói tiếng Việt thân thiện, ngắn gọn.\n"
        "CHỈ trả lời dựa trên phần NGỮ CẢNH dưới đây; tuyệt đối không bịa khoa/phòng "
        "không có trong ngữ cảnh. Nếu ngữ cảnh không đủ, hãy khuyên bệnh nhân tới Quầy "
        "Tiếp đón.\n\n"
        "=== NGỮ CẢNH (các khoa/phòng liên quan) ===\n"
        f"{context}\n"
        "=== HẾT NGỮ CẢNH ===\n\n"
        "Quy tắc: nêu rõ tên khoa kèm TẦNG, SỐ PHÒNG, GIỜ LÀM VIỆC; trường hợp khẩn cấp "
        "hướng tới Khoa Cấp cứu; không chẩn đoán chắc chắn, không kê đơn; trả lời gọn vài câu."
    )


@ai_rag_bp.route("/chat", methods=["POST"])
def chat_with_rag():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Thiếu tin nhắn người dùng!"}), 400

    if _get_client() is None:
        return jsonify({
            "status": "error",
            "message": "Server chưa cấu hình GEMINI_API_KEY. Thêm khoá vào backend/.env rồi khởi động lại.",
        }), 503

    from google.genai import types

    try:
        # (4) truy hồi ngữ cảnh liên quan
        top = retrieve(message)

        # (5) ghép lịch sử + câu hỏi rồi gọi LLM với ngữ cảnh đã truy hồi
        contents = []
        for turn in data.get("history", []):
            role = "model" if turn.get("role") == "assistant" else "user"
            text = (turn.get("text") or "").strip()
            if text:
                contents.append(types.Content(role=role, parts=[types.Part(text=text)]))
        contents.append(types.Content(role="user", parts=[types.Part(text=message)]))

        response = client_generate(contents, _system_instruction(top))
        return jsonify({
            "status": "success",
            "reply": response,
            # mỗi nguồn gồm id + tên để frontend liên kết sang trang chi tiết/đường đi
            "sources": [{"id": c["id"], "name": c["title"]} for c in top],
        })
    except Exception as e:
        return jsonify({"status": "error", "message": _friendly_error(str(e))}), 502


def client_generate(contents, system_instruction: str) -> str:
    """Gọi model sinh câu trả lời (tách riêng cho gọn)."""
    from google.genai import types

    client = _get_client()
    response = client.models.generate_content(
        model=CHAT_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.3,
        ),
    )
    return response.text


@ai_rag_bp.route("/status", methods=["GET"])
def status():
    """Xem nhanh tình trạng RAG (không gọi API nếu chưa build)."""
    return jsonify({
        "doc_exists": DOC_PATH.exists(),
        "doc_path": DOC_PATH.name,
        "indexed": _index is not None,
        "num_chunks": len(_index) if _index is not None else None,
        "chat_model": CHAT_MODEL,
        "embed_model": EMBED_MODEL,
        "top_k": TOP_K,
    })
