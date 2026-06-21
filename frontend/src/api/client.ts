// Lớp gọi API tập trung. Mọi component dùng các hàm ở đây thay vì gọi fetch rải rác,
// để dễ xử lý lỗi thống nhất và đổi endpoint một chỗ.

import type {
  ChatMessage,
  ChatReply,
  DepartmentDetail,
  DepartmentInput,
  DepartmentSummary,
  FloorGroup,
  SearchResponse,
  StatRow,
} from '@/types'

const BASE = '/api' // được Vite proxy sang Flask ở môi trường dev

// Hàm gọi chung cho mọi method. Đọc message lỗi (kể cả lỗi validation nhiều dòng)
// từ backend để hiển thị cho người dùng.
async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    let message = `Lỗi ${res.status}`
    try {
      const body = await res.json()
      if (Array.isArray(body?.messages)) message = body.messages.join('; ')
      else if (body?.message) message = body.message
    } catch {
      /* bỏ qua, dùng message mặc định */
    }
    throw new Error(message)
  }
  return res.json() as Promise<T>
}

function getJson<T>(path: string): Promise<T> {
  return request<T>(path)
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

// ---- Quản trị (CRUD) ----
export function createDepartment(input: DepartmentInput): Promise<DepartmentDetail> {
  return request<DepartmentDetail>('/departments', {
    method: 'POST',
    body: JSON.stringify(input),
  })
}

export function updateDepartment(id: string, input: DepartmentInput): Promise<DepartmentDetail> {
  return request<DepartmentDetail>(`/departments/${id}`, {
    method: 'PUT',
    body: JSON.stringify(input),
  })
}

export function deleteDepartment(id: string): Promise<{ deleted: string }> {
  return request<{ deleted: string }>(`/departments/${id}`, { method: 'DELETE' })
}

export function getStats(): Promise<StatRow[]> {
  return getJson<StatRow[]>('/stats')
}

// ---- Chatbot AI (Gemini) ----
// Chế độ "System Instruction": nhồi toàn bộ khoa vào prompt.
export function chatWithAI(message: string, history: ChatMessage[]): Promise<ChatReply> {
  return request<ChatReply>('/ai/chat', {
    method: 'POST',
    body: JSON.stringify({ message, history }),
  })
}

// Chế độ "RAG": truy hồi vài khoa liên quan từ tài liệu rồi mới hỏi LLM (kèm sources).
export function chatWithRAG(message: string, history: ChatMessage[]): Promise<ChatReply> {
  return request<ChatReply>('/ai/rag/chat', {
    method: 'POST',
    body: JSON.stringify({ message, history }),
  })
}
