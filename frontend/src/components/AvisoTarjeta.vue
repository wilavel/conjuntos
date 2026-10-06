<script setup>
import { cop } from '../api'

// Tarjeta de un aviso de venta o arriendo (catálogo e inicio).
// La foto principal se ve completa: el espacio sobrante se rellena con la misma foto difuminada.
const props = defineProps({ aviso: { type: Object, required: true } })

const arriendo = () => props.aviso.negocio === 'arriendo'
const area = () => props.aviso.area_construida_m2 || props.aviso.area_lote_m2 || 0
</script>

<template>
  <RouterLink class="tarjeta" :to="`/propiedades/${aviso.id}`">
    <div class="tarjeta-foto">
      <template v-if="aviso.fotos.length">
        <div class="tarjeta-foto-fondo" :style="{ backgroundImage: `url(${aviso.fotos[0].url})` }" aria-hidden="true"></div>
        <img :src="aviso.fotos[0].url" :alt="aviso.titulo" loading="lazy" />
      </template>
      <div v-else class="sin-foto">Sin foto</div>
      <span class="insignia insignia-negocio">
        {{ arriendo() ? (aviso.amoblado ? 'Arriendo amoblado' : 'Arriendo') : 'Venta' }}
      </span>
      <span v-if="aviso.fotos.length > 1" class="tarjeta-num-fotos">{{ aviso.fotos.length }} fotos</span>
    </div>
    <div class="tarjeta-cuerpo">
      <span class="tarjeta-lugar">{{ [aviso.barrio, aviso.ciudad].filter(Boolean).join(' | ') }}</span>
      <h3>{{ aviso.titulo }}</h3>
      <p class="tarjeta-precio">{{ cop(aviso.precio) }}<small v-if="arriendo()"> /mes</small></p>
      <ul class="rasgos">
        <li v-if="aviso.habitaciones">{{ aviso.habitaciones }} hab.</li>
        <li v-if="aviso.banos">{{ aviso.banos }} {{ aviso.banos === 1 ? 'baño' : 'baños' }}</li>
        <li v-if="area()">{{ area() }} m²</li>
        <li v-if="aviso.parqueaderos">{{ aviso.parqueaderos }} parq.</li>
        <li v-if="aviso.estrato">Estrato {{ aviso.estrato }}</li>
      </ul>
    </div>
  </RouterLink>
</template>
