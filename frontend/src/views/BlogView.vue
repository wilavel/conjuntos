<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'
import NoticiaTarjeta from '../components/NoticiaTarjeta.vue'

const noticias = ref([])
const cargando = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    noticias.value = await api.noticias()
  } catch (e) {
    error.value = e.message
  } finally {
    cargando.value = false
  }
})
</script>

<template>
  <div class="seccion-cabeza blog-cabeza">
    <div>
      <span class="rotulo">Blog</span>
      <h2>Noticias del conjunto</h2>
    </div>
    <p class="zonas-nota">Comunicados de la administración, novedades y eventos de Trend Apartamentos.</p>
  </div>

  <p v-if="error" class="error">{{ error }}</p>
  <p v-else-if="cargando">Cargando…</p>
  <div v-else-if="!noticias.length" class="vacio">Todavía no hay noticias publicadas.</div>

  <div class="tarjetas">
    <NoticiaTarjeta v-for="n in noticias" :key="n.id" :noticia="n" />
  </div>
</template>
