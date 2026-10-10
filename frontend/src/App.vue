<script setup>
import { useRoute } from 'vue-router'
import logoAlianza from './assets/logo-alianza.png'
import iconoTrend from './assets/logo-trend-icono.png'
import { ref, watch, onMounted } from 'vue'
import { api } from './api'
import { sesion, esAdmin, actualizarPerfil } from './sesion'
import Icono from './components/Icono.vue'

const route = useRoute()

// Menú desplegable en pantallas angostas: se cierra al navegar
const menuAbierto = ref(false)
watch(() => route.fullPath, () => (menuAbierto.value = false))

// El perfil (propietario, arrendatario...) puede haber cambiado desde el último ingreso
onMounted(() => {
  if (sesion.value) api.perfil().then(actualizarPerfil).catch(() => {})
})
</script>

<template>
  <header class="barra">
    <div class="barra-interior">
      <RouterLink class="marca" to="/">
        <img class="marca-logo" :src="iconoTrend" alt="" />
        <span class="marca-texto">
          <strong>Trend</strong>
          <small>Apartamentos</small>
        </span>
      </RouterLink>
      <nav class="menu" :class="{ abierto: menuAbierto }" aria-label="Principal">
        <RouterLink to="/" exact-active-class="" :class="{ activo: route.path === '/' && route.hash !== '#zonas' }">Inicio</RouterLink>
        <RouterLink :to="{ path: '/', hash: '#zonas' }" active-class="" exact-active-class="" :class="{ activo: route.hash === '#zonas' }">Zonas comunes</RouterLink>
        <RouterLink to="/venta-arriendo">Venta y arriendo</RouterLink>
        <RouterLink to="/noticias">Noticias</RouterLink>
        <RouterLink v-if="esAdmin" class="solo-movil-menu" to="/admin">Administrar</RouterLink>
      </nav>
      <div class="barra-acciones">
        <RouterLink v-if="esAdmin" class="boton secundario solo-escritorio" to="/admin">Administrar</RouterLink>
        <RouterLink v-if="!sesion" class="boton" to="/privado">Ingresar</RouterLink>
        <RouterLink v-else class="barra-perfil" to="/privado" :title="`Mi cuenta · ${sesion.nombre}`">
          <Icono nombre="person" />
        </RouterLink>
        <button type="button" class="boton-menu" :aria-expanded="menuAbierto" aria-label="Menú" @click="menuAbierto = !menuAbierto">
          <Icono :nombre="menuAbierto ? 'close' : 'menu'" />
        </button>
      </div>
    </div>
  </header>
  <main :class="{ ancho: route.meta.ancho }">
    <RouterView />
  </main>
  <footer class="pie-pagina">
    <div class="pie-columnas">
      <div class="pie-col">
        <RouterLink class="marca" to="/">
          <img class="marca-logo" :src="iconoTrend" alt="" />
          <span class="marca-texto"><strong>Trend</strong><small>Apartamentos</small></span>
        </RouterLink>
        <p>Conjunto residencial de apartamentos en Bogotá, con zonas comunes para el encuentro, el descanso y el día a día.</p>
        <span class="pie-chip">Bogotá · Colombia</span>
      </div>
      <div class="pie-col">
        <span class="pie-titulo">Administración</span>
        <img class="pie-alianza" :src="logoAlianza" alt="Alianza Grupo Inmobiliario S.A.S." />
        <p>Alianza Grupo Inmobiliario S.A.S.</p>
      </div>
      <div class="pie-col">
        <span class="pie-titulo">Residentes</span>
        <RouterLink to="/privado"><Icono nombre="lock" /> Zona privada</RouterLink>
        <RouterLink to="/noticias"><Icono nombre="campaign" /> Noticias y comunicados</RouterLink>
        <RouterLink :to="{ path: '/', hash: '#zonas' }"><Icono nombre="deck" /> Zonas comunes</RouterLink>
      </div>
      <div class="pie-col">
        <span class="pie-titulo">Accesos rápidos</span>
        <RouterLink to="/venta-arriendo"><Icono nombre="real_estate_agent" /> Apartamentos en venta y arriendo</RouterLink>
        <RouterLink :to="{ path: '/', hash: '#conjunto' }"><Icono nombre="apartment" /> El conjunto</RouterLink>
        <RouterLink to="/privado"><Icono nombre="person" /> {{ sesion ? 'Mi cuenta' : 'Ingresar' }}</RouterLink>
      </div>
    </div>
    <div class="pie-legal">
      <p>© {{ new Date().getFullYear() }} Trend Apartamentos. Todos los derechos reservados.</p>
    </div>
  </footer>
</template>
