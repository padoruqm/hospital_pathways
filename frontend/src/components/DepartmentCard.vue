<script setup lang="ts">
import type { DepartmentSummary } from '@/types'

// Thẻ hiển thị thông tin rút gọn một khoa/phòng: tên, nhóm, vị trí và giờ làm việc.
// Đây là component thuần hiển thị; việc điều hướng do nơi dùng quyết định.
defineProps<{
  dep: DepartmentSummary
}>()
</script>

<template>
  <article class="card dep-card">
    <div class="dep-head">
      <h3 class="dep-name">{{ dep.name }}</h3>
      <span class="badge">{{ dep.category }}</span>
    </div>
    <p class="dep-desc">{{ dep.description }}</p>
    <div class="dep-meta">
      <span title="Vị trí">📍 {{ dep.buildingName.split('—')[0].trim() }} · Tầng {{ dep.floor }} · Phòng {{ dep.room }}</span>
      <span title="Giờ làm việc">🕒 {{ dep.hours }}</span>
    </div>
  </article>
</template>

<style scoped>
.dep-card {
  padding: 14px 16px;
}
.dep-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}
.dep-name {
  margin: 0;
  font-size: 1.05rem;
  color: var(--color-primary-dark);
}
.dep-desc {
  margin: 8px 0 10px;
  color: var(--color-muted);
  font-size: 0.92rem;
}
.dep-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 0.85rem;
  color: var(--color-text);
}
</style>
