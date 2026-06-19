"""Flask API cho Hospital Wayfinding System.

Giai đoạn 1 chỉ cần một API đọc dữ liệu (read-only) để frontend tra cứu:

    GET /api/health                 -> kiểm tra service sống
    GET /api/departments            -> danh sách rút gọn tất cả khoa/phòng
    GET /api/departments/<id>       -> chi tiết một khoa (kèm hướng dẫn đường đi)
    GET /api/search?q=...           -> tìm kiếm khoa/phòng theo từ khoá
    GET /api/floors                 -> các tầng + phòng trên tầng (phục vụ sơ đồ)

Các endpoint ghi (thêm/sửa/xoá) sẽ được bổ sung ở giai đoạn Admin dashboard.
"""

from __future__ import annotations

from flask import Flask, jsonify, request
from flask_cors import CORS

import hospital_data as data


def _summary(dep: dict) -> dict:
    """Bản rút gọn của một khoa để hiển thị trong danh sách / kết quả tìm kiếm."""
    return {
        "id": dep["id"],
        "name": dep["name"],
        "category": dep["category"],
        "building": dep["building"],
        "buildingName": data.BUILDINGS.get(dep["building"], dep["building"]),
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

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "departments": len(data.get_all())})

    @app.get("/api/departments")
    def list_departments():
        return jsonify([_summary(d) for d in data.get_all()])

    @app.get("/api/departments/<dep_id>")
    def get_department(dep_id: str):
        dep = data.get_by_id(dep_id)
        if dep is None:
            return jsonify({"error": "not_found", "message": "Không tìm thấy khoa/phòng"}), 404
        return jsonify(_detail(dep))

    @app.get("/api/search")
    def search():
        query = request.args.get("q", "", type=str)
        if not query.strip():
            return jsonify({"query": query, "count": 0, "results": []})
        results = data.search(query)
        return jsonify({
            "query": query,
            "count": len(results),
            "results": [_summary(d) for d in results],
        })

    @app.get("/api/floors")
    def floors():
        """Gom phòng theo (toà nhà, tầng) để frontend vẽ sơ đồ từng tầng."""
        grouped: dict[str, dict] = {}
        for dep in data.get_all():
            key = f"{dep['building']}-{dep['floor']}"
            if key not in grouped:
                grouped[key] = {
                    "building": dep["building"],
                    "buildingName": data.BUILDINGS.get(dep["building"], dep["building"]),
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
