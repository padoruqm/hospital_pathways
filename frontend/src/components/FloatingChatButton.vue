<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

// Nút tròn nổi (Floating Action Button) mở trợ lý AI. Đặt `position: fixed` nên luôn
// theo màn hình khi cuộn. Ẩn khi đang ở chính trang chat cho đỡ thừa.
const route = useRoute()
const hidden = computed(() => route.name === 'chat')
</script>

<template>
  <RouterLink v-if="!hidden" to="/chat" class="fab" title="Trợ lý AI" aria-label="Mở trợ lý AI">
    <span class="icon" aria-hidden="true">💬</span>
  </RouterLink>
</template>

<style scoped>
.fab {
  position: fixed;
  right: 16px;
  bottom: 24px;
  z-index: 50;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary);
  color: #fff;
  box-shadow: 0 6px 18px rgba(2, 132, 199, 0.45);
  transition: transform 0.15s, box-shadow 0.15s, background 0.15s;
}
.fab:hover {
  background: var(--color-primary-dark);
  transform: translateY(-2px);
  box-shadow: 0 10px 24px rgba(2, 132, 199, 0.5);
}
.fab:active {
  transform: scale(0.95);
}
.icon {
  font-size: 1.6rem;
  line-height: 1;
}

/* Laptop/desktop: lùi vào trong một chút ở vùng dưới-phải, không sát góc; nút to hơn. */
@media (min-width: 768px) {
  .fab {
    right: 44px;
    bottom: 44px;
    width: 62px;
    height: 62px;
  }
  .fab .icon {
    font-size: 1.8rem;
  }
}
</style>
