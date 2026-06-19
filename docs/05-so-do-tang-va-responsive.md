# 05 — Sơ đồ tầng SVG & hoàn thiện responsive

Bước cuối của Giai đoạn 1: thêm **sơ đồ tầng trực quan** và rà lại trải nghiệm mobile.

## Sơ đồ tầng — `FloorMap.vue`

Đề yêu cầu *"sơ đồ tầng đơn giản, highlight phòng đang xem (SVG hoặc canvas)"*. Theo đúng
yêu cầu giữ **đơn giản**, component dùng **SVG thuần** (không ảnh thật):

- Gọi `GET /api/floors`, lọc các phòng **cùng toà nhà + cùng tầng** với khoa đang xem.
- Xếp các phòng thành các ô dọc theo một "hành lang", thứ tự trái→phải theo `pos.x` trong dữ liệu.
- **Tô sáng** ô của phòng đích (viền + nền màu chủ đạo) kèm chú thích (legend).

```
┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐
│ 201 │ │ 205 │ │ 208 │ │ 210 │   ← 205 được tô sáng = phòng cần đến
└──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘
═══╧═══════╧═══════╧═══════╧════  Hành lang
            ⬆ Thang máy / lối vào tầng
```

> Vì sao SVG mà không phải ảnh? SVG **co giãn theo màn hình** không vỡ nét, nhẹ, và highlight
> chỉ là đổi class. Sơ đồ hiện mang tính minh hoạ từ dữ liệu mock; có thể thay bằng sơ đồ vẽ
> tay/chi tiết hơn sau mà không đổi logic. Toạ độ `pos` đã có sẵn cũng sẽ dùng lại cho phần
> **tối ưu đường đi bằng đồ thị** (điểm cộng).

Sơ đồ được đặt **ngay phía trên** phần hướng dẫn đường đi trong trang chi tiết, để bệnh nhân
vừa thấy vị trí phòng, vừa đọc các bước đi.

## Responsive / mobile-first

Toàn bộ giao diện được thiết kế ưu tiên điện thoại ngay từ đầu:

- `meta viewport` chuẩn; khung nội dung giới hạn `max-width: 720px`, căn giữa.
- Lưới thẻ khoa: **1 cột trên mobile**, tự lên **2 cột** từ 560px (`@media`).
- Ô tìm kiếm, nút, vùng chạm đủ lớn cho ngón tay; header dính (sticky) để luôn quay về trang chủ.
- SVG sơ đồ `width: 100%` nên co giãn vừa mọi bề ngang màn hình.

## Kết thúc Giai đoạn 1

Luồng cốt lõi đã chạy đầy đủ:

```
Trang chủ (tìm kiếm / duyệt) → Kết quả → Chi tiết khoa
   → Sơ đồ tầng highlight phòng → Hướng dẫn đường đi từng bước
```

Các giai đoạn tiếp theo (AI Hướng A → Hướng B → điểm cộng) sẽ **gắn thêm** vào nền tảng này
mà không phải viết lại: backend đã có sẵn `keywords/symptoms` cho RAG và `pos/floor` cho đồ thị.
