<script setup>
import { computed } from 'vue'
import { cop } from '../api'
import Icono from './Icono.vue'

// Tarjeta de un aviso de venta o arriendo (catálogo e inicio), con la distribución del diseño.
// La foto principal se ve completa: el espacio sobrante se rellena con la misma foto difuminada.
const props = defineProps({ aviso: { type: Object, required: true } })

const arriendo = computed(() => props.aviso.negocio === 'arriendo')
const area = computed(() => props.aviso.area_construida_m2 || props.aviso.area_lote_m2 || 0)
const plural = (n, uno, varios) => `${n} ${n === 1 ? uno : varios}`
</script>

<template>
  <RouterLink class="tarjeta" :to="`/propiedades/${aviso.id}`">
    <div class="tarjeta-foto">
      <template v-if="aviso.fotos.length">
        <div class="tarjeta-foto-fondo" :style="{ backgroundImage: `url(${aviso.fotos[0].url})` }" aria-hidden="true"></div>
        <img :src="aviso.fotos[0].url" :alt="aviso.titulo" loading="lazy" />
      </template>
      <div v-else class="sin-foto"><Icono nombre="photo_camera" /></div>
      <span class="insignia insignia-negocio">
        {{ arriendo ? (aviso.amoblado ? 'Arriendo amoblado' : 'Arriendo') : 'Venta' }}
      </span>
      <span v-if="aviso.piso != null" class="insignia insignia-clara">Piso {{ aviso.piso }}</span>
      <span v-if="aviso.fotos.length > 1" class="tarjeta-num-fotos"><Icono nombre="photo_library" /> {{ aviso.fotos.length }}</span>
    </div>
    <div class="tarjeta-cuerpo">
      <div class="tarjeta-titulo">
        <h3>{{ aviso.titulo }}</h3>
        <span v-if="area" class="tarjeta-area">{{ area }} m²</span>
      </div>
      <p v-if="aviso.descripcion" class="tarjeta-descripcion">{{ aviso.descripcion }}</p>
      <ul class="tarjeta-specs">
        <li><Icono nombre="bed" /><span>{{ plural(aviso.habitaciones, 'Habitación', 'Habitaciones') }}</span></li>
        <li><Icono nombre="bathtub" /><span>{{ plural(aviso.banos, 'Baño', 'Baños') }}</span></li>
        <li><Icono nombre="directions_car" /><span>{{ plural(aviso.parqueaderos, 'Parqueadero', 'Parqueaderos') }}</span></li>
      </ul>
      <div class="tarjeta-pie">
        <span>
          <small>{{ arriendo ? 'Canon mensual' : 'Precio' }}</small>
          <strong class="tarjeta-precio">{{ cop(aviso.precio) }}</strong>
        </span>
        <span class="tarjeta-ir" aria-hidden="true"><Icono nombre="arrow_forward" /></span>
      </div>
    </div>
  </RouterLink>
</template>
