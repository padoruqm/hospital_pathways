<script setup lang="ts">
// Khung ứng dụng: header cố định + vùng nội dung theo route + footer.
</script>

<template>
  <header class="app-header">
    <div class="container inner">
      <RouterLink to="/" class="brand">
        <span class="logo">🏥</span>
        <span>Điều hướng bệnh viện</span>
      </RouterLink>
      <RouterLink to="/admin" class="nav-link">Quản trị</RouterLink>
    </div>
  </header>

  <main class="container app-main">
    <RouterView />
  </main>

  <footer class="app-footer">
    Hospital Wayfinding System · Dữ liệu mô phỏng phục vụ demo
  </footer>
</template>

<style scoped>
.app-main {
  min-height: calc(100vh - 130px);
  padding-top: 20px;
  padding-bottom: 20px;
}
</style>
