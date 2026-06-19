# Hospital Wayfinding System — Hệ thống điều hướng bệnh nhân

> Web giúp bệnh nhân **tự tra cứu và tìm đường** trong bệnh viện: tìm khoa/phòng,
> xem sơ đồ tầng, và nhận hướng dẫn đường đi từng bước. Về sau sẽ tích hợp AI
> (chatbot RAG + OCR CCCD) để hỗ trợ bệnh nhân nhập viện nhanh hơn.

Đây là bài test tuyển dụng Intern (Web & AI). Repo được xây **từng bước một**,
mỗi commit là một bước có ý nghĩa và đi kèm tài liệu trong thư mục [`docs/`](docs/)
để dễ theo dõi tiến độ và giải thích quyết định kỹ thuật.

---

## 1. Tech stack

| Lớp        | Công nghệ                          |
| ---------- | ---------------------------------- |
| Frontend   | Vue 3 + TypeScript + Vite          |
| Backend    | Flask (Python)                     |
| AI         | Google Gemini API (sẽ thêm sau)    |

## 2. Trạng thái hiện tại

- [x] **GĐ 1 — Web nền tảng**: tìm kiếm, trang kết quả, sơ đồ tầng, hướng dẫn đường đi ✅
- [ ] GĐ 2 — AI Hướng A: Chatbot RAG hỏi đáp tiếng Việt (Gemini)
- [ ] GĐ 3 — AI Hướng B: OCR quét CCCD đăng ký khám nhanh
- [~] GĐ 4 — Điểm cộng: **admin dashboard (xong)**; tối ưu đường đi (đồ thị) & kết hợp 2 hướng AI (sau)

> Chi tiết từng bước xem trong [`docs/`](docs/). Mỗi tài liệu tương ứng một (vài) commit.

### Tính năng đã xong (GĐ 1 + cải thiện)
- Trang chủ với ô tìm kiếm (debounce) + duyệt toàn bộ khoa theo nhóm.
- Tìm kiếm chịu được gõ có/không dấu, gõ liền (`xquang` ~ `x-quang`); **ưu tiên khớp
  nguyên cụm** nên "đau đầu" và "đau bụng" ra khoa khác nhau.
- Trang chi tiết khoa: toà nhà, tầng, phòng, giờ làm việc, mô tả.
- Sơ đồ tầng SVG highlight phòng cần đến.
- Hướng dẫn đường đi từng bước dạng text.
- **Trang quản trị `/admin`**: thêm/sửa/xoá khoa phòng + thống kê lượt tra cứu.
- Giao diện **xanh da trời**, mobile-first, xử lý đủ trạng thái loading / error / empty.

## 3. Cấu trúc thư mục

```
project_hospital_pathways/
├── backend/          # Flask API + mock data bệnh viện (thêm ở GĐ 1)
├── frontend/         # Vue 3 + TS SPA (thêm ở GĐ 1)
├── docs/             # Tài liệu giải thích từng bước build
└── README.md
```

## 4. Hướng AI đã chọn

Đề cho chọn **một** trong hai hướng AI. Dự án này sẽ làm **cả hai** (Hướng A trước,
rồi Hướng B) để nhắm thêm điểm cộng "Kết hợp cả hai hướng AI". Lý do chọn từng
hướng sẽ được ghi rõ trong tài liệu của giai đoạn tương ứng.

## 5. Cài đặt & chạy

Cần **2 cửa sổ terminal**: một cho backend, một cho frontend.

### Backend (Flask) — cổng 5057
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # (tuỳ chọn) chỉnh PORT, thêm GEMINI_API_KEY sau
python app.py                      # http://localhost:5057
```
> Mặc định cổng 5057 để tránh đụng AirPlay Receiver (chiếm 5000) trên macOS. Đổi bằng biến `PORT`.

### Frontend (Vue 3 + Vite) — cổng 5173
```bash
cd frontend
npm install
npm run dev                        # http://localhost:5173
```
Mở trình duyệt tại **http://localhost:5173**. Vite tự proxy `/api` sang backend nên không cần cấu hình thêm.

## 6. Tài liệu từng bước

| Tài liệu | Nội dung |
|----------|----------|
| [00 — Lộ trình](docs/00-lo-trinh.md) | Cách dự án được build từng bước & quy ước commit |
| [02 — Backend & dữ liệu](docs/02-backend-va-du-lieu.md) | Flask API + mock 20 khoa/phòng + tìm kiếm |
| [03 — Frontend & tìm kiếm](docs/03-frontend-va-tim-kiem.md) | Scaffold Vue 3 + trang chủ tìm kiếm |
| [04 — Chi tiết & đường đi](docs/04-trang-chi-tiet-va-duong-di.md) | Trang chi tiết khoa + hướng dẫn từng bước |
| [05 — Sơ đồ tầng & responsive](docs/05-so-do-tang-va-responsive.md) | Sơ đồ SVG highlight phòng + mobile |
| [06 — Giao diện xanh da trời](docs/06-giao-dien-xanh-da-troi.md) | Đổi màu chủ đạo + làm gọn giao diện |
| [07 — Admin & cải thiện search](docs/07-admin-va-cai-thien-search.md) | Trang quản trị CRUD + sửa tìm kiếm |

---

*Tài liệu nộp bài (video demo, khó khăn & cải thiện...) sẽ được hoàn thiện ở cuối dự án.*
