<script setup lang="ts">
import { ref } from 'vue'
import { debugOCR } from '@/api/client'
import type { OcrDebugResult } from '@/types'

// Trang xem trực quan TỪNG BƯỚC của pipeline OCR (phục vụ kiểm thử/giải thích).
const file = ref<File | null>(null)
const previewUrl = ref('')
const running = ref(false)
const error = ref('')
const result = ref<OcrDebugResult | null>(null)

const FIELD_LABELS: Record<string, string> = {
  id_number: 'Số CCCD',
  full_name: 'Họ và tên',
  dob: 'Ngày sinh',
  address: 'Địa chỉ',
}

function onFileChange(e: Event) {
  const f = (e.target as HTMLInputElement).files?.[0] || null
  file.value = f
  error.value = ''
  result.value = null
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = f ? URL.createObjectURL(f) : ''
}

async function run() {
  if (!file.value) return
  running.value = true
  error.value = ''
  try {
    result.value = await debugOCR(file.value)
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    running.value = false
  }
}
</script>

<template>
  <section class="dbg">
    <header class="dbg-head">
      <h1>OCR Debug — xem từng bước</h1>
      <p>Tải ảnh CCCD để xem: ảnh sau tiền xử lý → bounding box &amp; chữ nhận diện → hậu xử lý → trích xuất.</p>
      <RouterLink to="/register" class="back">← Về trang đăng ký</RouterLink>
    </header>

    <section class="card up">
      <input type="file" accept="image/*" @change="onFileChange" />
      <img v-if="previewUrl && !result" :src="previewUrl" alt="Ảnh gốc" class="thumb" />
      <button v-if="file" class="btn primary" :disabled="running" @click="run">
        {{ running ? 'Đang chạy pipeline…' : 'Chạy pipeline OCR' }}
      </button>
      <p v-if="error" class="state error">⚠️ {{ error }}</p>
    </section>

    <template v-if="result">
      <!-- BƯỚC 1 -->
      <section class="card step">
        <h2 class="step-title">1 · Tiền xử lý</h2>
        <p class="note">Ảnh đã xoay đúng chiều, thu nhỏ nếu quá lớn và tăng tương phản.</p>
        <img :src="result.preprocessed_image" alt="Ảnh sau tiền xử lý" class="stage-img" />
      </section>

      <!-- BƯỚC 2 -->
      <section class="card step">
        <h2 class="step-title">2 · Model — bounding box &amp; nhận diện</h2>
        <p class="note">PaddleOCR khoanh vùng chữ (đánh số) và đọc nội dung kèm độ tin cậy.</p>
        <img :src="result.annotated_image" alt="Ảnh có bounding box" class="stage-img" />
        <table class="boxes">
          <thead><tr><th>#</th><th>Chữ nhận diện</th><th>Độ tin cậy</th></tr></thead>
          <tbody>
            <tr v-for="b in result.boxes" :key="b.index">
              <td>{{ b.index }}</td>
              <td>{{ b.text }}</td>
              <td>{{ (b.score * 100).toFixed(1) }}%</td>
            </tr>
          </tbody>
        </table>
      </section>

      <!-- BƯỚC 3 -->
      <section class="card step">
        <h2 class="step-title">3 · Hậu xử lý</h2>
        <p class="note">Bỏ khoảng trắng thừa và dòng rỗng.</p>
        <div class="cols">
          <div>
            <h3 class="col-title">Thô (từ model)</h3>
            <ul class="lines"><li v-for="(l, i) in result.raw_lines" :key="i">{{ l }}</li></ul>
          </div>
          <div>
            <h3 class="col-title">Sau làm sạch</h3>
            <ul class="lines"><li v-for="(l, i) in result.cleaned_lines" :key="i">{{ l }}</li></ul>
          </div>
        </div>
      </section>

      <!-- BƯỚC 4 -->
      <section class="card step">
        <h2 class="step-title">4 · Trích xuất thông tin</h2>
        <table class="fields">
          <tbody>
            <tr v-for="(label, key) in FIELD_LABELS" :key="key">
              <td class="k">{{ label }}</td>
              <td class="v">{{ (result.fields as any)[key] || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </section>
    </template>
  </section>
</template>

<style scoped>
.dbg-head h1 {
  font-size: 1.4rem;
  margin: 0 0 2px;
}
.dbg-head p {
  color: var(--color-muted);
  font-size: 0.9rem;
  margin: 0 0 8px;
}
.back {
  color: var(--color-primary-dark);
  font-size: 0.9rem;
}
.up,
.step {
  padding: 16px;
  margin-bottom: 14px;
}
.step-title {
  font-size: 1.05rem;
  margin: 0 0 4px;
}
.note {
  color: var(--color-muted);
  font-size: 0.85rem;
  margin: 0 0 10px;
}
.thumb {
  display: block;
  max-height: 180px;
  max-width: 100%;
  margin: 12px 0;
  border-radius: var(--radius);
  border: 1px solid var(--color-border);
}
.stage-img {
  display: block;
  width: 100%;
  border-radius: var(--radius);
  border: 1px solid var(--color-border);
}
.btn {
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  border-radius: var(--radius);
  padding: 10px 16px;
  font-size: 0.95rem;
  margin-top: 12px;
}
.btn.primary {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: #fff;
  font-weight: 600;
}
.btn:disabled {
  opacity: 0.6;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.88rem;
  margin-top: 12px;
}
th,
td {
  text-align: left;
  padding: 8px;
  border-bottom: 1px solid var(--color-border);
  vertical-align: top;
}
th {
  color: var(--color-muted);
  font-size: 0.78rem;
}
.boxes td:last-child,
.boxes th:last-child {
  text-align: right;
  white-space: nowrap;
}
.cols {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
}
@media (min-width: 560px) {
  .cols {
    grid-template-columns: 1fr 1fr;
  }
}
.col-title {
  font-size: 0.85rem;
  margin: 0 0 6px;
  color: var(--color-primary-dark);
}
.lines {
  margin: 0;
  padding-left: 18px;
  font-size: 0.88rem;
}
.lines li {
  padding: 2px 0;
}
.fields .k {
  color: var(--color-muted);
  width: 40%;
}
.fields .v {
  font-weight: 600;
}
</style>
