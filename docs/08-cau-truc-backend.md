# 08 — Cấu trúc backend: từng file & luồng dữ liệu

Tài liệu này giải thích backend gồm những file nào, mỗi file làm gì, liên hệ với nhau ra
sao, và **dữ liệu được lấy như thế nào** từ lúc người dùng gõ tìm kiếm đến khi nhận JSON.

## Tổng quan các file

```
backend/
├── hospital_data.py   # (1) DỮ LIỆU thuần: danh sách khoa/phòng, toà nhà, điểm mốc
├── text_utils.py      # (2) TIỆN ÍCH chuỗi: bỏ dấu, chuẩn hoá để tìm kiếm
├── repository.py      # (3) XỬ LÝ DỮ LIỆU: đọc, tìm kiếm, thêm/sửa/xoá, thống kê
├── app.py             # (4) TẦNG WEB: định nghĩa route HTTP, trả JSON
└── requirements.txt   # thư viện cần cài (Flask, flask-cors, python-dotenv)
```

Nguyên tắc tách file: **mỗi file một trách nhiệm**. Nhờ vậy file dữ liệu không bị lẫn
code, và logic xử lý không bị lẫn vào tầng web — dễ đọc, dễ sửa, dễ test.

## Vai trò & liên hệ giữa các file

```
        (HTTP request)
              │
              ▼
   ┌─────────────────────┐
   │      app.py         │  Tầng web: nhận request, gọi repository, trả JSON
   │  (Flask routes)     │  — KHÔNG chứa logic dữ liệu
   └──────────┬──────────┘
              │ gọi hàm
              ▼
   ┌─────────────────────┐      dùng để chuẩn hoá chuỗi
   │   repository.py     │ ───────────────► text_utils.py  (2)
   │  (đọc/tìm/CRUD/     │
   │   thống kê)         │ ───────────────► hospital_data.py (1)
   └─────────────────────┘      đọc/ghi trên danh sách DEPARTMENTS
```

| File | Trách nhiệm | Phụ thuộc |
|------|-------------|-----------|
| **hospital_data.py** | Chỉ chứa dữ liệu: `BUILDINGS`, `DEPARTMENTS` (20 khoa), `LANDMARKS`. Không có hàm. | — |
| **text_utils.py** | `strip_accents()` (bỏ dấu) và `normalize()` (bỏ dấu + chỉ giữ chữ/số). Hàm thuần. | — |
| **repository.py** | Mọi thao tác trên dữ liệu: `get_all`, `get_by_id`, `search`, `create/update/delete_department`, `validate`, `record_view`, `get_stats`. | hospital_data, text_utils |
| **app.py** | Khai báo các route `/api/...`, gọi repository, đóng gói JSON, xử lý mã lỗi. | repository, Flask |

> **Vì sao tách `repository.py` khỏi `app.py`?** Để tầng web chỉ lo HTTP (nhận tham số,
> trả mã 200/400/404). Nếu sau này đổi từ dữ liệu trong bộ nhớ sang CSDL thật, chỉ cần
> sửa `repository.py`, không động tới route hay frontend.

## Dữ liệu được lấy như thế nào?

Dữ liệu **không nằm ở CSDL ngoài** mà là một danh sách Python (`DEPARTMENTS`) nạp sẵn vào
bộ nhớ khi server khởi động. Ví dụ luồng một lần **tìm kiếm**:

```
1. Người dùng gõ "đau bụng" trên web
2. Frontend gọi:  GET /api/search?q=đau%20bụng
3. app.py        : route /api/search nhận q, gọi repo.search("đau bụng")
4. repository.py : - normalize("đau bụng")  -> "daubung"   (text_utils)
                   - duyệt DEPARTMENTS, khoa nào có chuỗi "daubung" trong phần
                     dữ liệu tìm kiếm thì khớp (khớp ở tên xếp trước)
5. app.py        : đóng gói kết quả thành JSON { query, count, results } trả về
6. Frontend      : hiển thị danh sách thẻ khoa
```

Luồng **xem chi tiết** tương tự: `GET /api/departments/<id>` → `repo.get_by_id(id)` →
`repo.record_view(id)` (đếm lượt xem cho thống kê) → trả JSON đầy đủ kèm `directions`, `pos`.

Luồng **quản trị** (thêm/sửa/xoá): `app.py` nhận JSON → `repo.validate()` kiểm tra →
`repo.create/update/delete_department()` đổi trực tiếp trên `DEPARTMENTS`. Vì dữ liệu ở
trong bộ nhớ nên thay đổi có hiệu lực ngay nhưng **reset khi khởi động lại server**.

## Tìm kiếm hoạt động ra sao (bản đơn giản)

`repository.search()` chỉ dựa vào **một quy tắc** dễ giải thích:

1. Chuẩn hoá truy vấn và dữ liệu **giống nhau**: bỏ dấu, bỏ khoảng trắng và ký tự đặc
   biệt (qua `text_utils.normalize`). Ví dụ `"X-quang"`, `"x quang"`, `"xquang"` đều thành
   `"xquang"`.
2. Một khoa **khớp** nếu chuỗi truy vấn là **chuỗi con** của phần dữ liệu tìm kiếm được
   (tên + nhóm + số phòng + từ khoá + triệu chứng).
3. Khoa khớp ngay ở **tên** thì xếp lên trước.

Nhờ so khớp **nguyên cụm**, các triệu chứng khác nhau ra khoa khác nhau:

```
đau đầu  -> Khoa Nội thần kinh
đau bụng -> Khoa Nội tổng quát, Khoa Sản – Phụ khoa
đau ngực -> Khoa Cấp cứu, Khoa Tim mạch
```

> Đánh đổi của cách đơn giản này: truy vấn rất ngắn (vd "nhi") có thể khớp hơi rộng do là
> chuỗi con của vài từ khác — nhưng khoa đúng (Khoa Nhi) vẫn đứng đầu nhờ ưu tiên khớp tên.
> Việc hiểu câu tự nhiên sâu hơn sẽ do **chatbot RAG** đảm nhiệm ở Giai đoạn 2.
