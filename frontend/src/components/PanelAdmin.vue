<script setup>
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { sesion, esSuperadmin, cerrarSesion } from '../sesion'
import iconoTrend from '../assets/logo-trend-icono.png'
import Icono from './Icono.vue'

// Diseño propio del panel de administración: barra lateral + contenido.
// No muestra la cabecera ni el pie de la página pública.
const route = useRoute()
const router = useRouter()

const SECCIONES = [
  { ruta: '/admin', icono: 'dashboard', texto: 'Resumen', exacta: true },
  { ruta: '/admin/apartamentos', icono: 'apartment', texto: 'Apartamentos' },
  { ruta: '/admin/propietarios', icono: 'contacts', texto: 'Directorio' },
  { ruta: '/admin/parqueaderos', icono: 'local_parking', texto: 'Parqueaderos' },
  { ruta: '/admin/sorteos', icono: 'casino', texto: 'Sorteos' },
  { ruta: '/admin/zonas', icono: 'deck', texto: 'Zonas comunes' },
  { ruta: '/admin/noticias', icono: 'campaign', texto: 'Noticias' },
  { ruta: '/admin/usuarios', icono: 'group', texto: 'Usuarios' },
]
// Los avisos de venta y arriendo se manejan desde la ficha de cada apartamento
const activa = (s) =>
  s.exacta ? route.path === s.ruta : route.path.startsWith(s.ruta) || (s.ruta === '/admin/apartamentos' && route.path.startsWith('/admin/avisos'))

const abierto = ref(false) // barra lateral en móvil
watch(() => route.fullPath, () => (abierto.value = false))

function salir() {
  cerrarSesion()
  router.push('/')
}
</script>

<template>
  <div class="panel-admin">
    <aside class="panel-lateral" :class="{ abierto }">
      <RouterLink class="panel-marca" to="/admin">
        <img :src="iconoTrend" alt="" />
        <span><strong>Trend</strong><small>Administración</small></span>
      </RouterLink>
      <nav class="panel-menu" aria-label="Administración">
        <RouterLink v-for="s in SECCIONES" :key="s.ruta" :to="s.ruta" :class="{ activo: activa(s) }">
          <Icono :nombre="s.icono" /> {{ s.texto }}
        </RouterLink>
      </nav>
      <div class="panel-pie">
        <RouterLink to="/" class="panel-sitio"><Icono nombre="open_in_new" /> Ver sitio público</RouterLink>
        <div class="panel-usuario">
          <span class="panel-avatar"><Icono nombre="person" /></span>
          <span>
            <strong>{{ sesion?.nombre }}</strong>
            <small>{{ esSuperadmin ? 'Super admin' : 'Administrador' }}</small>
          </span>
        </div>
        <button type="button" class="panel-salir" @click="salir"><Icono nombre="logout" /> Cerrar sesión</button>
      </div>
    </aside>

    <div class="panel-principal">
      <header class="panel-barra">
        <button type="button" class="boton-menu panel-boton-menu" :aria-expanded="abierto" aria-label="Menú" @click="abierto = !abierto">
          <Icono :nombre="abierto ? 'close' : 'menu'" />
        </button>
        <span class="panel-titulo"><Icono nombre="admin_panel_settings" /> Panel de administración</span>
        <RouterLink to="/" class="enlace panel-sitio-barra"><Icono nombre="open_in_new" /> Ver sitio</RouterLink>
      </header>
      <main class="panel-contenido">
        <slot />
      </main>
    </div>
    <div v-if="abierto" class="panel-sombra" @click="abierto = false"></div>
  </div>
</template>
