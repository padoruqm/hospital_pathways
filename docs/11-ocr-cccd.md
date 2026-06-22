# 11 — Hướng B: OCR quét CCCD để đăng ký khám nhanh

Cho bệnh nhân **chụp/tải ảnh CCCD** → hệ thống OCR tự đọc thông tin điền vào form đăng ký
→ gợi ý khoa theo lý do khám → cấp **số thứ tự ảo** + chỉ đường tới phòng chờ. Bản cơ bản,
**không train model**, dùng **PaddleOCR** có sẵn.

> Code: [`backend/ocr.py`](../backend/ocr.py) (chú thích chi tiết từng bước) và
> [`frontend/src/views/RegisterView.vue`](../frontend/src/views/RegisterView.vue).

## Pipeline OCR (5 bước)

```
Ảnh CCCD ─►(1)Tiền xử lý─►(2)PaddleOCR─► các dòng text ─►(3)Hậu xử lý─►(4)Trích xuất─►(5)Output JSON
```

| Bước | Làm gì | Trong code |
|------|--------|-----------|
| (1) **Tiền xử lý** | Mở ảnh, xoay đúng chiều theo EXIF, thu nhỏ nếu cạnh > 1600px, tăng tương phản | `preprocess()` (Pillow) |
| (2) **Model OCR** | PaddleOCR (PP-OCRv*, `lang='vi'`) đọc toàn bộ chữ → danh sách dòng | `_get_engine()` + `engine.predict()` |
| (3) **Hậu xử lý** | Bỏ khoảng trắng thừa, bỏ dòng rỗng | `postprocess()` |
| (4) **Trích xuất** | Heuristic/regex lấy: số CCCD, họ tên, ngày sinh, giới tính, quốc tịch, quê quán, nơi thường trú | `extract_fields()` |
| (5) **Output** | Trả JSON `{fields, raw_lines}` (kèm dòng thô để đối chiếu) | route `/api/ocr/scan` |

### Vì sao chọn PaddleOCR & không train?
- PaddleOCR là **OCR có sẵn (pretrained)**, hỗ trợ **tiếng Việt** tốt, chạy CPU — hợp với
  yêu cầu "cơ bản, không train". Ta chỉ *dùng* model, không huấn luyện.
- Việc "hiểu" CCCD nằm ở bước (4): nhận diện trường theo **nhãn** ("Họ và tên", "Ngày sinh"…)
  và **mẫu** (regex ngày `dd/mm/yyyy`, dãy số 9/12 chữ số cho số CCCD). So khớp nhãn dùng
  `strip_accents` nên gõ có dấu hay không đều khớp.

### Trích xuất — vài mẹo nhỏ
- **Số CCCD**: dòng nào sau khi bỏ ký tự không phải số còn đúng **9 hoặc 12 chữ số**.
- **Giới tính**: chỉ xét đoạn **ngay sau nhãn "Giới tính"** để tránh dính chữ "Việt **Nam**".
- **Ngày sinh**: mẫu `dd/mm/yyyy` đầu tiên trong toàn văn bản.

## Đăng ký khám & gợi ý khoa

`POST /api/ocr/register` nhận form (họ tên, ngày sinh… + **lý do khám**) và:

1. **Gợi ý khoa** từ lý do: đếm số từ khoá/triệu chứng của mỗi khoa xuất hiện trong lý do,
   chọn khoa nhiều nhất (`_suggest_department`). Cách này hợp với **câu dài** như
   *"tôi bị đau ngực, khó thở"* → **Khoa Tim mạch** (khác với tìm-kiếm-chuỗi-con vốn cần
   khớp nguyên cụm). Không khớp gì → **Quầy Tiếp đón**.
2. **Cấp số thứ tự ảo** theo từng khoa, dạng `A2-001` (toà+tầng + số đếm).
3. Trả về **khoa + hướng dẫn đường đi** để bệnh nhân tới phòng chờ; frontend có nút sang
   thẳng trang chi tiết (sơ đồ tầng + chỉ đường).

## Giao diện — `/register` (link "Đăng ký khám" trên header)

3 bước trên cùng một trang:
1. **Tải ảnh CCCD** → xem trước → bấm *Quét thông tin* (gọi `/api/ocr/scan`, tự điền form).
2. **Kiểm tra/sửa form** + nhập **lý do khám** (luôn sửa được, kể cả khi không quét ảnh).
3. Bấm *Đăng ký & lấy số thứ tự* → màn hình xác nhận: **số thứ tự** lớn, khoa gợi ý, đường
   đi, nút **"Xem sơ đồ & đường đi"** sang trang chi tiết khoa.

## Trang "OCR Debug" — xem trực quan từng bước

Để kiểm thử và giải thích pipeline, có thêm endpoint `POST /api/ocr/debug` và trang
[`/ocr-debug`](../frontend/src/views/OcrDebugView.vue) (link "🔬 Xem các bước xử lý OCR"
trên trang đăng ký). Tải 1 ảnh CCCD, trang hiển thị lần lượt:

1. **Tiền xử lý** — ảnh sau khi xoay/thu nhỏ/tăng tương phản (`preprocessed_image`).
2. **Model** — ảnh có **vẽ bounding box + số thứ tự** từng vùng chữ (`annotated_image`),
   kèm bảng *chữ nhận diện + độ tin cậy* của từng box.
3. **Hậu xử lý** — so sánh dòng **thô** ↔ dòng **đã làm sạch**.
4. **Trích xuất** — bảng các trường lấy được.

Endpoint trả ảnh dưới dạng **data URL base64** nên frontend chỉ việc gán vào `<img :src>`,
không cần lưu file. Đây là công cụ debug, không nằm trong luồng đăng ký chính.

## Cài đặt & lưu ý môi trường ⚠️

PaddlePaddle **chưa có bản cho Python 3.14**. Để chạy OCR, dùng **Python 3.13**:

```bash
cd backend
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt        # lõi (Flask, Gemini…)
pip install -r requirements-ocr.txt    # PaddleOCR (nặng, ~vài trăm MB; tải model lần đầu)
python app.py
```

- Engine được **nạp lười** và dùng lại: lần quét đầu hơi chậm (tải model + khởi tạo).
- Nếu **chưa cài** được PaddleOCR, `/api/ocr/scan` trả lỗi 503 với hướng dẫn, **nhưng phần
  nhập tay + đăng ký vẫn hoạt động** bình thường — luồng Hướng B vẫn demo được đầy đủ.

## Đã kiểm thử
- Quét ảnh mẫu → trích xuất đúng: số CCCD, họ tên, ngày sinh, giới tính, quốc tịch, địa chỉ.
- `register` với *"tôi bị đau ngực, khó thở"* → **Khoa Tim mạch**, cấp số `A2-001`, kèm đường đi.
