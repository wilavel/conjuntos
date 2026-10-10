<script setup>
import { fechaLarga } from '../api'
import Icono from './Icono.vue'

defineProps({ noticia: { type: Object, required: true } })
</script>

<template>
  <RouterLink class="tarjeta noticia-tarjeta" :to="`/noticias/${noticia.id}`">
    <div class="tarjeta-foto">
      <template v-if="noticia.imagen">
        <div class="tarjeta-foto-fondo" :style="{ backgroundImage: `url(${noticia.imagen})` }" aria-hidden="true"></div>
        <img :src="noticia.imagen" :alt="noticia.titulo" loading="lazy" />
      </template>
      <div v-else class="sin-foto"><Icono nombre="campaign" /></div>
      <span class="insignia insignia-negocio">Noticia</span>
    </div>
    <div class="tarjeta-cuerpo">
      <time class="tarjeta-fecha" :datetime="noticia.creado"><Icono nombre="calendar_today" /> {{ fechaLarga(noticia.creado) }}</time>
      <h3>{{ noticia.titulo }}</h3>
      <p v-if="noticia.resumen" class="tarjeta-descripcion">{{ noticia.resumen }}</p>
      <span class="noticia-leer">Leer más <Icono nombre="arrow_forward" /></span>
    </div>
  </RouterLink>
</template>
