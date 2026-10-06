<script setup>
import { useRoute } from 'vue-router'
import logoAlianza from './assets/logo-alianza.png'
import iconoTrend from './assets/logo-trend-icono.png'
import logoTrend from './assets/logo-trend-oscuro.png'
import { onMounted } from 'vue'
import { api } from './api'
import { sesion, esAdmin, actualizarPerfil } from './sesion'

const route = useRoute()

// El perfil (propietario, arrendatario...) puede haber cambiado desde el último ingreso
onMounted(() => {
  if (sesion.value) api.perfil().then(actualizarPerfil).catch(() => {})
})
</script>

<template>
  <header class="barra">
    <RouterLink class="marca" to="/">
      <img class="marca-logo" :src="iconoTrend" alt="" />
      <span class="marca-texto">
        <strong>Trend</strong>
        <small>Apartamentos</small>
      </span>
    </RouterLink>
    <nav class="menu">
      <RouterLink to="/">Inicio</RouterLink>
      <RouterLink to="/noticias">Noticias</RouterLink>
      <RouterLink to="/venta-arriendo">Venta y arriendo</RouterLink>
      <RouterLink v-if="esAdmin" to="/admin">Administrar</RouterLink>
      <RouterLink class="boton" to="/privado">
        {{ sesion ? 'Mi cuenta' : 'Ingresar' }} <span class="flecha" aria-hidden="true">→</span>
      </RouterLink>
    </nav>
  </header>
  <main :class="{ ancho: route.meta.ancho }">
    <RouterView />
  </main>
  <footer class="pie-pagina">
    <RouterLink class="marca" to="/">
      <img class="pie-logo" :src="logoTrend" alt="Trend Apartamentos" />
    </RouterLink>
    <div class="pie-admin">
      <span>Administración</span>
      <img class="marca-logo" :src="logoAlianza" alt="Alianza Grupo Inmobiliario S.A.S." />
    </div>
    <p>© {{ new Date().getFullYear() }} Trend Apartamentos</p>
  </footer>
</template>
