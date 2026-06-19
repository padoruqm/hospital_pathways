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
  ],
  // Khi đổi trang, luôn cuộn lên đầu.
  scrollBehavior() {
    return { top: 0 }
  },
})

export default router
