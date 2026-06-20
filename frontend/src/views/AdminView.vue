<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import {
  createDepartment,
  deleteDepartment,
  getDepartment,
  getStats,
  listDepartments,
  updateDepartment,
} from "@/api/client";
import type { DepartmentInput, DepartmentSummary, StatRow } from "@/types";

// --- Danh sách + thống kê ---
const departments = ref<DepartmentSummary[]>([]);
const stats = ref<StatRow[]>([]);
const loading = ref(true);
const loadError = ref("");

// --- Form thêm/sửa ---
const editingId = ref<string | null>(null); // null = đang thêm mới
const saving = ref(false);
const formError = ref("");
const showForm = ref(false);

// Dùng text nhiều dòng cho danh sách (mỗi dòng 1 mục) cho dễ nhập.
const form = reactive({
  name: "",
  category: "",
  building: "A",
  floor: 1,
  room: "",
  hours: "",
  description: "",
  keywordsText: "",
  symptomsText: "",
  directionsText: "",
});

const categories = computed(() =>
  Array.from(new Set(departments.value.map((d) => d.category)))
);

const formTitle = computed(() =>
  editingId.value ? "Sửa khoa/phòng" : "Thêm khoa/phòng mới"
);

async function reload() {
  loading.value = true;
  loadError.value = "";
  try {
    [departments.value, stats.value] = await Promise.all([
      listDepartments(),
      getStats(),
    ]);
  } catch (e) {
    loadError.value = (e as Error).message;
  } finally {
    loading.value = false;
  }
}

onMounted(reload);

function resetForm() {
  editingId.value = null;
  Object.assign(form, {
    name: "",
    category: "",
    building: "A",
    floor: 1,
    room: "",
    hours: "",
    description: "",
    keywordsText: "",
    symptomsText: "",
    directionsText: "",
  });
  formError.value = "";
}

function startCreate() {
  resetForm();
  showForm.value = true;
}

async function startEdit(id: string) {
  formError.value = "";
  try {
    const dep = await getDepartment(id);
    editingId.value = dep.id;
    Object.assign(form, {
      name: dep.name,
      category: dep.category,
      building: dep.building,
      floor: dep.floor,
      room: dep.room,
      hours: dep.hours,
      description: dep.description,
      keywordsText: dep.keywords.join("\n"),
      symptomsText: dep.symptoms.join("\n"),
      directionsText: dep.directions.join("\n"),
    });
    showForm.value = true;
  } catch (e) {
    loadError.value = (e as Error).message;
  }
}

function linesOf(text: string): string[] {
  return text
    .split("\n")
    .map((s) => s.trim())
    .filter(Boolean);
}

async function save() {
  formError.value = "";
  saving.value = true;
  const payload: DepartmentInput = {
    name: form.name,
    category: form.category,
    building: form.building,
    floor: Number(form.floor),
    room: form.room,
    hours: form.hours,
    description: form.description,
    keywords: linesOf(form.keywordsText),
    symptoms: linesOf(form.symptomsText),
    directions: linesOf(form.directionsText),
  };
  try {
    if (editingId.value) await updateDepartment(editingId.value, payload);
    else await createDepartment(payload);
    showForm.value = false;
    resetForm();
    await reload();
  } catch (e) {
    formError.value = (e as Error).message;
  } finally {
    saving.value = false;
  }
}

async function remove(dep: DepartmentSummary) {
  if (!confirm(`Xoá "${dep.name}"? Hành động này không thể hoàn tác.`)) return;
  try {
    await deleteDepartment(dep.id);
    await reload();
  } catch (e) {
    loadError.value = (e as Error).message;
  }
}
</script>

