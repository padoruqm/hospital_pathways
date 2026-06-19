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

Dự án đang ở **Giai đoạn 1 — Web nền tảng**. Các giai đoạn:

- [ ] **GĐ 1 — Web nền tảng**: tìm kiếm, trang kết quả, sơ đồ tầng, hướng dẫn đường đi *(đang làm)*
- [ ] GĐ 2 — AI Hướng A: Chatbot RAG hỏi đáp tiếng Việt (Gemini)
- [ ] GĐ 3 — AI Hướng B: OCR quét CCCD đăng ký khám nhanh
- [ ] GĐ 4 — Điểm cộng: tối ưu đường đi (đồ thị), kết hợp 2 hướng AI, admin dashboard

> Chi tiết từng bước xem trong [`docs/`](docs/). Mỗi tài liệu tương ứng một (vài) commit.

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

> Hướng dẫn cài đặt chi tiết sẽ được bổ sung dần theo từng giai đoạn. Xem
> [`docs/01-tong-quan-va-kien-truc.md`](docs/01-tong-quan-va-kien-truc.md) để bắt đầu.

---

*Tài liệu nộp bài (video demo, danh sách tính năng, khó khăn...) sẽ được hoàn thiện ở cuối dự án.*
