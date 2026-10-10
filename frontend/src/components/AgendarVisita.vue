<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { api } from '../api'

// El visitante elige día y hora libres y deja sus datos (no necesita cuenta)
const props = defineProps({ avisoId: { type: Number, required: true } })

const dias = ref([])
const duracion = ref(30)
const fecha = ref('')
const hora = ref('')
const datos = reactive({ nombre: '', telefono: '', email: '', mensaje: '' })
const error = ref('')
const enviando = ref(false)
const agendada = ref(null)

async function cargar() {
  try {
    const r = await api.horarios(props.avisoId)
    dias.value = r.dias
    duracion.value = r.duracion
    if (!dias.value.some((d) => d.fecha === fecha.value)) fecha.value = dias.value[0]?.fecha || ''
    hora.value = ''
  } catch {
    dias.value = []
  }
}
onMounted(cargar)

const horas = computed(() => dias.value.find((d) => d.fecha === fecha.value)?.horas || [])
const etiquetaDia = (d) => {
  const f = new Date(`${d.fecha}T12:00:00`)
  return { dia: d.dia.slice(0, 3), num: f.getDate(), mes: f.toLocaleDateString('es-CO', { month: 'short' }).replace('.', '') }
}
const fechaLarga = (d) =>
  new Date(`${d}T12:00:00`).toLocaleDateString('es-CO', { weekday: 'long', day: 'numeric', month: 'long' })

async function agendar() {
  error.value = ''
  enviando.value = true
  try {
    agendada.value = await api.agendarVisita(props.avisoId, { ...datos, fecha: fecha.value, hora: hora.value })
  } catch (e) {
    error.value = e.message
    await cargar() // la hora pudo ocuparse mientras tanto
  } finally {
    enviando.value = false
  }
}
</script>

<template>
  <section v-if="dias.length || agendada" class="agendar">
    <h2>Agenda una visita</h2>

    <div v-if="agendada" class="aviso-ok">
      <strong>¡Listo, {{ agendada.nombre }}!</strong> Tu solicitud de visita quedó para el
      {{ fechaLarga(agendada.fecha) }} a las {{ agendada.hora }}. Te contactarán para confirmarla.
    </div>

    <form v-else class="formulario" @submit.prevent="agendar">
      <div>
        <span class="agendar-paso">1. Elige el día</span>
        <div class="agendar-dias">
          <button
            v-for="d in dias"
            :key="d.fecha"
            type="button"
            :class="{ activo: fecha === d.fecha }"
            @click="fecha = d.fecha; hora = ''"
          >
            <small>{{ etiquetaDia(d).dia }}</small>
            <strong>{{ etiquetaDia(d).num }}</strong>
            <small>{{ etiquetaDia(d).mes }}</small>
          </button>
        </div>
      </div>
      <div>
        <span class="agendar-paso">2. Elige la hora <span class="opcional">(visitas de {{ duracion }} minutos)</span></span>
        <div class="agendar-horas">
          <button v-for="h in horas" :key="h" type="button" :class="{ activo: hora === h }" @click="hora = h">{{ h }}</button>
        </div>
      </div>
      <template v-if="hora">
        <span class="agendar-paso">3. Tus datos <span class="opcional">(nombre, correo y teléfono para confirmar la visita)</span></span>
        <div class="grupo">
          <label>Nombre<input v-model="datos.nombre" required minlength="2" maxlength="100" autocomplete="name" /></label>
          <label>Teléfono<input v-model="datos.telefono" type="tel" required maxlength="30" autocomplete="tel" /></label>
          <label>Correo<input v-model="datos.email" type="email" required maxlength="255" autocomplete="email" /></label>
        </div>
        <label>Mensaje <span class="opcional">(opcional)</span><textarea v-model="datos.mensaje" rows="2" maxlength="1000"></textarea></label>
        <p v-if="error" class="error">{{ error }}</p>
        <button class="boton" type="submit" :disabled="enviando">
          Agendar visita el {{ fechaLarga(fecha) }} a las {{ hora }} <span class="flecha" aria-hidden="true">→</span>
        </button>
      </template>
      <p v-else-if="error" class="error">{{ error }}</p>
    </form>
  </section>
</template>
