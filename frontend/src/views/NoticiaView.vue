<script setup>
import { ref, computed, onMounted } from 'vue'
import { api, fechaLarga } from '../api'

const props = defineProps({ id: String })

const noticia = ref(null)
const error = ref('')

onMounted(async () => {
  try {
    noticia.value = await api.noticia(props.id)
  } catch (e) {
    error.value = e.message
  }
})

// El contenido es texto plano: cada línea en blanco separa un párrafo
const parrafos = computed(() =>
  (noticia.value?.contenido || '').split(/\n\s*\n/).map((t) => t.trim()).filter(Boolean),
)
</script>

<template>
  <p v-if="error" class="error">{{ error }}</p>
  <p v-else-if="!noticia">Cargando…</p>
  <article v-else class="articulo">
    <RouterLink class="articulo-volver" to="/noticias">← Todas las noticias</RouterLink>
    <span class="rotulo">
      <time :datetime="noticia.creado">{{ fechaLarga(noticia.creado) }}</time>
      <template v-if="!noticia.publicada"> · Borrador</template>
    </span>
    <h1>{{ noticia.titulo }}</h1>
    <p v-if="noticia.resumen" class="articulo-resumen">{{ noticia.resumen }}</p>
    <img v-if="noticia.imagen" class="articulo-imagen" :src="noticia.imagen" :alt="noticia.titulo" />
    <div class="articulo-cuerpo">
      <p v-for="(texto, i) in parrafos" :key="i">{{ texto }}</p>
    </div>
  </article>
</template>
