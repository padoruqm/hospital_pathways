<script setup lang="ts">
import { ref, watch } from 'vue'

// Ô tìm kiếm tái sử dụng. Hỗ trợ v-model và phát sự kiện `search` đã được
// debounce (chờ người dùng ngừng gõ ~300ms) để tránh gọi API liên tục.
const props = defineProps<{
  modelValue: string
  placeholder?: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'search', value: string): void
}>()

const local = ref(props.modelValue)
let timer: ReturnType<typeof setTimeout> | undefined

watch(
  () => props.modelValue,
  (v) => {
    if (v !== local.value) local.value = v
  },
)

function onInput(value: string) {
  local.value = value
  emit('update:modelValue', value)
  if (timer) clearTimeout(timer)
  timer = setTimeout(() => emit('search', value.trim()), 300)
}

function clear() {
  onInput('')
}
</script>

<template>
  <div class="search-bar">
    <span class="icon" aria-hidden="true">🔍</span>
    <input
      :value="local"
      type="search"
      inputmode="search"
      :placeholder="placeholder ?? 'Tìm khoa, phòng hoặc dịch vụ…'"
      aria-label="Tìm kiếm khoa hoặc phòng"
      @input="onInput(($event.target as HTMLInputElement).value)"
    />
    <button v-if="local" class="clear" type="button" aria-label="Xoá" @click="clear">✕</button>
  </div>
</template>

<style scoped>
.search-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--color-surface);
  border: 2px solid var(--color-primary-light);
  border-radius: 999px;
  padding: 4px 14px;
  box-shadow: var(--shadow);
  transition: border-color 0.15s;
}
.search-bar:focus-within {
  border-color: var(--color-primary);
}
.icon {
  font-size: 1.05rem;
}
input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: 1.05rem;
  padding: 12px 0;
  color: var(--color-text);
}
.clear {
  border: none;
  background: var(--color-border);
  color: var(--color-muted);
  width: 26px;
  height: 26px;
  border-radius: 50%;
  font-size: 0.8rem;
  line-height: 1;
}
</style>
