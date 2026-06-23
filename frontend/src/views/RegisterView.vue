<script setup lang="ts">
import { reactive, ref } from 'vue'
import { registerVisit, scanCCCD } from '@/api/client'
import type { RegisterResult } from '@/types'

// Luồng Hướng B: (1) tải ảnh CCCD -> quét OCR -> (2) điền/sửa form + lý do khám
// -> (3) đăng ký: nhận số thứ tự ảo + khoa gợi ý + đường đi tới phòng chờ.

// --- Bước 1: ảnh + OCR ---
const file = ref<File | null>(null)
const previewUrl = ref('')
const scanning = ref(false)
const scanError = ref('')
const scanned = ref(false)

// --- Bước 2: form đăng ký ---
const form = reactive({
  full_name: '',
  dob: '',
  id_number: '',
  address: '',
  reason: '',
})

// --- Bước 3: kết quả ---
const registering = ref(false)
const registerError = ref('')
const result = ref<RegisterResult | null>(null)

function onFileChange(e: Event) {
  const f = (e.target as HTMLInputElement).files?.[0] || null
  file.value = f
  scanError.value = ''
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = f ? URL.createObjectURL(f) : ''
}

async function scan() {
  if (!file.value) return
  scanning.value = true
  scanError.value = ''
  try {
    const res = await scanCCCD(file.value)
    const f = res.fields
    form.full_name = f.full_name || form.full_name
    form.dob = f.dob || form.dob
    form.id_number = f.id_number || form.id_number
    form.address = f.address || form.address
    scanned.value = true
  } catch (e) {
    scanError.value = (e as Error).message
  } finally {
    scanning.value = false
  }
}

async function submit() {
  registerError.value = ''
  if (!form.full_name.trim()) {
    registerError.value = 'Vui lòng nhập họ tên.'
    return
  }
  if (!form.reason.trim()) {
    registerError.value = 'Vui lòng nhập lý do khám.'
    return
  }
  registering.value = true
  try {
    result.value = await registerVisit({ ...form })
  } catch (e) {
    registerError.value = (e as Error).message
  } finally {
    registering.value = false
  }
}

function reset() {
  result.value = null
  scanned.value = false
  file.value = null
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = ''
  Object.assign(form, { full_name: '', dob: '', id_number: '', address: '', reason: '' })
}
</script>

<template>
  <section class="reg">
    <header class="reg-head">
      <h1>Đăng ký khám</h1>
      <p>Quét CCCD để tự điền thông tin, hoặc nhập tay. Hệ thống sẽ gợi ý khoa và cấp số thứ tự.</p>
    </header>

    <!-- KẾT QUẢ -->
    <section v-if="result" class="card done">
      <div class="done-badge">✓ Đăng ký thành công</div>
      <p class="queue-label">Số thứ tự của bạn</p>
      <p class="queue-number">{{ result.queue_number }}</p>

      <div class="dep-box">
        <p class="dep-name">{{ result.department.name }}</p>
        <p class="dep-meta">
          {{ result.department.buildingName.split('—')[0].trim() }} ·
          Tầng {{ result.department.floor }} · Phòng {{ result.department.room }} ·
          🕒 {{ result.department.hours }}
        </p>
      </div>

      <div v-if="result.directions.length" class="dirs">
        <p class="dirs-title">🧭 Đường tới phòng chờ:</p>
        <ol>
          <li v-for="(s, i) in result.directions" :key="i">{{ s }}</li>
        </ol>
      </div>

      <div class="done-actions">
        <RouterLink :to="`/department/${result.department.id}`" class="btn primary">Xem sơ đồ &amp; đường đi</RouterLink>
        <button class="btn" @click="reset">Đăng ký người khác</button>
      </div>
    </section>

    <template v-else>
      <!-- BƯỚC 1: QUÉT CCCD -->
      <section class="card step">
        <h2 class="step-title">1 · Quét ảnh CCCD <span class="opt">(không bắt buộc)</span></h2>
        <input type="file" accept="image/*" capture="environment" @change="onFileChange" />
        <img v-if="previewUrl" :src="previewUrl" alt="Xem trước CCCD" class="preview" />
        <button v-if="file" class="btn primary" :disabled="scanning" @click="scan">
          {{ scanning ? 'Đang quét…' : 'Quét thông tin' }}
        </button>
        <p v-if="scanError" class="state error">⚠️ {{ scanError }}</p>
        <p v-else-if="scanned" class="ok-note">✓ Đã điền thông tin từ ảnh — kiểm tra lại bên dưới nhé.</p>
      </section>

      <!-- BƯỚC 2: FORM -->
      <section class="card step">
        <h2 class="step-title">2 · Thông tin đăng ký</h2>
        <div class="grid2">
          <label>Họ và tên *<input v-model="form.full_name" type="text" /></label>
          <label>Ngày sinh<input v-model="form.dob" type="text" placeholder="dd/mm/yyyy" /></label>
          <label>Số CCCD<input v-model="form.id_number" type="text" /></label>
          <label>Địa chỉ<input v-model="form.address" type="text" /></label>
        </div>
        <label class="full">Lý do khám / triệu chứng *
          <textarea v-model="form.reason" rows="2" placeholder="VD: tôi bị đau ngực, khó thở"></textarea>
        </label>
        <p v-if="registerError" class="state error">⚠️ {{ registerError }}</p>
        <button class="btn primary block" :disabled="registering" @click="submit">
          {{ registering ? 'Đang đăng ký…' : 'Đăng ký & lấy số thứ tự' }}
        </button>
      </section>
    </template>
  </section>
