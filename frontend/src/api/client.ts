// Lớp gọi API tập trung. Mọi component dùng các hàm ở đây thay vì gọi fetch rải rác,
// để dễ xử lý lỗi thống nhất và đổi endpoint một chỗ.

import type {
  DepartmentDetail,
  DepartmentSummary,
  FloorGroup,
  SearchResponse,
} from '@/types'

const BASE = '/api' // được Vite proxy sang Flask ở môi trường dev

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(BASE + path)
  if (!res.ok) {
    // Cố đọc message lỗi từ backend nếu có
    let message = `Lỗi ${res.status}`
    try {
      const body = await res.json()
      if (body?.message) message = body.message
    } catch {
      /* bỏ qua, dùng message mặc định */
    }
    throw new Error(message)
  }
  return res.json() as Promise<T>
}

export function listDepartments(): Promise<DepartmentSummary[]> {
  return getJson<DepartmentSummary[]>('/departments')
}

export function getDepartment(id: string): Promise<DepartmentDetail> {
  return getJson<DepartmentDetail>(`/departments/${id}`)
}

export function searchDepartments(query: string): Promise<SearchResponse> {
  return getJson<SearchResponse>(`/search?q=${encodeURIComponent(query)}`)
}

export function getFloors(): Promise<FloorGroup[]> {
  return getJson<FloorGroup[]>('/floors')
}
