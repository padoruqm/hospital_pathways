# 10 — Chatbot RAG (Retrieval-Augmented Generation)

Bản chatbot ở [09](09-ai-chatbot-gemini.md) nhồi **toàn bộ** khoa vào prompt. Bước này
thêm **RAG**: chỉ lấy vài đoạn tài liệu **liên quan nhất** tới câu hỏi rồi mới đưa cho
LLM. Cả hai bản cùng tồn tại — người dùng đổi qua lại bằng nút gạt trên trang `/chat`.

> Toàn bộ pipeline nằm trong [`backend/ai_rag.py`](../backend/ai_rag.py) với chú thích
> chi tiết từng bước ngay trong code. Tài liệu này tóm tắt bức tranh tổng thể.

## Vì sao cần RAG?

Nhồi hết dữ liệu vào prompt sẽ không mở rộng được: bệnh viện thật có hàng trăm khoa,
quy định, dịch vụ → prompt quá dài, tốn token, model dễ "lạc" và dễ bịa. RAG giải quyết
bằng cách **truy hồi (retrieve)** đúng phần cần thiết trước khi **sinh (generate)** câu trả lời.

## Pipeline 5 bước

```
              ┌─────────────────────── CHUẨN BỊ (1 lần, cache) ───────────────────────┐
data_hospital.md ─►(2)chunking─► 21 đoạn ─►(3)embedding─► 21 vector ─►(4)vector store
              └────────────────────────────────────────────────────────────────────────┘

Câu hỏi ─►(3)embedding─► vector câu hỏi ─►(4)so cosine, lấy TOP-K ─► K đoạn liên quan
                                                                          │
                              (5) prompt = K đoạn + câu hỏi ──► Gemini LLM ─► trả lời + nguồn
```

### (1) Tài liệu — `data_hospital.md`
Sinh tự động từ `hospital_data` (giữ **đầy đủ** mọi trường của 20 khoa) bằng hàm
`build_document()`. Tách tài liệu khỏi code để sau này có thể thay bằng tài liệu thật
(quy định, hướng dẫn…) mà không đụng pipeline. "Nguồn sự thật" vẫn là `hospital_data`,
`data_hospital.md` là bản **xuất ra** cho RAG dùng.

### (2) Chunking — cắt thành đoạn
Mỗi khoa = **một chunk** (cắt theo tiêu đề `## ...`). Lý do: mỗi khoa là một đơn vị
ngữ nghĩa trọn vẹn, độ dài vừa phải. Chunk **quá to** → nhiễu, kém chính xác; **quá nhỏ**
(vd từng dòng) → mất ngữ cảnh. Cắt theo mục là điểm cân bằng tự nhiên ở đây (21 chunk:
1 đoạn toà nhà + 20 khoa).

### (3) Embedding — văn bản → vector
Dùng model `gemini-embedding-001` biến mỗi đoạn thành **vector số** (~3072 chiều), sao cho
đoạn có nghĩa gần nhau thì vector gần nhau. Dùng `task_type` khác nhau cho tài liệu
(`RETRIEVAL_DOCUMENT`) và câu hỏi (`RETRIEVAL_QUERY`) — khuyến nghị của Google để tăng
chất lượng truy hồi.

### (4) Vector store — kho vector + tìm cosine
Với 21 chunk, lưu **trong bộ nhớ** (list) là quá đủ, không cần CSDL vector nặng. Đo độ
giống nhau bằng **cosine similarity** (góc giữa 2 vector, càng gần 1 càng giống). Lấy
`TOP_K = 4` đoạn điểm cao nhất.

> Khi dữ liệu lớn lên, chỉ cần thay phần này bằng **FAISS / Chroma / pgvector**; các bước
> còn lại giữ nguyên. Index được **build 1 lần rồi cache** trong bộ nhớ.

### (5) LLM — sinh câu trả lời có "grounding"
Ghép K đoạn liên quan vào System Instruction kèm yêu cầu **chỉ dựa trên ngữ cảnh, không
bịa**. Gemini (`gemini-2.0-flash`) soạn câu trả lời; API trả về kèm `sources` = danh sách
`{id, name}` các khoa đã truy hồi để người dùng thấy "AI dựa vào đâu".

**Liên thông sang trang chi tiết/đường đi:** vì mỗi nguồn có `id`, frontend hiển thị chúng
thành **liên kết** tới `/department/{id}` — bấm vào là sang đúng trang chi tiết khoa (có
sơ đồ tầng highlight + hướng dẫn đường đi từng bước). Nhờ vậy chatbot không phải widget rời
mà nối thẳng vào luồng điều hướng chính của web.

## Kết quả truy hồi thực tế (đã test)

Truy vấn *"tôi bị đau ngực, khó thở"* → cosine xếp hạng:

```
0.712  Khoa Tim mạch
0.698  Khoa Cấp cứu
0.670  Khoa Nội tổng quát
0.653  Khoa Nội thần kinh
```

→ Đúng các khoa cần thiết, **không cần khớp từ khoá chính xác** (đây là điểm mạnh của
embedding so với tìm kiếm chuỗi con ở `repository.search`).

## API & tích hợp

| Method & path | Chức năng |
|---------------|-----------|
| `POST /api/ai/rag/chat` | `{message, history}` → `{reply, sources}` |
| `GET  /api/ai/rag/status` | Tình trạng index (đã build chưa, số chunk, model…) |

- Đăng ký Blueprint trong [`app.py`](../backend/app.py): `url_prefix="/api/ai/rag"`.
- Frontend [`ChatView.vue`](../frontend/src/views/ChatView.vue) có **nút gạt** chọn
  *RAG (tra tài liệu)* hoặc *Hỏi nhanh*; chế độ RAG hiển thị dòng **"📚 Xem chi tiết &
  đường đi: …"** với mỗi khoa là một **liên kết** sang trang chi tiết (`/department/{id}`).

## Cấu hình (backend/.env)

```bash
GEMINI_API_KEY=...                      # bắt buộc (cả embedding lẫn sinh câu trả lời đều cần)
GEMINI_MODEL=gemini-2.0-flash           # model sinh câu trả lời (tuỳ chọn)
GEMINI_EMBED_MODEL=gemini-embedding-001 # model embedding (tuỳ chọn)
RAG_TOP_K=4                             # số đoạn truy hồi (tuỳ chọn)
```

> Lưu ý quota: RAG gọi Gemini **2 nhóm** quota khác nhau (embedding + sinh nội dung). Nếu
> khoá hết quota phần sinh nội dung, bước truy hồi vẫn chạy nhưng câu trả lời sẽ báo lỗi
> quota — hãy dùng khoá có hạn mức hoặc bật billing.