</template>

<style scoped>
.reg-head h1 {
  font-size: 1.4rem;
  margin: 0 0 2px;
}
.reg-head p {
  color: var(--color-muted);
  font-size: 0.9rem;
  margin: 0 0 16px;
}
.step {
  padding: 16px;
  margin-bottom: 14px;
}
.step-title {
  font-size: 1.05rem;
  margin: 0 0 12px;
}
.opt {
  font-size: 0.8rem;
  font-weight: 400;
  color: var(--color-muted);
}
.preview {
  display: block;
  max-width: 100%;
  max-height: 220px;
  border-radius: var(--radius);
  border: 1px solid var(--color-border);
  margin: 12px 0;
}
.ok-note {
  color: var(--color-primary-dark);
  font-size: 0.85rem;
  margin: 10px 0 0;
}
.grid2 {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}
@media (min-width: 560px) {
  .grid2 {
    grid-template-columns: 1fr 1fr;
  }
}
label {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 0.85rem;
  color: var(--color-muted);
  margin-bottom: 12px;
}
input,
textarea {
  font-family: inherit;
  font-size: 0.95rem;
  color: var(--color-text);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: 9px 11px;
  background: #fff;
}
input:focus,
textarea:focus {
  outline: none;
  border-color: var(--color-primary);
}
.btn {
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text);
  border-radius: var(--radius);
  padding: 10px 16px;
  font-size: 0.95rem;
}
.btn.primary {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: #fff;
  font-weight: 600;
}
.btn.block {
  width: 100%;
  margin-top: 4px;
}
.btn:disabled {
  opacity: 0.6;
}

/* Kết quả */
.done {
  padding: 22px 18px;
  text-align: center;
}
.done-badge {
  display: inline-block;
  background: var(--color-primary-light);
  color: var(--color-primary-dark);
  font-weight: 600;
  font-size: 0.85rem;
  padding: 4px 12px;
  border-radius: 999px;
}
.queue-label {
  color: var(--color-muted);
  margin: 16px 0 0;
  font-size: 0.9rem;
}
.queue-number {
  font-size: 2.6rem;
  font-weight: 800;
  color: var(--color-primary-dark);
  margin: 2px 0 14px;
  letter-spacing: 1px;
}
.dep-box {
  background: var(--color-bg);
  border-radius: var(--radius);
  padding: 12px;
}
.dep-name {
  font-weight: 700;
  margin: 0 0 4px;
}
.dep-meta {
  font-size: 0.85rem;
  color: var(--color-muted);
  margin: 0;
}
.dirs {
  text-align: left;
  margin-top: 14px;
}
.dirs-title {
  font-weight: 600;
  margin: 0 0 6px;
}
.dirs ol {
  margin: 0;
  padding-left: 20px;
  color: var(--color-text);
  font-size: 0.92rem;
}
.dirs li {
  padding: 2px 0;
}
.done-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
  margin-top: 18px;
}
</style>
