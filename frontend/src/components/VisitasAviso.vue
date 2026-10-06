<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'

// Visitas agendadas del aviso: solo para quien lo publicó y la administración
const props = defineProps({ avisoId: { type: Number, required: true } })

const visitas = ref([])
const error = ref('')
const verPasadas = ref(false)
const hoy = new Date().toLocaleDateString('en-CA', { timeZone: 'America/Bogota' }) // AAAA-MM-DD

onMounted(async () => {
  try {
    visitas.value = await api.visitas(props.avisoId)
  } catch (e) {
    error.value = e.message
  }
})

const proximas = computed(() => visitas.value.filter((v) => v.fecha >= hoy))
const pasadas = computed(() => visitas.value.filter((v) => v.fecha < hoy))
const pendientes = computed(() => proximas.value.filter((v) => v.estado === 'pendiente').length)
const fecha = (v) => new Date(`${v.fecha}T12:00:00`).toLocaleDateString('es-CO', { weekday: 'long', day: 'numeric', month: 'long' })

async function cambiar(v, estado) {
  if (estado === 'cancelada' && !confirm(`¿Cancelar la visita de ${v.nombre}?`)) return
  error.value = ''
  try {
    const nueva = await api.estadoVisita(v.id, estado)
    visitas.value = visitas.value.map((x) => (x.id === v.id ? nueva : x))
  } catch (e) {
    error.value = e.message
  }
}
</script>

<template>
  <section class="visitas-aviso">
    <h2>
      Visitas agendadas
      <span v-if="pendientes" class="contador-fotos">{{ pendientes }} por confirmar</span>
    </h2>
    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="!proximas.length" class="vacio">No hay visitas próximas.</p>
    <ul class="personas-lista">
      <li v-for="v in verPasadas ? [...proximas, ...pasadas] : proximas" :key="v.id" :class="{ inactiva: v.estado === 'cancelada' || v.fecha < hoy }">
        <div class="persona-datos">
          <strong>{{ fecha(v) }} · {{ v.hora }}</strong>
          <span>{{ v.nombre }} · <a :href="`tel:${v.telefono}`">{{ v.telefono }}</a><template v-if="v.email"> · {{ v.email }}</template></span>
          <span v-if="v.mensaje">«{{ v.mensaje }}»</span>
        </div>
        <div class="persona-acciones">
          <span class="estado" :class="{ pendiente: 'borrador', confirmada: 'publicado', cancelada: 'vendido' }[v.estado]">{{ v.estado }}</span>
          <template v-if="v.fecha >= hoy">
            <button v-if="v.estado === 'pendiente'" type="button" class="enlace" @click="cambiar(v, 'confirmada')">Confirmar</button>
            <button v-if="v.estado !== 'cancelada'" type="button" class="enlace peligro-texto" @click="cambiar(v, 'cancelada')">Cancelar</button>
          </template>
        </div>
      </li>
    </ul>
    <button v-if="pasadas.length" type="button" class="enlace" @click="verPasadas = !verPasadas">
      {{ verPasadas ? 'Ocultar visitas pasadas' : `Ver visitas pasadas (${pasadas.length})` }}
    </button>
  </section>
</template>
