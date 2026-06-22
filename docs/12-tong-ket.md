# 12 — Tổng kết dự án

Tài liệu tổng kết: dự án làm được gì, kiến trúc & pipeline, các phần chưa ổn cần lưu ý,
và hướng cải thiện. Đây là tài liệu "đọc cuối" để nắm toàn cảnh.

## 1. Tổng quan

**Hospital Wayfinding System** — web giúp bệnh nhân tự tra cứu khoa/phòng, xem sơ đồ tầng,
nhận hướng dẫn đường đi, và đăng ký khám nhanh. Tech: **Vue 3 + TS** (frontend),
**Flask** (backend), **Google Gemini** + **PaddleOCR** (AI).

Dự án làm **cả hai hướng AI** của đề + một phần điểm cộng:

| Hạng mục (theo đề) | Trạng thái |
|--------------------|-----------|
| Phần 1 — Web nền tảng (tìm kiếm, kết quả, sơ đồ tầng, chỉ đường, mobile) | ✅ Xong |
| Phần 2 — Hướng A: Chatbot hỏi đáp (Gemini) — *System Instruction* **và** *RAG* | ✅ Xong |
| Phần 2 — Hướng B: OCR quét CCCD đăng ký khám (PaddleOCR) | ✅ Xong |
| Điểm cộng — Admin dashboard (CRUD + thống kê) | ✅ Xong |
| Điểm cộng — Kết hợp 2 hướng AI trong cùng web | ✅ Xong (chatbot + OCR liên thông trang chi tiết) |
| Điểm cộng — Tối ưu đường đi (đồ thị Dijkstra/A\*) | ❌ Không làm |

## 2. Các tính năng & nơi xem tài liệu

| Tính năng | Trang | Tài liệu |
|-----------|-------|----------|
| Tìm kiếm khoa/phòng | `/` | [02](02-backend-va-du-lieu.md), [03](03-frontend-va-tim-kiem.md) |
| Chi tiết khoa + sơ đồ tầng + chỉ đường | `/department/:id` | [04](04-trang-chi-tiet-va-duong-di.md), [05](05-so-do-tang-va-responsive.md) |
| Quản trị CRUD + thống kê | `/admin` | [07](07-admin-va-cai-thien-search.md) |
| Chatbot (System Instruction) | `/chat` (nút "Hỏi nhanh") | [09](09-ai-chatbot-gemini.md) |
| Chatbot RAG (truy hồi tài liệu + nguồn) | `/chat` (nút "RAG") | [10](10-rag-chatbot.md) |
| OCR CCCD + đăng ký khám | `/register` | [11](11-ocr-cccd.md) |
| OCR debug (xem từng bước) | `/ocr-debug` | [11](11-ocr-cccd.md) |

## 3. Kiến trúc & pipeline

### 3.1 Tổng thể
```
Vue 3 SPA  ──/api/*──►  Flask (app.py)
                          ├── repository.py   (dữ liệu khoa: đọc/tìm/CRUD/thống kê)
                          ├── ai.py           (chatbot System Instruction — Gemini)
                          ├── ai_rag.py       (chatbot RAG — embedding + vector store + Gemini)
                          └── ocr.py          (OCR CCCD — PaddleOCR + đăng ký)
       dữ liệu nguồn: hospital_data.py (20 khoa)  ·  text_utils.py (chuẩn hoá chuỗi)
```
Chi tiết quan hệ file backend: [08 — Cấu trúc backend](08-cau-truc-backend.md).

### 3.2 Pipeline RAG (Hướng A nâng cao)
```
data_hospital.md ─► chunk (mỗi khoa 1 đoạn) ─► embedding (gemini-embedding-001)
                                                       ─► vector store (cosine, in-memory)
Câu hỏi ─► embedding ─► tìm top-K cosine ─► ghép ngữ cảnh + câu hỏi ─► Gemini ─► trả lời + nguồn
```

### 3.3 Pipeline OCR (Hướng B)
```
Ảnh CCCD ─► (1) tiền xử lý (xoay EXIF, resize, tăng tương phản)
         ─► (2) PaddleOCR (detect + recognize) ─► dòng text + box
         ─► (3) hậu xử lý (làm sạch dòng)
         ─► (4) trích xuất 4 trường (số CCCD, họ tên, ngày sinh, địa chỉ)
         ─► (5) đăng ký: gợi ý khoa theo lý do + số thứ tự ảo + chỉ đường
```

