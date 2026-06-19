<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import SearchBar from '@/components/SearchBar.vue'
import DepartmentCard from '@/components/DepartmentCard.vue'
import { listDepartments, searchDepartments } from '@/api/client'
import type { DepartmentSummary } from '@/types'

// --- Trạng thái tìm kiếm ---
const query = ref('')
const results = ref<DepartmentSummary[]>([])
const searching = ref(false)
const searchError = ref('')
const hasSearched = ref(false)

// --- Danh sách tất cả khoa (hiển thị mặc định khi chưa tìm) ---
const all = ref<DepartmentSummary[]>([])
const loadingAll = ref(true)
const loadError = ref('')

// Gom các khoa theo nhóm (category) để duyệt cho dễ.
const grouped = computed(() => {
  const map = new Map<string, DepartmentSummary[]>()
  for (const d of all.value) {
    if (!map.has(d.category)) map.set(d.category, [])
    map.get(d.category)!.push(d)
  }
  return Array.from(map.entries()).map(([category, items]) => ({ category, items }))
})

onMounted(async () => {
  try {
    all.value = await listDepartments()
  } catch (e) {
    loadError.value = (e as Error).message
  } finally {
    loadingAll.value = false
  }
})

async function onSearch(q: string) {
  if (!q) {
    // Quay lại trạng thái duyệt tất cả khi xoá ô tìm kiếm
    hasSearched.value = false
    results.value = []
    searchError.value = ''
    return
  }
  searching.value = true
  searchError.value = ''
  hasSearched.value = true
  try {
    const res = await searchDepartments(q)
    results.value = res.results
  } catch (e) {
    searchError.value = (e as Error).message
  } finally {
    searching.value = false
  }
}
</script>

<template>
  <section class="hero">
    <h1>Bạn cần tìm khoa hay phòng nào?</h1>
    <p class="sub">Tra cứu khoa, phòng, dịch vụ — xem tầng, số phòng và đường đi.</p>
    <SearchBar v-model="query" @search="onSearch" />
  </section>

  <!-- KẾT QUẢ TÌM KIẾM -->
  <section v-if="hasSearched" class="results">
    <div v-if="searching" class="state">
      <div class="spinner"></div>
      Đang tìm…
    </div>
    <div v-else-if="searchError" class="state error">⚠️ {{ searchError }}</div>
    <template v-else>
      <p class="result-count">
        Tìm thấy <strong>{{ results.length }}</strong> kết quả cho "{{ query }}"
      </p>
      <div v-if="results.length" class="grid">
        <DepartmentCard v-for="d in results" :key="d.id" :dep="d" />
      </div>
      <div v-else class="state">
        Không tìm thấy khoa/phòng phù hợp. Thử từ khoá khác như "tim", "x-quang", "xét nghiệm".
      </div>
    </template>
  </section>

  <!-- DUYỆT TẤT CẢ (trạng thái mặc định) -->
  <section v-else class="browse">
    <h2 class="section-title">Tất cả khoa &amp; phòng</h2>
    <div v-if="loadingAll" class="state">
      <div class="spinner"></div>
      Đang tải danh sách…
    </div>
    <div v-else-if="loadError" class="state error">⚠️ {{ loadError }}</div>
    <template v-else>
      <div v-for="group in grouped" :key="group.category" class="group">
        <h3 class="group-title">{{ group.category }}</h3>
        <div class="grid">
          <DepartmentCard v-for="d in group.items" :key="d.id" :dep="d" />
        </div>
      </div>
    </template>
  </section>
</template>

<style scoped>
.hero {
  text-align: center;
  padding: 18px 0 24px;
}
.hero h1 {
  font-size: 1.5rem;
  margin: 0 0 6px;
}
.hero .sub {
  color: var(--color-muted);
  margin: 0 0 18px;
  font-size: 0.95rem;
}
.section-title {
  font-size: 1.1rem;
  margin: 8px 0 14px;
}
.result-count {
  color: var(--color-muted);
  font-size: 0.9rem;
  margin: 4px 0 14px;
}
.group {
  margin-bottom: 22px;
}
.group-title {
  font-size: 0.95rem;
  color: var(--color-primary-dark);
  margin: 0 0 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--color-border);
}
.grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}
/* Màn hình rộng: 2 cột cho dễ duyệt */
@media (min-width: 560px) {
  .grid {
    grid-template-columns: 1fr 1fr;
  }
  .hero h1 {
    font-size: 1.8rem;
  }
}
</style>
