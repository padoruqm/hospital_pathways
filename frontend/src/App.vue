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
      <nav class="nav">
        <RouterLink to="/chat" class="nav-link">Trợ lý AI</RouterLink>
        <RouterLink to="/admin" class="nav-link">Admin</RouterLink>
      </nav>
    </div>
  </header>

  <main class="container app-main">
    <RouterView />
  </main>

  <footer class="app-footer">
    Hospital Wayfinding System · Hoang Minh Quang dz
  </footer>
</template>

<style scoped>
.app-main {
  min-height: calc(100vh - 130px);
  padding-top: 20px;
  padding-bottom: 20px;
}
.nav {
  display: flex;
  gap: 4px;
}
.nav :global(.router-link-active) {
  color: var(--color-primary-dark);
  background: var(--color-bg);
}
</style>
