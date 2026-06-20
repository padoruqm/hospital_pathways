# 09 — Chatbot AI tư vấn khoa khám (Gemini, bản đơn giản)

Bước đầu của Giai đoạn 2 (Hướng A): cho bệnh nhân **nhắn tiếng Việt tự nhiên** mô tả
triệu chứng, chatbot gợi ý khoa khám kèm tầng/phòng/giờ. **Chưa dùng RAG** — giữ đơn
giản để thử nghiệm System Instruction trước.

## Cách hoạt động

Thay vì truy hồi (RAG), ta **nhồi cả 20 khoa vào System Instruction** rồi để Gemini tự
tư vấn dựa trên đó. Với dữ liệu nhỏ (20 khoa) cách này đủ tốt và rất dễ hiểu.

```
Người dùng (web /chat)
      │  POST /api/ai/chat { message, history }
      ▼
backend/ai.py  ── system_instruction = nhân cách + DANH SÁCH KHOA (sinh từ repository)
      │           contents = lịch sử hội thoại + câu hỏi mới
      ▼
Google Gemini (gemini-2.5-flash, temperature 0.3)
      │  trả lời text
      ▼
{ status: "success", reply }  ──► hiển thị bong bóng chat
```

### Điểm chính trong [`backend/ai.py`](../backend/ai.py)
- **System Instruction sinh động** từ `repository.get_all()` (hàm `_departments_context`),
  nên danh sách khoa trong prompt **luôn khớp** dữ liệu thật — sửa/thêm khoa ở admin là
  prompt tự cập nhật, không phải chép tay.
- **`temperature=0.3`** thấp để model bám dữ liệu, hạn chế "bịa" khoa không có.
- **Lịch sử hội thoại** do frontend giữ và gửi kèm mỗi lần → hỏi tiếp có ngữ cảnh
  (không cần lưu session ở server, đơn giản hoá).
- **Không cần khoá vẫn chạy**: nếu thiếu `GEMINI_API_KEY`, `/api/ai/chat` trả lỗi 503 với
  thông báo rõ ràng; các tính năng khác của web không bị ảnh hưởng.

### Tầng web — [`backend/app.py`](../backend/app.py)
Route AI được gom trong một **Blueprint** (`ai_bp`) và gắn vào app dưới tiền tố `/api/ai`:
`app.register_blueprint(ai_bp, url_prefix="/api/ai")` → endpoint cuối là `POST /api/ai/chat`.

### Frontend — [`ChatView.vue`](../frontend/src/views/ChatView.vue)
- Trang `/chat` (link **"Trợ lý AI"** trên header), giao diện bong bóng chat quen thuộc.
- Giữ mảng `messages` ngay trong component, gửi kèm làm `history`.
- Có gợi ý câu hỏi mẫu, hiệu ứng "đang gõ", xử lý trạng thái gửi/lỗi.

## Cấu hình khoá Gemini

```bash
# backend/.env
GEMINI_API_KEY=  # dán API key lấy từ Google AI Studio
```
Lấy key miễn phí tại Google AI Studio, dán vào `backend/.env`, khởi động lại backend là
chat hoạt động. Khi chưa có key, mở `/chat` vẫn được — gửi tin sẽ hiện thông báo cần cấu hình key.

## Bước tiếp theo

- **RAG**: thay vì nhồi cả 20 khoa, chỉ truy hồi vài khoa liên quan nhất tới câu hỏi rồi
  mới đưa vào prompt — cần khi dữ liệu lớn dần.
- Gắn kết quả chatbot với **đường đi/sơ đồ** trong web (liên thông dữ liệu) để bệnh nhân
  bấm thẳng sang trang chi tiết khoa được gợi ý.
