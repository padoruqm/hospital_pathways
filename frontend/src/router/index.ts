import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      // Trang chi tiết một khoa: thông tin đầy đủ + hướng dẫn đường đi.
      // Lazy-load để tách chunk, trang chủ tải nhẹ hơn.
      path: '/department/:id',
      name: 'department',
      component: () => import('@/views/DepartmentDetailView.vue'),
    },
    {
      // Trang trợ lý AI (chatbot Gemini) — hỏi đáp triệu chứng để gợi ý khoa.
      path: '/chat',
      name: 'chat',
      component: () => import('@/views/ChatView.vue'),
    },
    {
      // Hướng B: đăng ký khám nhanh bằng OCR quét CCCD.
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterView.vue'),
    },
    {
      // Trang debug: xem trực quan từng bước của pipeline OCR.
      path: '/ocr-debug',
      name: 'ocr-debug',
      component: () => import('@/views/OcrDebugView.vue'),
    },
    {
      // Trang quản trị: thêm/sửa/xoá khoa phòng + thống kê lượt tra cứu.
      path: '/admin',
      name: 'admin',
      component: () => import('@/views/AdminView.vue'),
    },
  ],
  // Khi đổi trang, luôn cuộn lên đầu.
  scrollBehavior() {
    return { top: 0 }
  },
})

export default router
