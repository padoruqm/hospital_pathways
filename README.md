# Hospital Wayfinding System — Hệ thống điều hướng bệnh nhân

Web giúp bệnh nhân **tự tra cứu và tìm đường trong bệnh viện** và **đăng ký khám nhanh**:
tìm khoa/phòng, xem sơ đồ tầng, nhận hướng dẫn đường đi từng bước; hỏi đáp triệu chứng
bằng AI; quét CCCD để điền form đăng ký. Tích hợp **AI cả hai hướng**: Chatbot (Hướng A)
và OCR CCCD (Hướng B).

- **Repository:** https://github.com/padoruqm/hospital_pathways
- **Video demo:** _(sẽ cập nhật link YouTube/Drive)_

---

## 1. Mô tả & vấn đề giải quyết

Bệnh nhân đến bệnh viện lần đầu thường bối rối: khám khoa nào, tầng mấy, lấy số ở đâu.
Web này giúp họ **tự phục vụ** qua 3 cách:

1. **Tìm kiếm** khoa/phòng/dịch vụ → xem tầng, phòng, giờ làm việc, **sơ đồ tầng** và
   **chỉ đường từng bước**.
2. **Hỏi trợ lý AI** bằng tiếng Việt tự nhiên ("tôi bị đau ngực, khó thở") → được gợi ý
   khoa phù hợp kèm vị trí.
3. **Đăng ký khám nhanh**: chụp/tải ảnh CCCD → OCR tự điền thông tin → gợi ý khoa theo lý
   do khám → cấp **số thứ tự ảo** và chỉ đường tới phòng chờ.

Dữ liệu bệnh viện được **mock 20 khoa/phòng** (2 toà nhà, 4 tầng).

## 2. Hướng AI đã chọn & lý do

Đề cho chọn **một** trong hai hướng; dự án này làm **cả hai** để nhắm điểm cộng *"Kết hợp
cả hai hướng AI"* và để AI bao trùm trọn luồng bệnh nhân:

- **Hướng A — Chatbot hỏi đáp (RAG):** phù hợp bệnh nhân **chưa biết nên khám khoa nào**,
  chỉ mô tả triệu chứng. Làm **2 chế độ** để so sánh:
  - *System Instruction*: nhồi toàn bộ khoa vào prompt (đơn giản).
  - *RAG*: embedding + truy hồi vài khoa liên quan rồi mới hỏi LLM, **trả kèm "nguồn"**
    bấm được sang trang chi tiết/đường đi.
- **Hướng B — OCR quét CCCD:** phù hợp khâu **đăng ký tại quầy** — giảm thao tác nhập tay.

> AI **nằm trong luồng** chứ không phải widget tách rời: chatbot → trang chi tiết khoa;
> OCR → đăng ký → khoa gợi ý + chỉ đường.

## 3. Kiến trúc hệ thống

```
┌─────────────── Frontend (Vue 3 + TS + Vite) ───────────────┐
│  /         tìm kiếm + duyệt khoa                            │
│  /department/:id  chi tiết + sơ đồ tầng SVG + chỉ đường     │
│  /chat     chatbot (gạt System Instruction | RAG)          │
│  /register OCR CCCD → form → số thứ tự + chỉ đường          │
│  /admin    CRUD khoa/phòng + thống kê lượt tra cứu         │
└───────────────────────────┬────────────────────────────────┘
                            │  HTTP /api/*  (Vite proxy → 5057)
┌───────────────────────────▼──────────── Backend (Flask) ───┐
│  app.py        khai báo route, trả JSON                    │
│  repository.py đọc / tìm kiếm / CRUD / thống kê            │
│  ai.py         chatbot System Instruction (Gemini)        │
│  ai_rag.py     RAG: chunk → embedding → vector store → LLM │
│  ocr.py        OCR CCCD: tiền xử lý → PaddleOCR → trích xuất│
│  ── nguồn dữ liệu: hospital_data.py (20 khoa), text_utils.py│
└────────────────────────────────────────────────────────────┘
        AI ngoài: Google Gemini (chat + embedding) · PaddleOCR (OCR)
```

**Tech stack**

| Lớp | Công nghệ |
|-----|-----------|
| Frontend | Vue 3 + TypeScript + Vite, vue-router |
| Backend  | Flask, flask-cors, python-dotenv |
| AI | Google Gemini API (`google-genai`) · PaddleOCR (PaddlePaddle) |

