<script setup>
import { DIAS } from '../api'

// Editor de la disponibilidad semanal para visitas (franjas por día y hora)
const props = defineProps({
  franjas: { type: Array, required: true }, // [{ dia, inicio, fin }] (se edita directamente)
  duracion: { type: Number, required: true },
})
const emit = defineEmits(['update:duracion'])

const DURACIONES = [15, 20, 30, 45, 60, 90]

function agregar() {
  const ultima = props.franjas[props.franjas.length - 1]
  props.franjas.push({ dia: ultima ? (ultima.dia + 1) % 7 : 0, inicio: ultima?.inicio || '09:00', fin: ultima?.fin || '12:00' })
}

// Atajo: la misma franja de lunes a viernes
function diasHabiles() {
  const base = props.franjas[0] || { inicio: '09:00', fin: '12:00' }
  const otras = props.franjas.filter((f) => f.dia > 4)
  props.franjas.splice(0, props.franjas.length, ...[0, 1, 2, 3, 4].map((dia) => ({ dia, inicio: base.inicio, fin: base.fin })), ...otras)
}
</script>

<template>
  <fieldset class="horario">
    <legend>Horario de visitas</legend>
    <p class="opcional">
      Te proponemos de lunes a viernes de 9:00 a 17:00: cambia los días y las horas, agrega franjas
      (por ejemplo el sábado en la mañana) o quita las que no te sirvan. Los interesados agendarán
      en esas horas desde el aviso; sin franjas, solo verán los teléfonos.
    </p>
    <label class="horario-duracion">
      Duración de cada visita
      <select :value="duracion" @change="emit('update:duracion', Number($event.target.value))">
        <option v-for="d in DURACIONES" :key="d" :value="d">{{ d }} minutos</option>
      </select>
    </label>

    <p v-if="!franjas.length" class="vacio">Sin horario de visitas: el aviso solo mostrará los teléfonos.</p>
    <div v-for="(f, i) in franjas" :key="i" class="horario-fila">
      <select v-model.number="f.dia" aria-label="Día">
        <option v-for="(d, n) in DIAS" :key="n" :value="n">{{ d }}</option>
      </select>
      <span>de</span>
      <input v-model="f.inicio" type="time" step="900" required aria-label="Desde" />
      <span>a</span>
      <input v-model="f.fin" type="time" step="900" required aria-label="Hasta" />
      <button type="button" class="enlace peligro-texto" @click="franjas.splice(i, 1)">Quitar</button>
    </div>

    <div class="acciones">
      <button type="button" class="boton secundario" @click="agregar">+ Agregar franja</button>
      <button v-if="franjas.length" type="button" class="enlace" @click="diasHabiles">Usar la primera de lunes a viernes</button>
      <button v-if="franjas.length" type="button" class="enlace peligro-texto" @click="franjas.splice(0)">Quitar todas</button>
    </div>
  </fieldset>
</template>
