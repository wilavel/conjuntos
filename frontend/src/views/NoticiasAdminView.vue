<script setup>
import AdminNav from '../components/AdminNav.vue'
import { ref, onMounted } from 'vue'
import { api, fechaLarga } from '../api'

const noticias = ref([])
const cargando = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    noticias.value = await api.noticias({ todas: true })
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
    <h1>Administrar noticias</h1>
    <RouterLink class="boton" to="/admin/noticias/nueva">Nueva noticia</RouterLink>
  </div>

  <p v-if="error" class="error">{{ error }}</p>
  <p v-else-if="cargando">Cargando…</p>
  <p v-else-if="!noticias.length" class="vacio">
    Aún no hay noticias. <RouterLink to="/admin/noticias/nueva">Escribe la primera</RouterLink>.
  </p>

  <div class="lista">
    <RouterLink v-for="n in noticias" :key="n.id" class="fila" :to="`/admin/noticias/${n.id}/editar`">
      <img v-if="n.imagen" :src="n.imagen" alt="" />
      <div v-else class="sin-foto">Sin foto</div>
      <div class="datos">
        <strong>{{ n.titulo }}</strong>
        <span>{{ fechaLarga(n.creado) }}</span>
        <span v-if="n.resumen">{{ n.resumen }}</span>
      </div>
      <span class="estado" :class="n.publicada ? 'publicado' : 'borrador'">
        {{ n.publicada ? 'publicada' : 'borrador' }}
      </span>
    </RouterLink>
  </div>
</template>
