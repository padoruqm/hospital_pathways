# 06 — Giao diện gọn hơn & màu chủ đạo xanh da trời

Theo yêu cầu: làm giao diện **đơn giản hơn** và đổi **màu chủ đạo sang xanh da trời**.

## Thay đổi màu — một chỗ duy nhất

Toàn bộ màu được khai báo bằng **CSS variables** trong
[`frontend/src/assets/styles.css`](../frontend/src/assets/styles.css), nên chỉ cần đổi ở
`:root` là cả app đổi theo (thẻ, badge, sơ đồ tầng, các bước đường đi…):

| Biến | Trước (teal) | Sau (xanh da trời) |
|------|--------------|--------------------|
| `--color-primary` | `#0d9488` | `#0284c7` (sky-600) |
| `--color-primary-dark` | `#0f766e` | `#0369a1` (sky-700) |
| `--color-primary-light` | `#ccfbf1` | `#e0f2fe` (sky-100) |

`theme-color` trong `index.html` cũng đổi theo để thanh trình duyệt trên mobile khớp màu.

## Làm gọn hơn

- **Header**: từ thanh đặc màu → **nền trắng, chữ xanh, viền dưới mảnh** → nhẹ và sạch hơn.
- **Bo góc** nhỏ lại (`--radius` 14px → 10px) và **đổ bóng phẳng hơn** (bớt 1 lớp shadow).
- Header dùng layout `inner` (flex, space-between) để sẵn chỗ cho liên kết **Quản trị** ở bước sau.

> Vì màu tập trung ở biến CSS nên thay đổi này gần như không đụng tới logic — minh hoạ lợi ích
> của việc tách style ra biến dùng chung ngay từ đầu.
