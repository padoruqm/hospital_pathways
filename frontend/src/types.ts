// Các kiểu dữ liệu khớp với JSON do Flask backend trả về (xem backend/app.py).

/** Bản rút gọn của một khoa/phòng — dùng cho danh sách và kết quả tìm kiếm. */
export interface DepartmentSummary {
  id: string
  name: string
  category: string
  building: string
  buildingName: string
  floor: number
  room: string
  hours: string
  description: string
}

/** Toạ độ phòng trên sơ đồ tầng (hệ 0..100). */
export interface Pos {
  x: number
  y: number
}

/** Bản đầy đủ — thêm hướng dẫn đường đi và toạ độ sơ đồ. */
export interface DepartmentDetail extends DepartmentSummary {
  keywords: string[]
  symptoms: string[]
  pos: Pos
  directions: string[]
}

export interface SearchResponse {
  query: string
  count: number
  results: DepartmentSummary[]
}

export interface FloorRoom {
  id: string
  name: string
  room: string
  pos: Pos
}

export interface FloorGroup {
  building: string
  buildingName: string
  floor: number
  rooms: FloorRoom[]
}

/** Dữ liệu gửi lên khi tạo/sửa khoa ở trang quản trị. */
export interface DepartmentInput {
  name: string
  category: string
  building: string
  floor: number
  room: string
  hours: string
  description: string
  keywords: string[]
  symptoms: string[]
  directions: string[]
  pos?: Pos
}

/** Một dòng thống kê lượt xem theo khoa. */
export interface StatRow {
  id: string
  name: string
  views: number
}

/** Nguồn (khoa) mà RAG đã truy hồi — kèm id để liên kết sang trang chi tiết. */
export interface ChatSource {
  id: string
  name: string
}

/** Một lượt trong hội thoại với chatbot AI. */
export interface ChatMessage {
  role: 'user' | 'assistant'
  text: string
  /** (Chỉ chế độ RAG) các khoa đã được truy hồi làm ngữ cảnh. */
  sources?: ChatSource[]
}

export interface ChatReply {
  status: string
  reply: string
  /** (Chỉ chế độ RAG) các khoa/phòng đã truy hồi. */
  sources?: ChatSource[]
}

// ---- Hướng B: OCR CCCD + đăng ký khám ----
export interface OcrFields {
  id_number: string
  full_name: string
  dob: string
  sex: string
  nationality: string
  hometown: string
  residence: string
}

export interface ScanResult {
  status: string
  fields: OcrFields
  raw_lines: string[]
}

/** Một vùng chữ model nhận diện (để vẽ/đối chiếu ở trang debug). */
export interface OcrBox {
  index: number
  text: string
  score: number
  box: number[][]
}

/** Kết quả debug pipeline OCR — ảnh + kết quả từng bước. */
export interface OcrDebugResult {
  status: string
  preprocessed_image: string
  annotated_image: string
  boxes: OcrBox[]
  raw_lines: string[]
  cleaned_lines: string[]
  fields: OcrFields
}

export interface RegisterResult {
  status: string
  queue_number: string
  patient: { full_name: string; reason: string }
  department: {
    id: string
    name: string
    buildingName: string
    floor: number
    room: string
    hours: string
  }
  directions: string[]
}
