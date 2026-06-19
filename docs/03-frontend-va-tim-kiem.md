# 03 — Frontend Vue 3 + TS & trang chủ tìm kiếm

Bước này dựng bộ khung frontend và **tính năng đầu tiên người dùng chạm vào: tìm kiếm**.

## Công nghệ & lý do

- **Vue 3 + `<script setup>` + TypeScript**: component gọn, type an toàn khi map dữ liệu API.
- **Vite**: dev server nhanh, có sẵn **proxy** `/api → http://localhost:5001` nên frontend gọi
  đường dẫn tương đối, không cần hard-code host hay xử lý CORS khi dev.
- **vue-router**: chuẩn bị sẵn điều hướng nhiều trang (trang chi tiết thêm ở bước sau).

## Cấu trúc thư mục frontend

```
frontend/src/
├── main.ts                 # điểm khởi động, gắn router + CSS toàn cục
├── App.vue                 # khung: header + <RouterView> + footer
├── types.ts                # kiểu TS khớp JSON backend trả về
├── api/client.ts           # gom mọi lời gọi API + xử lý lỗi một chỗ
├── router/index.ts         # khai báo route (hiện mới có trang chủ)
├── assets/styles.css       # biến màu + style toàn cục (mobile-first)
├── components/
│   ├── SearchBar.vue       # ô tìm kiếm có debounce
│   └── DepartmentCard.vue  # thẻ hiển thị 1 khoa/phòng
└── views/
    └── HomeView.vue        # trang chủ: tìm kiếm + duyệt tất cả khoa
```

## Luồng dữ liệu

```
HomeView ──(gõ từ khoá)──▶ SearchBar ──debounce 300ms──▶ onSearch()
                                                            │
                                          api/client.ts ◀───┘
                                                │ fetch /api/search?q=…
                                          Flask backend
```

- **`api/client.ts`** là lớp duy nhất gọi `fetch`. Mỗi hàm có kiểu trả về rõ ràng
  (`DepartmentSummary[]`, `SearchResponse`…) và ném `Error` với message từ backend khi lỗi.
- **`SearchBar.vue`** *debounce* 300ms: chỉ gọi API khi người dùng ngừng gõ, tránh spam request.

## Xử lý 3 trạng thái (loading / error / empty)

`HomeView` thể hiện đầy đủ các trạng thái — một tiêu chí chấm điểm của đề:

| Trạng thái | Hiển thị |
|------------|----------|
| Đang tải / đang tìm | spinner + chữ "Đang tìm…" |
| Lỗi mạng/API | dòng ⚠️ kèm message lỗi |
| Không có kết quả | gợi ý từ khoá khác |
| Có dữ liệu | lưới thẻ `DepartmentCard` |

Mặc định (chưa gõ gì) trang chủ **liệt kê toàn bộ khoa gom theo nhóm** để bệnh nhân duyệt nhanh.

## Tinh chỉnh tìm kiếm phía backend

Khi ráp với giao diện, phát hiện người dùng hay gõ liền như `"xquang"`. Đã bổ sung hàm
`_compact()` ở backend (bỏ khoảng trắng/dấu gạch) nên `"xquang"`, `"x-quang"`, `"x quang"`
đều ra **Phòng X-quang**. Đây là ví dụ điển hình: giao diện thực tế giúp lộ ra thiếu sót của API.

## Chạy frontend

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173 (cần backend chạy ở cổng 5001)
```

> Lưu ý: chạy backend trước (`cd backend && python app.py`) để Vite proxy gọi được API.
