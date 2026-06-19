<script setup lang="ts">
// Hiển thị hướng dẫn đường đi dạng từng bước được đánh số.
// Bước cuối được tô đậm như đích đến để bệnh nhân biết mình đã tới nơi.
defineProps<{
  steps: string[]
  destination: string
}>()
</script>

<template>
  <ol class="steps">
    <li v-for="(step, i) in steps" :key="i" class="step">
      <span class="num">{{ i + 1 }}</span>
      <span class="text">{{ step }}</span>
    </li>
    <li class="step arrive">
      <span class="num">🏁</span>
      <span class="text"><strong>Đến nơi:</strong> {{ destination }}</span>
    </li>
  </ol>
</template>

<style scoped>
.steps {
  list-style: none;
  margin: 0;
  padding: 0;
}
.step {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 10px 0;
  position: relative;
}
/* Đường nối dọc giữa các bước */
.step:not(:last-child)::after {
  content: '';
  position: absolute;
  left: 13px;
  top: 36px;
  bottom: -4px;
  width: 2px;
  background: var(--color-primary-light);
}
.num {
  flex: 0 0 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--color-primary);
  color: #fff;
  font-size: 0.85rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
}
.arrive .num {
  background: var(--color-primary-dark);
}
.text {
  padding-top: 3px;
}
</style>
