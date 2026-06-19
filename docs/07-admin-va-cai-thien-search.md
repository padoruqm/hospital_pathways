# 07 — Trang quản trị (CRUD) & cải thiện tìm kiếm

Bước này thêm **trang quản trị** để thêm/sửa/xoá khoa phòng, và **sửa lại thuật toán
tìm kiếm** cho đúng nhu cầu.

## A. Sửa tìm kiếm: "đau đầu" ≠ "đau bụng"

### Vấn đề
Trước đây mỗi từ trong truy vấn khớp ở bất kỳ đâu đều được +1 điểm. Vì rất nhiều khoa
có chứa từ **"đau"** (đau ngực, đau khớp, đau bụng, đau răng…), nên `"đau đầu"` và
`"đau bụng"` trả về **gần như cùng một danh sách** — không phân biệt được.

> Lưu ý kỹ thuật: khi bỏ dấu tiếng Việt, **"đau" và "đầu" đều thành "dau"**. Vì vậy
> phải dựa vào việc khớp **nguyên cụm** (giữ thứ tự liền nhau) thì mới phân biệt được.

### Cách sửa — ưu tiên khớp nguyên cụm, hạ thấp khớp từ rời
Trong [`backend/hospital_data.py`](../backend/hospital_data.py), hàm `search()` cho điểm:

| Mức khớp | Điểm |
|----------|------|
| Cụm truy vấn nằm trong **tên khoa** | +100 |
| Cụm truy vấn nằm trong **một từ khoá / triệu chứng** (vd "đau đầu" ⊂ "đau đầu kéo dài") | +60 |
| Cụm truy vấn xuất hiện ở bất kỳ trường nào | +20 |
| Nhiều từ rời: **chỉ** cộng khi TẤT CẢ các từ cùng xuất hiện (AND) | +15 |

Điểm mấu chốt là quy tắc cuối: không còn cộng điểm cho **từng** từ rời, nên một từ phổ
biến như "đau" không thể tự kéo cả loạt khoa về. Kết quả thực tế:

```
đau đầu  -> [Khoa Nội thần kinh]
đau bụng -> [Khoa Nội tổng quát, Khoa Sản – Phụ khoa]
đau ngực -> [Khoa Cấp cứu, Khoa Tim mạch]
đau khớp -> [Khoa Cơ xương khớp, Khoa Phục hồi chức năng]
```

Đây vẫn là tìm kiếm "cứng" theo từ khoá; phần hiểu câu tự nhiên sâu hơn (vd "tôi hay
quên, mất ngủ") sẽ do **chatbot RAG** đảm nhiệm ở Giai đoạn 2.

## B. Trang quản trị — CRUD + thống kê

### Backend
Thêm các endpoint ghi (xem [`backend/app.py`](../backend/app.py)):

| Method & path | Chức năng |
|---------------|-----------|
| `POST /api/departments` | Thêm khoa mới (tự sinh `id` từ tên) |
| `PUT /api/departments/<id>` | Sửa khoa |
| `DELETE /api/departments/<id>` | Xoá khoa |
| `GET /api/stats` | Thống kê lượt xem theo khoa |

- Có **validation**: thiếu trường bắt buộc → trả lỗi 400 kèm danh sách lỗi rõ ràng.
- `GET /api/departments/<id>` giờ **đếm lượt xem** để phục vụ thống kê.
- Dữ liệu lưu **trong bộ nhớ** (đơn giản theo yêu cầu) — thay đổi có hiệu lực ngay trong
  phiên chạy, reset khi khởi động lại. Sau này có thể đẩy xuống JSON/CSDL mà không đổi UI.

### Frontend
- Route mới `/admin` (lazy-load) + liên kết **"Quản trị"** trên header.
- [`AdminView.vue`](../frontend/src/views/AdminView.vue): bảng danh sách + nút **Sửa/Xoá**,
  form **thêm/sửa** (từ khoá / triệu chứng / các bước đường đi nhập mỗi dòng một mục),
  và mục **thống kê lượt tra cứu**.
- Đủ trạng thái loading / error / saving; xoá có hộp xác nhận.

> Trang quản trị giữ ở mức gọn theo yêu cầu — đủ minh hoạ tính năng điểm cộng
> "Admin dashboard" mà không làm phức tạp hệ thống.
