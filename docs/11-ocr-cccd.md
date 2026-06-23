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
| (4) **Trích xuất** | Heuristic/regex lấy **4 trường**: số CCCD, họ tên, ngày sinh, địa chỉ | `extract_fields()` |
| (5) **Output** | Trả JSON `{fields, raw_lines}` (kèm dòng thô để đối chiếu) | route `/api/ocr/scan` |

### Vì sao chọn PaddleOCR & không train?
- PaddleOCR là **OCR có sẵn (pretrained)**, hỗ trợ **tiếng Việt** tốt, chạy CPU — hợp với
  yêu cầu "cơ bản, không train". Ta chỉ *dùng* model, không huấn luyện.
- Việc detect đuúng thông tin CCCD nằm ở bước (4): nhận diện trường theo **nhãn** ("Họ và tên", "Ngày sinh"…)
  và **mẫu** (regex ngày `dd/mm/yyyy`, dãy số 9/12 chữ số cho số CCCD). So khớp nhãn dùng
  `strip_accents` nên gõ có dấu hay không đều khớp.

### Giải thích kỹ BƯỚC 4 — trích xuất 4 trường

Đầu vào của bước này là **danh sách dòng chữ** đã làm sạch (vd):

```
['CAN CUOC CONG DAN',
 'So / No: 001099012345',
 'Ho va ten / Full name',
 'NGUYEN VAN AN',
 'Ngay sinh / Date of birth: 12/05/1990',
 'Noi thuong tru / Place of residence',
 '15 Tran Hung Dao, Ha Noi']
```

Ta lấy mỗi trường bằng **một cách đơn giản**, chia làm 2 nhóm:

**a) Lấy theo MẪU (pattern) — không cần nhãn**
- **Số CCCD**: duyệt từng dòng, bỏ hết ký tự không phải số (`re.sub(r"\D", "", line)`);
  dòng nào còn **đúng 9 chữ số (CMND cũ) hoặc 12 chữ số (CCCD)** thì lấy.
- **Ngày sinh**: tìm **mẫu ngày `dd/mm/yyyy` đầu tiên** trong toàn bộ chữ (regex `_DATE_RE`),
  rồi chuẩn hoá về dạng 2 chữ số ngày/tháng.

**b) Lấy theo NHÃN — dùng `value_below_label(lines, keywords)`**

Mấu chốt bố cục CCCD: **dòng nhãn đứng riêng, GIÁ TRỊ nằm ở DÒNG NGAY DƯỚI**:

```
"Họ và tên / Full name"      ← dòng nhãn (song ngữ)
"NGUYEN VAN AN"              ← giá trị thật nằm ở DÒNG DƯỚI
```

Hàm chỉ làm 3 việc, đọc là hiểu:
1. Tìm dòng có **chứa nhãn** — so khớp **không dấu** (`strip_accents`) nên "Họ và tên",
   "ho va ten", "HO VA TEN" đều khớp.
2. Nếu dòng đó viết kiểu `"nhãn: giá trị"` (giá trị cùng dòng) → lấy phần **sau dấu ':'**.
3. Nếu không → lấy luôn **dòng kế tiếp** làm giá trị.

```python
def value_below_label(lines, keywords):
    for i, line in enumerate(lines):
        if not any(kw in strip_accents(line) for kw in keywords):
            continue
        if ":" in line:                       # (2) giá trị cùng dòng
            after = line.split(":", 1)[1].strip()
            if after:
                return after
        if i + 1 < len(lines):                # (3) giá trị ở dòng kế tiếp
            return lines[i + 1].strip()
        return ""
    return ""
```

Áp dụng: **Họ tên** ← nhãn `["ho va ten", "ho ten", "full name"]`; **Địa chỉ** ← nhãn
`["noi thuong tru", "thuong tru", "place of residence", "dia chi", ...]`.

> **Vì sao cách này đơn giản hơn bản trước & vẫn đúng?** Bản cũ cố lấy text *cùng dòng* với
> nhãn rồi phải làm sạch nhiều (bỏ '/', '|', 'I', loại nhãn tiếng Anh "Full name"…) — rối và
> dễ lấy nhầm chính nhãn tiếng Anh làm giá trị. Bản mới đi thẳng vào quy luật "giá trị nằm ở
> **dòng dưới**", nên **không cần** mấy bước làm sạch đó nữa.
>
> Lưu ý: lỗi "ra Full name thay vì tên" là ở **bước (4) trích xuất**, KHÔNG phải tiền xử lý /
> text detection / recognition — PaddleOCR đã tách đúng 2 dòng, chỉ là logic lấy sai dòng.

> Đã **rút gọn còn 4 trường** (số CCCD, họ tên, ngày sinh, địa chỉ) — vừa đủ cho form đăng ký,
> code gọn và dễ giải thích hơn. Các trường khác (giới tính, quốc tịch, quê quán) đã bỏ.

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

## Thử từng bước pipeline — notebook Colab

Để xem trực quan từng bước (tiền xử lý → bounding box → hậu xử lý → trích xuất), dùng
notebook [`backend/ocr_pipeline_colab.ipynb`](../backend/ocr_pipeline_colab.ipynb): tải lên
Google Colab, chạy lần lượt các cell, mỗi bước hiển thị ảnh/kết quả tương ứng. Notebook
độc lập với web nên không cần chạy backend.

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
- Quét ảnh mẫu → trích xuất đúng **4 trường**: số CCCD, họ tên, ngày sinh, địa chỉ
  (đúng cả 3 bố cục: giá trị ở dòng dưới, biến thể '|'→'I', và giá trị cùng dòng).
- `register` với *"tôi bị đau ngực, khó thở"* → **Khoa Tim mạch**, cấp số `A2-001`, kèm đường đi.