<template>
  <div class="admin">
    <div class="admin-head">
      <h1>Quản trị khoa / phòng</h1>
      <button class="btn primary" @click="startCreate">+ Thêm mới</button>
    </div>
    <p class="hint">
      Thêm / sửa / xoá dữ liệu khoa, phòng. Thay đổi có hiệu lực ngay trong
      phiên chạy (sẽ reset khi khởi động lại server — dữ liệu mock lưu trong bộ
      nhớ).
    </p>

    <!-- Bảng quản trị (FORM) -->
    <section v-if="showForm" class="card form">
      <h2 class="form-title">{{ formTitle }}</h2>
      <div class="grid2">
        <label>Tên khoa/phòng *<input v-model="form.name" type="text" /></label>
        <label
          >Nhóm *
          <input v-model="form.category" type="text" list="cat-list" />
          <datalist id="cat-list">
            <option v-for="c in categories" :key="c" :value="c" />
          </datalist>
        </label>
        <label
          >Toà nhà *
          <select v-model="form.building">
            <option value="A">Nhà A</option>
            <option value="B">Nhà B</option>
          </select>
        </label>
        <label
          >Tầng *<input v-model.number="form.floor" type="number" min="1"
        /></label>
        <label>Phòng *<input v-model="form.room" type="text" /></label>
        <label
          >Giờ làm việc *<input
            v-model="form.hours"
            type="text"
            placeholder="07:00 – 16:30 (T2–T7)"
        /></label>
      </div>
      <label class="full"
        >Mô tả *<textarea v-model="form.description" rows="2"></textarea>
      </label>
      <div class="grid2">
        <label
          >Từ khoá (mỗi dòng 1 từ)<textarea
            v-model="form.keywordsText"
            rows="3"
          ></textarea>
        </label>
        <label
          >Triệu chứng (mỗi dòng 1)<textarea
            v-model="form.symptomsText"
            rows="3"
          ></textarea>
        </label>
      </div>
      <label class="full"
        >Hướng dẫn đường đi (mỗi dòng 1 bước)<textarea
          v-model="form.directionsText"
          rows="3"
        ></textarea>
      </label>

      <p v-if="formError" class="state error">⚠️ {{ formError }}</p>
      <div class="form-actions">
        <button class="btn" @click="showForm = false">Huỷ</button>
        <button class="btn primary" :disabled="saving" @click="save">
          {{ saving ? "Đang lưu…" : "Lưu" }}
        </button>
      </div>
    </section>

    <!-- DANH SÁCH -->
    <div v-if="loading" class="state">
      <div class="spinner"></div>
      Đang tải…
    </div>
    <div v-else-if="loadError" class="state error">⚠️ {{ loadError }}</div>
    <template v-else>
      <section class="card list">
        <table>
          <thead>
            <tr>
              <th>Tên</th>
              <th>Nhóm</th>
              <th class="hide-sm">Vị trí</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="d in departments" :key="d.id">
              <td>{{ d.name }}</td>
              <td>
                <span class="badge">{{ d.category }}</span>
              </td>
              <td class="hide-sm">
                Nhà {{ d.building }} · T{{ d.floor }} · P{{ d.room }}
              </td>
              <td class="row-actions">
                <button class="btn sm" @click="startEdit(d.id)">Sửa</button>
                <button class="btn sm danger" @click="remove(d)">Xoá</button>
              </td>
            </tr>
          </tbody>
        </table>
      </section>

      <!-- Bảng thống kê -->
      <section class="card stats">
        <h2 class="form-title">Lượt tra cứu theo khoa</h2>
        <ul>
          <li v-for="s in stats.slice(0, 8)" :key="s.id">
            <span>{{ s.name }}</span
            ><strong>{{ s.views }}</strong>
          </li>
        </ul>
        <p class="hint">
          Đếm số lần mở trang chi tiết khoa trong phiên chạy hiện tại.
        </p>
      </section>
    </template>
  </div>
</template>

<style scoped>
.admin-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.admin-head h1 {
  font-size: 1.4rem;
  margin: 0;
}
.hint {
  color: var(--color-muted);
  font-size: 0.85rem;
  margin: 6px 0 16px;
}
.btn {
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text);
  border-radius: var(--radius);
  padding: 8px 14px;
  font-size: 0.9rem;
}
.btn.sm {
  padding: 5px 10px;
  font-size: 0.82rem;
}
.btn.primary {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: #fff;
}
.btn.danger {
  color: var(--color-danger);
  border-color: #fecaca;
}
.btn:disabled {
  opacity: 0.6;
}

.form {
  padding: 16px;
  margin-bottom: 16px;
}
.form-title {
  font-size: 1.05rem;
  margin: 0 0 12px;
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
label.full {
  display: flex;
}
input,
select,
textarea {
  font-family: inherit;
  font-size: 0.95rem;
  color: var(--color-text);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: 8px 10px;
  background: #fff;
}
input:focus,
select:focus,
textarea:focus {
  outline: none;
  border-color: var(--color-primary);
}
textarea {
  resize: vertical;
}
.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 4px;
}

.list {
  padding: 4px 8px;
  margin-bottom: 16px;
  overflow-x: auto;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}
th,
td {
  text-align: left;
  padding: 10px 8px;
  border-bottom: 1px solid var(--color-border);
}
th {
  color: var(--color-muted);
  font-weight: 600;
  font-size: 0.8rem;
}
tr:last-child td {
  border-bottom: none;
}
.row-actions {
  display: flex;
  gap: 6px;
  justify-content: flex-end;
}

.stats {
  padding: 16px;
}
.stats ul {
  list-style: none;
  margin: 0;
  padding: 0;
}
.stats li {
  display: flex;
  justify-content: space-between;
  padding: 7px 0;
  border-bottom: 1px solid var(--color-border);
  font-size: 0.9rem;
}
.stats li:last-child {
  border-bottom: none;
}

@media (max-width: 480px) {
  .hide-sm {
    display: none;
  }
}
</style>
