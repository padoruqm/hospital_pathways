<script setup lang="ts">
import type { DepartmentSummary } from '@/types'

// Thẻ hiển thị thông tin rút gọn một khoa/phòng: tên, nhóm, vị trí và giờ làm việc.
// Đây là component thuần hiển thị; việc điều hướng do nơi dùng quyết định.
defineProps<{
  dep: DepartmentSummary
}>()
</script>

<template>
  <RouterLink :to="`/department/${dep.id}`" class="card dep-card">
    <div class="dep-head">
      <h3 class="dep-name">{{ dep.name }}</h3>
      <span class="badge">{{ dep.category }}</span>
    </div>
    <p class="dep-desc">{{ dep.description }}</p>
    <div class="dep-meta">
      <span title="Vị trí">📍 {{ dep.buildingName.split('—')[0].trim() }} · Tầng {{ dep.floor }} · Phòng {{ dep.room }}</span>
      <span title="Giờ làm việc">🕒 {{ dep.hours }}</span>
    </div>
    <span class="go" aria-hidden="true">Xem đường đi →</span>
  </RouterLink>
</template>

<style scoped>
.dep-card {
  display: block;
  padding: 14px 16px;
  transition: border-color 0.15s, transform 0.05s;
}
.dep-card:hover {
  border-color: var(--color-primary);
}
.dep-card:active {
  transform: scale(0.995);
}
.go {
  display: inline-block;
  margin-top: 10px;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-primary-dark);
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
