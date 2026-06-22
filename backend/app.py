"""Flask API cho Hospital Wayfinding System — tầng web (HTTP).

File này CHỈ lo việc nhận request, gọi ``repository`` để xử lý dữ liệu, rồi trả JSON.
Không chứa logic dữ liệu/tìm kiếm (nằm ở ``repository.py``).

    Đọc:
    GET    /api/health              -> kiểm tra service sống
    GET    /api/departments         -> danh sách rút gọn tất cả khoa/phòng
    GET    /api/departments/<id>    -> chi tiết một khoa (kèm hướng dẫn đường đi)
    GET    /api/search?q=...        -> tìm kiếm khoa/phòng theo từ khoá
    GET    /api/floors              -> các tầng + phòng trên tầng (phục vụ sơ đồ)

    Quản trị (ghi):
    POST   /api/departments         -> thêm khoa
    PUT    /api/departments/<id>    -> sửa khoa
    DELETE /api/departments/<id>    -> xoá khoa
    GET    /api/stats               -> thống kê lượt tra cứu theo khoa
    AI (chatbot Gemini, xem ai.py):
    POST   /api/ai/chat             -> tư vấn khoa khám (System Instruction)
    POST   /api/ai/rag/chat         -> tư vấn khoa khám (RAG, xem ai_rag.py)
    GET    /api/ai/rag/status       -> tình trạng index RAG
    OCR CCCD (Hướng B, xem ocr.py):
    POST   /api/ocr/scan            -> quét ảnh CCCD trích xuất thông tin
    POST   /api/ocr/register        -> đăng ký khám: gợi ý khoa + số thứ tự ảo

"""

from __future__ import annotations
from flask import Flask, jsonify, request
from flask_cors import CORS

import repository as repo
from ai import ai_bp
from ai_rag import ai_rag_bp
from ocr import ocr_bp

def _summary(dep: dict) -> dict:
    """Bản rút gọn của một khoa để hiển thị trong danh sách / kết quả tìm kiếm."""
    return {
        "id": dep["id"],
        "name": dep["name"],
        "category": dep["category"],
        "building": dep["building"],
        "buildingName": repo.building_name(dep["building"]),
        "floor": dep["floor"],
        "room": dep["room"],
        "hours": dep["hours"],
        "description": dep["description"],
    }

def _detail(dep: dict) -> dict:
    """Bản đầy đủ kèm hướng dẫn đường đi và toạ độ trên sơ đồ tầng."""
    return {
        **_summary(dep),
        "keywords": dep["keywords"],
        "symptoms": dep.get("symptoms", []),
        "pos": dep["pos"],
        "directions": dep["directions"],
    }

def create_app() -> Flask:
    app = Flask(__name__)
    # Cho phép frontend (Vite dev server) gọi API trong môi trường dev.
    CORS(app)

    # Đăng ký blueprint
    # Nhóm route AI (chatbot Gemini) dưới tiền tố /api/ai -> POST /api/ai/chat
    app.register_blueprint(ai_bp, url_prefix="/api/ai")
    # Chatbot RAG (tra tài liệu) -> POST /api/ai/rag/chat, GET /api/ai/rag/status
    app.register_blueprint(ai_rag_bp, url_prefix="/api/ai/rag")
    # OCR quét CCCD (Hướng B) -> POST /api/ocr/scan, POST /api/ocr/register
    app.register_blueprint(ocr_bp, url_prefix="/api/ocr")

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "departments": len(repo.get_all())})

    @app.get("/api/departments")
    def list_departments():
        return jsonify([_summary(d) for d in repo.get_all()])
  
    @app.get("/api/departments/<dep_id>")
    def get_department(dep_id: str):
        dep = repo.get_by_id(dep_id)
        if dep is None:
            return jsonify({"error": "not_found", "message": "Không tìm thấy khoa/phòng"}), 404
        repo.record_view(dep_id)  # đếm lượt xem cho thống kê admin
        return jsonify(_detail(dep))

    # ---- Endpoint quản trị (CRUD) ----
    @app.post("/api/departments")
    def create_department():
        payload = request.get_json(silent=True) or {}
        errors = repo.validate(payload)
        if errors:
            return jsonify({"error": "validation", "messages": errors}), 400
        dep = repo.create_department(payload)
        return jsonify(_detail(dep)), 201

    @app.put("/api/departments/<dep_id>")
    def update_department(dep_id: str):
        payload = request.get_json(silent=True) or {}
        errors = repo.validate(payload)
        if errors:
            return jsonify({"error": "validation", "messages": errors}), 400
        dep = repo.update_department(dep_id, payload)
        if dep is None:
            return jsonify({"error": "not_found", "message": "Không tìm thấy khoa/phòng"}), 404
        return jsonify(_detail(dep))

    @app.delete("/api/departments/<dep_id>")
    def delete_department(dep_id: str):
        ok = repo.delete_department(dep_id)
        if not ok:
            return jsonify({"error": "not_found", "message": "Không tìm thấy khoa/phòng"}), 404
        return jsonify({"deleted": dep_id})

    @app.get("/api/stats")
    def stats():
        return jsonify(repo.get_stats())

    @app.get("/api/search")
    def search():
        query = request.args.get("q", "", type=str)
        if not query.strip():
            return jsonify({"query": query, "count": 0, "results": []})
        results = repo.search(query)
        return jsonify({
            "query": query,
            "count": len(results),
            "results": [_summary(d) for d in results],
        })

    @app.get("/api/floors")
    def floors():
        """Gom phòng theo (toà nhà, tầng) để frontend vẽ sơ đồ từng tầng."""
        grouped: dict[str, dict] = {}
        for dep in repo.get_all():
            key = f"{dep['building']}-{dep['floor']}"
            if key not in grouped:
                grouped[key] = {
                    "building": dep["building"],
                    "buildingName": repo.building_name(dep["building"]),
                    "floor": dep["floor"],
                    "rooms": [],
                }
            grouped[key]["rooms"].append({
                "id": dep["id"],
                "name": dep["name"],
                "room": dep["room"],
                "pos": dep["pos"],
            })
        floors = sorted(grouped.values(), key=lambda f: (f["building"], f["floor"]))
        return jsonify(floors)

    return app


app = create_app()

if __name__ == "__main__":
    import os

    # Cổng đọc từ biến môi trường PORT (mặc định 5057 để tránh đụng AirPlay
    # Receiver chiếm cổng 5000 trên macOS). Production sẽ dùng gunicorn/uwsgi.
    port = int(os.environ.get("PORT", "5057"))
    app.run(host="0.0.0.0", port=port, debug=True)
