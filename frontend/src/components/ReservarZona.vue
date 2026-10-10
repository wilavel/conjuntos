<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { api, nombreApto } from '../api'
import { simboloZona } from '../zonas'
import { sesion } from '../sesion'
import Icono from './Icono.vue'

// Reserva de una zona común para mi apartamento: zona → día → 1 o 2 horas → hora en punto
const props = defineProps({ zonaInicial: { type: String, default: '' } }) // slug
const emit = defineEmits(['reservado'])

const zonas = ref([])
const zonaId = ref(null)
const aptoId = ref(null)
const fecha = ref('')
const horas = ref(1)
const disponibles = ref([])
const hora = ref('')
const cargandoHoras = ref(false)
const error = ref('')
const listo = ref(null)

const misAptos = computed(() => {
  const vistos = new Map()
  for (const a of sesion.value?.apartamentos || []) vistos.set(a.id, a)
  return [...vistos.values()]
})
const zona = computed(() => zonas.value.find((z) => z.id === zonaId.value))

// Próximos 14 días en que la zona atiende
const dias = computed(() => {
  if (!zona.value) return []
  const abre = new Set(zona.value.franjas.map((f) => f.dia))
  const lista = []
  for (let n = 0; n < 14; n++) {
    const d = new Date(Date.now() + n * 864e5)
    const iso = d.toLocaleDateString('en-CA', { timeZone: 'America/Bogota' })
    const dia = (new Date(`${iso}T12:00:00`).getDay() + 6) % 7 // 0 = lunes
    if (abre.has(dia)) lista.push(iso)
  }
  return lista
})
const etiqueta = (iso) => {
  const f = new Date(`${iso}T12:00:00`)
  return {
    dia: f.toLocaleDateString('es-CO', { weekday: 'short' }).replace('.', ''),
    num: f.getDate(),
    mes: f.toLocaleDateString('es-CO', { month: 'short' }).replace('.', ''),
  }
}
const fechaLarga = (iso) => new Date(`${iso}T12:00:00`).toLocaleDateString('es-CO', { weekday: 'long', day: 'numeric', month: 'long' })
const fin = computed(() => {
  if (!hora.value) return ''
  const h = Number(hora.value.slice(0, 2)) + horas.value
  return `${String(h).padStart(2, '0')}:00`
})

onMounted(async () => {
  zonas.value = (await api.zonas().catch(() => [])).filter((z) => z.reservable && z.franjas.length)
  const inicial = zonas.value.find((z) => z.slug === props.zonaInicial) || zonas.value[0]
  zonaId.value = inicial?.id ?? null
  aptoId.value = misAptos.value[0]?.id ?? null
})

watch(zonaId, () => {
  listo.value = null
  fecha.value = dias.value[0] || ''
})
watch([zonaId, fecha, horas], cargarHoras)

async function cargarHoras() {
  hora.value = ''
  disponibles.value = []
  if (!zonaId.value || !fecha.value) return
  cargandoHoras.value = true
  try {
    disponibles.value = (await api.disponibilidadZona(zonaId.value, fecha.value, horas.value)).horas
  } catch (e) {
    error.value = e.message
  } finally {
    cargandoHoras.value = false
  }
}

async function reservar() {
  error.value = ''
  try {
    listo.value = await api.reservar({ zona_id: zonaId.value, apartamento_id: aptoId.value, fecha: fecha.value, inicio: hora.value, horas: horas.value })
    emit('reservado')
    await cargarHoras()
  } catch (e) {
    error.value = e.message
    await cargarHoras()
  }
}
</script>

<template>
  <div class="reservar">
    <p v-if="!zonas.length" class="vacio">Por ahora no hay zonas comunes disponibles para reservar.</p>
    <template v-else>
      <div class="reservar-zonas" role="radiogroup" aria-label="Zona común">
        <button v-for="z in zonas" :key="z.id" type="button" :class="{ activo: zonaId === z.id }" @click="zonaId = z.id">
          <Icono :nombre="simboloZona(z.icono)" /> {{ z.nombre }}
        </button>
      </div>
      <p v-if="zona" class="reservar-horario"><Icono nombre="schedule" /> {{ zona.horario }}</p>

      <div v-if="listo" class="aviso-ok">
        <strong>¡Reserva confirmada!</strong> {{ listo.zona.nombre }} para el Apto {{ listo.apartamento.numero }},
        {{ fechaLarga(listo.fecha) }} de {{ listo.inicio }} a {{ listo.fin }}.
      </div>

      <form class="formulario" @submit.prevent="reservar">
        <label v-if="misAptos.length > 1">
          Apartamento
          <select v-model="aptoId">
            <option v-for="a in misAptos" :key="a.id" :value="a.id">{{ nombreApto(a) }}</option>
          </select>
        </label>
        <div>
          <span class="agendar-paso">1. Día</span>
          <div class="agendar-dias">
            <button v-for="d in dias" :key="d" type="button" :class="{ activo: fecha === d }" @click="fecha = d">
              <small>{{ etiqueta(d).dia }}</small><strong>{{ etiqueta(d).num }}</strong><small>{{ etiqueta(d).mes }}</small>
            </button>
          </div>
        </div>
        <div>
          <span class="agendar-paso">2. Duración</span>
          <div class="segmentos reservar-duracion">
            <button v-for="h in [1, 2]" :key="h" type="button" :class="{ activo: horas === h }" @click="horas = h">
              {{ h }} {{ h === 1 ? 'hora' : 'horas' }}
            </button>
          </div>
        </div>
        <div>
          <span class="agendar-paso">3. Hora de inicio</span>
          <p v-if="cargandoHoras" class="opcional">Buscando horas libres…</p>
          <p v-else-if="!disponibles.length" class="opcional">No hay horas libres ese día. Prueba otro día o 1 hora.</p>
          <div class="agendar-horas">
            <button v-for="h in disponibles" :key="h" type="button" :class="{ activo: hora === h }" @click="hora = h">{{ h }}</button>
          </div>
        </div>
        <p v-if="error" class="error">{{ error }}</p>
        <button class="boton" type="submit" :disabled="!hora || !aptoId">
          <Icono nombre="event_available" />
          {{ hora ? `Reservar ${zona?.nombre} · ${fechaLarga(fecha)} de ${hora} a ${fin}` : 'Elige una hora' }}
        </button>
      </form>
    </template>
  </div>
</template>
