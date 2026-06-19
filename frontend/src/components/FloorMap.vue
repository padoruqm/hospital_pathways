<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { getFloors } from '@/api/client'
import type { FloorGroup, FloorRoom } from '@/types'

// Sơ đồ tầng SVG **đơn giản, mang tính minh hoạ** (không dùng ảnh thật):
// vẽ các phòng cùng tầng/toà nhà thành các ô dọc một hành lang, tô sáng phòng đích.
// Toạ độ pos.x trong dữ liệu quyết định thứ tự trái→phải dọc hành lang.
const props = defineProps<{
  building: string
  floor: number
  highlightId: string
}>()

const floors = ref<FloorGroup[]>([])
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    floors.value = await getFloors()
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
})

// Các phòng trên đúng (toà nhà, tầng) của khoa đang xem, xếp theo vị trí trái→phải.
const rooms = computed<FloorRoom[]>(() => {
  const group = floors.value.find(
    (f) => f.building === props.building && f.floor === props.floor,
  )
  if (!group) return []
  return [...group.rooms].sort((a, b) => a.pos.x - b.pos.x)
})

// Bố trí đều các ô theo số lượng phòng để không bị chồng nhau.
const VIEW_W = 100
const VIEW_H = 46
function boxFor(index: number, total: number) {
  const w = Math.min(20, (VIEW_W - 8) / total - 2)
  const cx = ((index + 0.5) / total) * VIEW_W
  return { x: cx - w / 2, w }
}

function shortName(name: string) {
  return name.replace(/^Khoa |^Phòng |^Quầy /, '')
}
</script>

<template>
  <div class="floor-map">
    <div v-if="loading" class="state"><div class="spinner"></div>Đang tải sơ đồ…</div>
    <div v-else-if="error" class="state error">⚠️ {{ error }}</div>
    <div v-else-if="!rooms.length" class="state">Chưa có sơ đồ cho tầng này.</div>

    <template v-else>
      <svg :viewBox="`0 0 ${VIEW_W} ${VIEW_H}`" class="svg" role="img"
           :aria-label="`Sơ đồ tầng ${floor}`">
        <!-- Hành lang -->
        <rect x="2" y="28" :width="VIEW_W - 4" height="5" rx="2" class="corridor" />
        <text x="4" y="32" class="corridor-label">Hành lang</text>

        <!-- Các phòng -->
        <g v-for="(room, i) in rooms" :key="room.id">
          <rect
            :x="boxFor(i, rooms.length).x"
            y="6"
            :width="boxFor(i, rooms.length).w"
            height="16"
            rx="2"
            class="room"
            :class="{ active: room.id === highlightId }"
          />
          <!-- nối phòng xuống hành lang -->
          <line
            :x1="boxFor(i, rooms.length).x + boxFor(i, rooms.length).w / 2" y1="22"
            :x2="boxFor(i, rooms.length).x + boxFor(i, rooms.length).w / 2" y2="28"
            class="door" :class="{ active: room.id === highlightId }"
          />
          <text
            :x="boxFor(i, rooms.length).x + boxFor(i, rooms.length).w / 2" y="13"
            class="room-no" :class="{ active: room.id === highlightId }"
          >{{ room.room }}</text>
          <text
            :x="boxFor(i, rooms.length).x + boxFor(i, rooms.length).w / 2" y="18.5"
            class="room-name"
          >{{ shortName(room.name).slice(0, 10) }}</text>
        </g>

        <!-- Lối vào / thang máy -->
        <text :x="VIEW_W / 2" y="42" class="entrance">⬆ Thang máy / lối vào tầng</text>
      </svg>

      <p class="legend">
        <span class="dot active"></span> Phòng bạn cần đến &nbsp;·&nbsp;
        <span class="dot"></span> Phòng khác cùng tầng
      </p>
      <p class="note">Sơ đồ mang tính minh hoạ, vị trí phòng theo dữ liệu mock.</p>
    </template>
  </div>
</template>

<style scoped>
.svg {
  width: 100%;
  height: auto;
  background: var(--color-bg);
  border-radius: var(--radius);
  border: 1px solid var(--color-border);
}
.corridor {
  fill: #e2e8f0;
}
.corridor-label {
  font-size: 2.2px;
  fill: var(--color-muted);
}
.room {
  fill: #fff;
  stroke: var(--color-border);
  stroke-width: 0.4;
}
.room.active {
  fill: var(--color-primary-light);
  stroke: var(--color-primary);
  stroke-width: 0.8;
}
.door {
  stroke: var(--color-border);
  stroke-width: 0.5;
}
.door.active {
  stroke: var(--color-primary);
  stroke-width: 0.9;
}
.room-no {
  font-size: 3px;
  font-weight: 700;
  text-anchor: middle;
  fill: var(--color-text);
}
.room-no.active {
  fill: var(--color-primary-dark);
}
.room-name {
  font-size: 2.1px;
  text-anchor: middle;
  fill: var(--color-muted);
}
.entrance {
  font-size: 2.6px;
  text-anchor: middle;
  fill: var(--color-muted);
}
.legend {
  font-size: 0.8rem;
  color: var(--color-muted);
  margin: 10px 0 2px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
}
.dot {
  display: inline-block;
  width: 11px;
  height: 11px;
  border-radius: 3px;
  border: 1px solid var(--color-border);
  background: #fff;
  margin-right: 4px;
  vertical-align: middle;
}
.dot.active {
  background: var(--color-primary-light);
  border-color: var(--color-primary);
}
.note {
  font-size: 0.75rem;
  color: var(--color-muted);
  margin: 2px 0 0;
}
</style>
