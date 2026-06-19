# 02 — Backend Flask & dữ liệu bệnh viện

Bước này dựng **lớp dữ liệu + API** trước, để frontend ở các bước sau chỉ việc gọi.

## Vì sao làm backend trước?

Toàn bộ web xoay quanh dữ liệu khoa/phòng. Khi dữ liệu và API đã ổn định, việc dựng
giao diện trở nên đơn giản và không phải sửa đi sửa lại. Backend cũng là nơi sau này
gắn AI (RAG đọc cùng nguồn dữ liệu) nên định hình sớm sẽ tiết kiệm công.

## Hai file chính

| File | Vai trò |
|------|---------|
| [`backend/hospital_data.py`](../backend/hospital_data.py) | "Nguồn sự thật": 20 khoa/phòng mock + hàm tìm kiếm |
| [`backend/app.py`](../backend/app.py) | Flask app, khai báo các route API |

## Mô hình dữ liệu một khoa/phòng

```python
{
  "id": "tim-mach",            # slug định danh, dùng trên URL
  "name": "Khoa Tim mạch",
  "category": "Khám bệnh",     # nhóm: Khám bệnh / Chẩn đoán hình ảnh / Xét nghiệm / ...
  "building": "A",             # toà nhà (A / B)
  "floor": 2,                  # tầng
  "room": "205",               # số phòng
  "pos": {"x": 45, "y": 30},   # toạ độ trên sơ đồ tầng (hệ 0..100) -> dùng vẽ SVG
  "hours": "07:00 – 16:30 (T2–T7)",
  "description": "...",
  "keywords": ["tim", "huyết áp", "đau ngực", ...],   # phục vụ tìm kiếm + RAG
  "symptoms": ["đau ngực", "hồi hộp", ...],            # phục vụ RAG (GĐ2)
  "directions": ["Vào cửa chính Nhà A", "Lên tầng 2", ...]  # đường đi từng bước
}
```

> Mỗi trường được thiết kế để **dùng lại** ở các giai đoạn sau: `keywords/symptoms` cho
> chatbot RAG, `pos/floor` cho sơ đồ SVG và đồ thị tìm đường (điểm cộng).

Dữ liệu hiện có **20 khoa/phòng** trải trên 2 toà nhà (A, B) và 4 tầng — đủ nhiều để test
tìm kiếm và sơ đồ có ý nghĩa.

## Tìm kiếm có dấu / không dấu

Hàm `strip_accents()` bỏ dấu tiếng Việt và đưa về chữ thường, nên gõ `"tim mach"`,
`"Tim mạch"` hay `"TIM"` đều ra Khoa Tim mạch. Hàm `search()` cho điểm đơn giản:
khớp ở **tên** (điểm cao) > khớp ở **từ khoá/triệu chứng**, rồi sắp xếp theo độ liên quan.

Đây là tìm kiếm "cứng". Việc hiểu câu tự nhiên kiểu *"tôi bị đau ngực"* sẽ do **chatbot
RAG** đảm nhiệm ở Giai đoạn 2 — nhưng nhờ đã có sẵn `symptoms`, ngay cả tìm kiếm cứng
cũng bắt được vài triệu chứng phổ biến.

## Các endpoint API

| Method & path | Trả về |
|---------------|--------|
| `GET /api/health` | Trạng thái service + số khoa |
| `GET /api/departments` | Danh sách rút gọn tất cả khoa/phòng |
| `GET /api/departments/<id>` | Chi tiết một khoa (kèm `directions`, `pos`) |
| `GET /api/search?q=...` | Kết quả tìm kiếm theo từ khoá |
| `GET /api/floors` | Phòng gom theo (toà nhà, tầng) — để vẽ sơ đồ |

CORS được bật để Vite dev server (cổng khác) gọi được API trong môi trường dev.

## Chạy thử backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py                      # chạy ở http://localhost:5001 (đổi cổng bằng biến PORT)
```

Kiểm tra nhanh:

```bash
curl http://localhost:5001/api/health
curl "http://localhost:5001/api/search?q=tim%20mach"
curl http://localhost:5001/api/departments/tim-mach
```
