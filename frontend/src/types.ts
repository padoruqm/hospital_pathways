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