## 4. Các phần CHƯA ỔN (cần lưu ý / sửa trước khi nộp)

1. **Model Gemini mặc định không tồn tại.** `ai.py` và `ai_rag.py` đang đặt mặc định
   `GEMINI_MODEL = "gemini-3.1-flash-lite"` — **model này không có thật** nên sẽ lỗi 404 nếu
   không đặt biến môi trường. **Nên sửa** về model có thật, ví dụ `gemini-2.0-flash`
   (hoặc đặt `GEMINI_MODEL=gemini-2.0-flash` trong `backend/.env`).
2. **Khoá Gemini hiện tại hết quota / không có quyền model mới** (`limit: 0`) — embedding chạy
   được nhưng bước sinh câu trả lời báo 429/403. Cần API key có hạn mức để demo chatbot trả lời.
3. **OCR phụ thuộc Python ≤ 3.13.** PaddlePaddle chưa có bản cho Python 3.14; phải tạo venv
   bằng `python3.13` + `pip install -r requirements-ocr.txt`. Nếu chạy Python 3.14, phần quét
   ảnh báo lỗi (nhập tay vẫn được).
4. **Dữ liệu chỉ nằm trong bộ nhớ.** Thêm/sửa/xoá khoa (admin), số thứ tự, lượt xem… **reset
   khi khởi động lại** server. Đủ cho demo, nhưng không bền.
5. **Tìm kiếm "cứng" theo chuỗi con.** Truy vấn rất ngắn ("nhi") có thể khớp hơi rộng; câu
   dài chỉ map tốt nhờ chatbot/keyword-overlap, không phải bản tìm kiếm chính.
6. **Trích xuất OCR là heuristic.** Đúng với bố cục CCCD chuẩn; ảnh mờ/nghiêng/bố cục lạ có
   thể sai — đã có form cho người dùng **sửa tay**.
7. **Footer còn để tạm** ("… Hoang Minh Quang dz") — nên sửa lại lịch sự trước khi nộp.
8. **Chưa có test tự động** và **chưa có CI/CD**.
9. **README chưa có link video demo** (đề yêu cầu) — cần bổ sung khi quay xong.

## 5. Hướng cải thiện (nếu có thêm thời gian)

- **Tối ưu đường đi (điểm cộng còn thiếu):** mô hình hoá bệnh viện thành đồ thị (node =
  phòng/sảnh/thang máy, cạnh = lối đi) rồi chạy **BFS/Dijkstra/A\*** từ vị trí hiện tại tới
  phòng đích, highlight path trên SVG. Dữ liệu đã có sẵn `pos`, `floor`, `LANDMARKS` để dựng.
- **Lưu trữ bền:** chuyển dữ liệu khoa + lượt xem + số thứ tự xuống **SQLite/JSON file** để
  không mất khi restart (chỉ cần sửa `repository.py`).
- **Vector store thật cho RAG:** thay in-memory bằng **FAISS/Chroma**, lưu embedding ra đĩa
  để khỏi tính lại mỗi lần khởi động khi dữ liệu lớn.
- **OCR mạnh hơn:** thêm bước căn chỉnh/cắt vùng CCCD (perspective transform), nhận diện
  thêm trường; hoặc dùng template-matching theo vị trí trường để bớt phụ thuộc nhãn.
- **Liên thông sâu Hướng A↔B:** sau khi chatbot gợi ý khoa, cho bấm thẳng sang `/register`
  với lý do khám điền sẵn.
- **Bảo mật/triển khai:** rate-limit API AI, chạy backend bằng gunicorn, build frontend tĩnh,
  thêm test + GitHub Actions (CI).
- **Trải nghiệm:** lưu lịch sử chat vào localStorage; nén ảnh phía client trước khi gửi OCR.

## 6. Nhận xét chung

Dự án **bám sát đề**: luồng người dùng cốt lõi chạy mượt, **làm cả 2 hướng AI** (hiếm, vì đề
chỉ yêu cầu 1) và AI **nằm trong luồng** chứ không phải widget rời (chatbot → trang chi tiết;
OCR → đăng ký → khoa + chỉ đường). Code **tách lớp rõ** (data / repository / web / từng module
AI), mỗi bước có tài liệu riêng và commit history phản ánh tiến độ thực tế. Điểm trừ chính là
vài **mặc định/khoá Gemini** cần chỉnh để demo trơn tru, dữ liệu chưa bền, và **thiếu phần tối
ưu đường đi**. Sửa 3 mục đầu ở §4 là có thể demo đầy đủ.
