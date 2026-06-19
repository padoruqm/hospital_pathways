# 04 — Trang chi tiết khoa & hướng dẫn đường đi

Bước này nối **tìm kiếm → kết quả → chi tiết**, hoàn thiện luồng cốt lõi đề yêu cầu:
*tìm kiếm → kết quả → xem hướng dẫn đường đi từng bước*.

## Điều hướng

Thêm route động `/department/:id`. Mỗi `DepartmentCard` ở trang chủ giờ là một
`RouterLink` dẫn tới trang chi tiết tương ứng:

```
HomeView (thẻ khoa)  ──click──▶  /department/tim-mach  ──▶  DepartmentDetailView
```

- Trang chi tiết được **lazy-load** (`() => import(...)`) nên trang chủ tải nhẹ hơn,
  code của trang chi tiết chỉ tải khi cần (thấy rõ qua chunk riêng khi `npm run build`).
- `scrollBehavior` đưa trang về đầu khi chuyển route — trải nghiệm mobile mượt hơn.

## Trang chi tiết hiển thị gì

[`DepartmentDetailView.vue`](../frontend/src/views/DepartmentDetailView.vue) gọi
`GET /api/departments/:id` và trình bày:

1. **Tên khoa + nhóm + mô tả**
2. **Bảng thông tin**: toà nhà · tầng · phòng · giờ làm việc
3. **Hướng dẫn đường đi từng bước** (thành phần `DirectionSteps`)
4. **Từ khoá liên quan** (chips)

Trang có đủ trạng thái **loading / error**; khi đổi từ khoa này sang khoa khác,
một `watch` trên `route.params.id` sẽ tải lại dữ liệu.

## Hướng dẫn đường đi — `DirectionSteps.vue`

Nhận `steps: string[]` từ backend và render thành danh sách **đánh số có đường nối dọc**,
kết thúc bằng mốc 🏁 "Đến nơi" để bệnh nhân biết đã tới đích. Ví dụ với Khoa Tim mạch:

```
1  Vào cửa chính Nhà A, đi tới thang máy giữa sảnh
2  Lên tầng 2
3  Ra khỏi thang máy rẽ trái, đi qua phòng 201, phòng 205 nằm bên phải
🏁 Đến nơi: Khoa Tim mạch — Phòng 205
```

Văn bản đường đi nằm trong dữ liệu (`directions`) ở backend, nên dễ chỉnh sửa và sau này
có thể **sinh tự động từ đồ thị** khi làm điểm cộng tối ưu đường đi.

## Còn thiếu gì ở bước này?

Trang chi tiết hiện mô tả đường đi bằng chữ. **Sơ đồ tầng SVG highlight phòng** sẽ được
thêm ở bước kế tiếp (05) cùng với việc tinh chỉnh responsive cho điện thoại.
