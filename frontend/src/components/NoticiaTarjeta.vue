<script setup>
import { fechaLarga } from '../api'

defineProps({ noticia: { type: Object, required: true } })
</script>

<template>
  <RouterLink class="tarjeta noticia-tarjeta" :to="`/noticias/${noticia.id}`">
    <div class="tarjeta-foto">
      <img v-if="noticia.imagen" :src="noticia.imagen" :alt="noticia.titulo" loading="lazy" />
      <div v-else class="sin-foto">Trend</div>
      <span class="insignia">Noticia</span>
    </div>
    <div class="tarjeta-cuerpo">
      <time class="tarjeta-lugar" :datetime="noticia.creado">{{ fechaLarga(noticia.creado) }}</time>
      <h3>{{ noticia.titulo }}</h3>
      <p v-if="noticia.resumen" class="noticia-resumen">{{ noticia.resumen }}</p>
      <span class="noticia-leer">Leer más <span class="flecha" aria-hidden="true">→</span></span>
    </div>
  </RouterLink>
</template>
