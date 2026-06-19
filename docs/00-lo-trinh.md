# 00 — Lộ trình xây dựng & quy ước commit

Tài liệu này giải thích **cách dự án được xây dựng từng bước**, để khi review có thể
đọc lần lượt và hiểu rõ từng quyết định kỹ thuật.

## Vì sao chia nhỏ?

Đề bài yêu cầu *"commit history phản ánh tiến độ làm việc thực tế — không nộp 1 commit
duy nhất"*. Vì vậy mỗi commit ở đây là **một bước có ý nghĩa** (một tính năng hoặc một
lớp kiến trúc), kèm tài liệu trong `docs/` để giải thích bước đó làm gì và vì sao.

## Lộ trình các giai đoạn

### Giai đoạn 1 — Web nền tảng (30 điểm)
| # | Bước | Nội dung |
|---|------|----------|
| 1 | Khởi tạo | Cấu trúc repo, README, .gitignore, tài liệu lộ trình *(commit này)* |
| 2 | Backend & dữ liệu | Flask API + mock 18+ khoa/phòng, endpoint tìm kiếm/chi tiết |
| 3 | Frontend & tìm kiếm | Vue 3 + TS, trang chủ với ô tìm kiếm gọi API |
| 4 | Kết quả & đường đi | Trang chi tiết khoa (tầng, phòng, giờ) + hướng dẫn đường đi từng bước |
| 5 | Sơ đồ tầng & mobile | Sơ đồ tầng SVG đơn giản highlight phòng + tinh chỉnh responsive |

> Sau Giai đoạn 1 sẽ **tạm dừng** để người đọc nắm được luồng trước khi sang phần AI.

### Giai đoạn 2 — AI Hướng A: Chatbot RAG (một phần của 40 điểm)
Chatbot tiếng Việt: bệnh nhân mô tả triệu chứng → RAG tìm khoa phù hợp → trả lời kèm đường đi.

### Giai đoạn 3 — AI Hướng B: OCR CCCD (một phần của 40 điểm)
Upload ảnh CCCD → OCR trích xuất thông tin → tự điền form đăng ký → gợi ý khoa + số thứ tự ảo.

### Giai đoạn 4 — Điểm cộng (tối đa +30 điểm)
- Tối ưu đường đi bằng đồ thị (BFS/Dijkstra/A\*) + highlight path trên SVG.
- Kết hợp 2 hướng AI liên thông dữ liệu.
- Admin dashboard CRUD khoa/phòng + thống kê lượt tra cứu.

## Quy ước commit

- Mỗi commit nhỏ, tập trung một việc; tiêu đề rõ ràng theo dạng `loại: mô tả`.
- Tác giả commit chỉ là chủ repo (không thêm co-author nào khác).
- Mỗi giai đoạn có ít nhất một tài liệu `docs/NN-*.md` đi kèm.
