<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'
import { iconoZona } from '../zonas'
import AdminNav from '../components/AdminNav.vue'

const zonas = ref([])
const cargando = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    zonas.value = await api.zonas()
  } catch (e) {
    error.value = e.message
  } finally {
    cargando.value = false
  }
})
</script>

<template>
  <AdminNav />
  <div class="encabezado titulo-admin">
    <h1>Zonas comunes</h1>
    <RouterLink class="boton" to="/admin/zonas/nueva">Nueva zona</RouterLink>
  </div>

  <p v-if="error" class="error">{{ error }}</p>
  <p v-else-if="cargando">Cargando…</p>
  <p v-else-if="!zonas.length" class="vacio">Aún no hay zonas comunes.</p>

  <div class="lista">
    <RouterLink v-for="z in zonas" :key="z.id" class="fila" :to="`/admin/zonas/${z.id}`">
      <img v-if="z.fotos.length" :src="z.fotos[0].url" alt="" />
      <div v-else class="sin-foto zona-sin-foto" v-html="iconoZona(z.icono)"></div>
      <div class="datos">
        <strong>{{ z.nombre }}</strong>
        <span>{{ z.resumen }}</span>
        <span>{{ z.fotos.length }} {{ z.fotos.length === 1 ? 'foto' : 'fotos' }}<template v-if="z.horario"> · {{ z.horario }}</template></span>
      </div>
      <span class="estado publicado">{{ z.slug }}</span>
    </RouterLink>
  </div>
</template>
