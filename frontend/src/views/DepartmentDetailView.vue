<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getDepartment } from '@/api/client'
import type { DepartmentDetail } from '@/types'
import DirectionSteps from '@/components/DirectionSteps.vue'

const route = useRoute()
const dep = ref<DepartmentDetail | null>(null)
const loading = ref(true)
const error = ref('')

async function load(id: string) {
  loading.value = true
  error.value = ''
  dep.value = null
  try {
    dep.value = await getDepartment(id)
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
}

onMounted(() => load(route.params.id as string))
// Nếu điều hướng giữa hai khoa khác nhau mà không rời trang, tải lại dữ liệu.
watch(
  () => route.params.id,
  (id) => id && load(id as string),
)
</script>

<template>
  <RouterLink to="/" class="back">← Tìm kiếm khác</RouterLink>

  <div v-if="loading" class="state">
    <div class="spinner"></div>
    Đang tải thông tin…
  </div>
  <div v-else-if="error" class="state error">⚠️ {{ error }}</div>

  <article v-else-if="dep" class="detail">
    <header class="detail-head">
      <span class="badge">{{ dep.category }}</span>
      <h1>{{ dep.name }}</h1>
      <p class="desc">{{ dep.description }}</p>
    </header>

    <section class="card info">
      <div class="info-row"><span class="label">🏢 Toà nhà</span><span>{{ dep.buildingName }}</span></div>
      <div class="info-row"><span class="label">🛗 Tầng</span><span>Tầng {{ dep.floor }}</span></div>
      <div class="info-row"><span class="label">🚪 Phòng</span><span>{{ dep.room }}</span></div>
      <div class="info-row"><span class="label">🕒 Giờ làm việc</span><span>{{ dep.hours }}</span></div>
    </section>

    <section class="card block">
      <h2 class="block-title">🧭 Hướng dẫn đường đi</h2>
      <DirectionSteps :steps="dep.directions" :destination="`${dep.name} — Phòng ${dep.room}`" />
    </section>

    <section v-if="dep.keywords.length" class="card block">
      <h2 class="block-title">🔖 Từ khoá liên quan</h2>
      <div class="chips">
        <span v-for="k in dep.keywords" :key="k" class="chip">{{ k }}</span>
      </div>
    </section>
  </article>
</template>

<style scoped>
.back {
  display: inline-block;
  color: var(--color-primary-dark);
  font-size: 0.9rem;
  margin-bottom: 12px;
}
.detail-head {
  margin-bottom: 16px;
}
.detail-head h1 {
  font-size: 1.5rem;
  margin: 8px 0 6px;
}
.desc {
  color: var(--color-muted);
  margin: 0;
}
.info {
  padding: 6px 16px;
  margin-bottom: 14px;
}
.info-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid var(--color-border);
}
.info-row:last-child {
  border-bottom: none;
}
.info-row .label {
  color: var(--color-muted);
}
.block {
  padding: 16px;
  margin-bottom: 14px;
}
.block-title {
  font-size: 1.05rem;
  margin: 0 0 12px;
}
.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.chip {
  font-size: 0.82rem;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 999px;
  padding: 4px 10px;
  color: var(--color-muted);
}
</style>
