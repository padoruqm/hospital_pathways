import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'

// Ở Giai đoạn 1 mới có trang chủ. Trang kết quả & chi tiết khoa sẽ được thêm ở bước sau.
const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
  ],
})

export default router
