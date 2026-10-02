<script setup>
import { ref, watch, onMounted } from 'vue'
import { api, cop, capitalizar, ESTADOS } from '../api'

const propiedades = ref([])
const tipos = ref([])
const estado = ref('')
const tipoId = ref('')
const cargando = ref(true)
const error = ref('')

async function cargar() {
  cargando.value = true
  error.value = ''
  try {
    propiedades.value = await api.listar({ estado: estado.value, tipoId: tipoId.value })
  } catch (e) {
    error.value = e.message
  } finally {
    cargando.value = false
  }
}

function area(p) {
  const a = p.area_construida_m2 || p.area_lote_m2
  return a ? `${a} m²` : ''
}

onMounted(async () => {
  tipos.value = await api.tipos().catch(() => [])
  cargar()
})
watch([estado, tipoId], cargar)
</script>

<template>
  <div class="encabezado titulo-admin">
    <h1>Administrar propiedades</h1>
    <RouterLink class="boton" to="/nuevo">Nueva propiedad</RouterLink>
  </div>

  <div class="barra-filtros">
    <nav class="filtros">
      <a href="#" :class="{ activo: !estado }" @click.prevent="estado = ''">Todos</a>
      <a
        v-for="e in ESTADOS"
        :key="e"
        href="#"
        :class="{ activo: estado === e }"
        @click.prevent="estado = e"
      >
        {{ capitalizar(e) }}
      </a>
    </nav>
    <select v-model="tipoId" class="filtro-tipo" aria-label="Filtrar por tipo">
      <option value="">Todos los tipos</option>
      <option v-for="t in tipos" :key="t.id" :value="t.id">{{ t.nombre }}</option>
    </select>
  </div>

  <p v-if="error" class="error">{{ error }}</p>
  <p v-else-if="cargando">Cargando…</p>
  <p v-else-if="!propiedades.length" class="vacio">
    Aún no hay propiedades con estos filtros.
    <RouterLink to="/nuevo">Crea la primera</RouterLink> para empezar a armar tus anuncios.
  </p>

  <div class="lista">
    <RouterLink v-for="p in propiedades" :key="p.id" class="fila" :to="`/propiedades/${p.id}`">
      <img v-if="p.fotos.length" :src="p.fotos[0].url" alt="" />
      <div v-else class="sin-foto">Sin foto</div>
      <div class="datos">
        <strong>{{ p.titulo }}</strong>
        <span>{{ cop(p.precio) }}</span>
        <span>
          {{ p.tipo }}<template v-if="area(p)">, {{ area(p) }}</template
          ><template v-if="p.habitaciones">, {{ p.habitaciones }} hab.</template
          ><template v-if="p.banos">, {{ p.banos }} baños</template>
        </span>
        <span>{{ p.barrio ? p.barrio + ', ' : '' }}{{ p.ciudad }}</span>
      </div>
      <span class="estado" :class="p.estado">{{ p.estado }}</span>
    </RouterLink>
  </div>
</template>
