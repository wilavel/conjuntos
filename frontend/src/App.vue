<script setup>
import { useRoute } from 'vue-router'

const route = useRoute()
</script>

<template>
  <header class="barra">
    <RouterLink class="marca" to="/">
      <span class="marca-icono" aria-hidden="true"></span>
      <span class="marca-texto">
        <strong>Mis propiedades</strong>
        <small>Bogotá</small>
      </span>
    </RouterLink>
    <nav class="menu">
      <RouterLink to="/">Propiedades</RouterLink>
      <RouterLink to="/admin">Administrar</RouterLink>
      <RouterLink class="boton" to="/registro">Registrarse <span class="flecha" aria-hidden="true">→</span></RouterLink>
    </nav>
  </header>
  <main :class="{ ancho: route.meta.ancho }">
    <RouterView />
  </main>
  <footer class="pie-pagina">
    <RouterLink class="marca" to="/">
      <span class="marca-icono" aria-hidden="true"></span>
      <strong>Mis propiedades</strong>
    </RouterLink>
    <p>© {{ new Date().getFullYear() }} Mis propiedades. Inspirado en la materia del altiplano cundiboyacense.</p>
  </footer>
</template>