**Cấu trúc thư mục**
```
project_hospital_pathways/
├── backend/
│   ├── hospital_data.py      # dữ liệu thuần 20 khoa/phòng
│   ├── text_utils.py         # tiện ích chuỗi (bỏ dấu, chuẩn hoá)
│   ├── repository.py         # đọc / tìm kiếm / CRUD / thống kê
│   ├── ai.py                 # chatbot System Instruction (/api/ai/chat)
│   ├── ai_rag.py             # chatbot RAG (/api/ai/rag/chat)
│   ├── data_hospital.md      # tài liệu kiến thức cho RAG (sinh từ hospital_data)
│   ├── ocr.py                # OCR CCCD + đăng ký (/api/ocr/*)
│   ├── app.py                # Flask app + route
│   ├── requirements.txt      # phụ thuộc lõi
│   ├── requirements-ocr.txt  # phụ thuộc OCR (PaddleOCR — tách riêng)
│   └── ocr_pipeline_colab.ipynb  # notebook thử từng bước OCR (Colab)
├── frontend/                 # Vue 3 + TS SPA
└── docs/                     # tài liệu giải thích từng bước (chỉ đọc ở local)
```

## 4. Hướng dẫn cài đặt & chạy

Cần **2 terminal**: một cho backend, một cho frontend.

### 4.1 Backend (Flask) — cổng 5057
```bash
cd backend
python3.13 -m venv .venv            # nên dùng Python 3.13 (xem lưu ý OCR)
source .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install -r requirements.txt     # lõi: Flask, google-genai…
pip install -r requirements-ocr.txt # (tuỳ chọn) bật OCR CCCD — PaddleOCR
cp .env.example .env                # rồi mở .env điền cấu hình (mục 4.3)
python app.py                       # http://localhost:5057
```

### 4.2 Frontend (Vue 3 + Vite) — cổng 5173
```bash
cd frontend
npm install
npm run dev                         # http://localhost:5173
```
Mở **http://localhost:5173**. Vite tự proxy `/api` sang backend, không cần cấu hình thêm.

### 4.3 Biến môi trường (`backend/.env`)

| Biến | Ý nghĩa | Mặc định |
|------|---------|----------|
| `PORT` | Cổng Flask (tránh AirPlay chiếm 5000 trên macOS) | `5057` |
| `GEMINI_API_KEY` | Khoá Gemini (chatbot + embedding RAG). Lấy ở Google AI Studio (key chuẩn bắt đầu `AIza`) | _(trống)_ |
| `GEMINI_MODEL` | Model sinh câu trả lời — **đặt model có thật**, ví dụ `gemini-2.0-flash` | `gemini-2.0-flash` |
| `GEMINI_EMBED_MODEL` | Model embedding cho RAG | `gemini-embedding-001` |
| `RAG_TOP_K` | Số đoạn truy hồi mỗi câu hỏi | `4` |
| `OCR_LANG` | Ngôn ngữ PaddleOCR | `vi` |

> **Lưu ý môi trường:**
> - **OCR (Hướng B)** cần **Python ≤ 3.13** vì PaddlePaddle chưa có bản cho Python 3.14.
>   Bỏ qua `requirements-ocr.txt` thì web vẫn chạy, chỉ phần *quét ảnh* báo cần cài — vẫn
>   **nhập tay** để đăng ký được.
> - Không có `GEMINI_API_KEY` thì các tính năng khác vẫn chạy, chỉ `/chat` báo cần khoá.

## 5. Tính năng

### Đã hoàn thành
- **Phần 1 — Web nền tảng:** trang chủ tìm kiếm (debounce, gõ có/không dấu, gõ liền
  `xquang`~`x-quang`), trang kết quả/chi tiết (tầng, phòng, giờ, mô tả), **sơ đồ tầng SVG
  highlight phòng**, **hướng dẫn đường đi từng bước**, giao diện **mobile-first**, xử lý đủ
  trạng thái loading/error/empty.
- **Phần 2 — Hướng A (Chatbot):** 2 chế độ *System Instruction* và **RAG** (chunk →
  embedding → vector store cosine → LLM), lưu lịch sử hội thoại trong phiên, RAG hiển thị
  **nguồn** bấm sang trang chi tiết.
- **Phần 2 — Hướng B (OCR CCCD):** pipeline tiền xử lý → PaddleOCR → hậu xử lý → trích xuất
  4 trường (số CCCD, họ tên, ngày sinh, địa chỉ) → form đăng ký → **gợi ý khoa theo lý do**
  → **số thứ tự ảo** + chỉ đường tới phòng chờ.
- **Điểm cộng — Admin dashboard:** `/admin` CRUD khoa/phòng + **thống kê lượt tra cứu**.
- **Điểm cộng — Kết hợp 2 hướng AI** trong cùng web, liên thông sang trang chi tiết/đường đi.

### Chưa làm được
- **Tối ưu đường đi bằng đồ thị** (BFS/Dijkstra/A\*) — chưa làm.
- **Lưu trữ bền:** dữ liệu khoa, số thứ tự, lượt xem nằm **trong bộ nhớ**, reset khi khởi
  động lại server (phiếu đăng ký mới chỉ demo, chưa lưu DB).
- **Đồng bộ tri thức RAG khi sửa/xoá khoa:** sửa/xoá ở admin **chưa cập nhật** lại index RAG
  nên chatbot có thể vẫn tư vấn khoa đã bị xoá.

## 6. Khó khăn gặp phải & cách giải quyết

1. **Tìm kiếm triệu chứng bị lẫn khoa.** "đau đầu" và "đau bụng" ban đầu ra gần như cùng kết
   quả (do mỗi từ khớp đều cộng điểm, mà "đau" có ở nhiều khoa; thêm nữa bỏ dấu thì "đau" và
   "đầu" đều thành "dau"). → **Sửa:** chuẩn hoá rồi **khớp nguyên cụm (chuỗi con)**, khớp ở
   tên xếp trước → mỗi triệu chứng ra đúng khoa.
2. **Khoá/Model Gemini.** Gặp `404` (tên model không tồn tại) và `403/429 limit:0` (project
   không có quyền model mới / hết quota free). → **Sửa:** cho chọn model qua `GEMINI_MODEL`,
   mặc định `gemini-2.0-flash`; **dịch lỗi sang tiếng Việt** thân thiện; thiếu khoá thì báo
   rõ thay vì sập.
3. **PaddlePaddle không cài được trên Python 3.14.** → **Sửa:** tách `requirements-ocr.txt`,
   khuyến nghị **Python 3.13**, **import lười + fallback** (thiếu thư viện vẫn nhập tay đăng
   ký được).
4. **Lỗi oneDNN của PaddleOCR trên CPU Colab** (`NotImplementedError ... onednn_instruction`).
   → **Sửa:** tắt oneDNN (`FLAGS_use_mkldnn=0` + `enable_mkldnn=False`) trong notebook.
5. **OCR lấy nhầm nhãn tiếng Anh.** Trên CCCD, nhãn "Họ và tên / Full name" đứng một dòng,
   **giá trị ở dòng dưới** → ban đầu trả về "Full name". → **Sửa:** hàm `value_below_label`
   lấy **dòng kế tiếp** (hoặc phần sau ':' nếu cùng dòng); rút gọn còn 4 trường cho dễ hiểu.

## 7. Nếu có thêm thời gian sẽ cải thiện

- **Tối ưu đường đi (điểm cộng còn thiếu):** mô hình hoá bệnh viện thành **đồ thị** (phòng/
  sảnh/thang máy = node) rồi chạy **Dijkstra/A\*** và highlight path trên SVG (dữ liệu đã có
  `pos`, `floor`, `LANDMARKS`).
- **Lưu trữ bền:** đưa khoa/phòng, số thứ tự, lượt xem và **phiếu đăng ký** xuống
  **SQLite/JSON** (chỉ cần sửa `repository.py`).
- **Đồng bộ RAG khi CRUD:** sửa/xoá khoa thì **rebuild index** để chatbot không tư vấn khoa
  đã xoá.
- **Cải tiến OCR cho tiếng Việt:** PaddleOCR còn yếu với tiếng Việt nên hiện **chủ yếu dựa
  cấu trúc CCCD ở bước hậu xử lý**; sẽ tinh chỉnh **tiền xử lý ảnh, Text Detection, Text
  Recognition** phù hợp loại ảnh (căn chỉnh/cắt vùng, nâng chất lượng ảnh).
- **RAG mạnh hơn:** thay vector store in-memory bằng **FAISS/Chroma**, lưu embedding ra đĩa.
- **Triển khai:** gunicorn, build frontend tĩnh, rate-limit API AI, thêm test + CI.

---

> Tài liệu giải thích chi tiết **từng bước build** nằm trong thư mục `docs/` (chỉ để đọc ở
> local). Notebook thử từng bước OCR: `backend/ocr_pipeline_colab.ipynb`.
