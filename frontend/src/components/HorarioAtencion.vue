<script setup>
import { DIAS } from '../api'
import Icono from './Icono.vue'

// Editor del horario de atención de una zona común (franjas por día de la semana)
const props = defineProps({ franjas: { type: Array, required: true } }) // [{ dia, inicio, fin }]

const todosLosDias = (inicio = '06:00', fin = '22:00') =>
  props.franjas.splice(0, props.franjas.length, ...[0, 1, 2, 3, 4, 5, 6].map((dia) => ({ dia, inicio, fin })))

function agregar() {
  const ultima = props.franjas[props.franjas.length - 1]
  props.franjas.push({ dia: ultima ? (ultima.dia + 1) % 7 : 0, inicio: ultima?.inicio || '06:00', fin: ultima?.fin || '22:00' })
}
</script>

<template>
  <fieldset class="horario">
    <legend>Horario de atención</legend>
    <p class="opcional">
      Los residentes reservan la zona dentro de este horario, en franjas de 1 o 2 horas que empiezan
      en punto.
    </p>
    <p v-if="!franjas.length" class="vacio">Sin horario: la zona no se puede reservar.</p>
    <div v-for="(f, i) in franjas" :key="i" class="horario-fila">
      <select v-model.number="f.dia" aria-label="Día">
        <option v-for="(d, n) in DIAS" :key="n" :value="n">{{ d }}</option>
      </select>
      <span>de</span>
      <input v-model="f.inicio" type="time" step="3600" required aria-label="Abre" />
      <span>a</span>
      <input v-model="f.fin" type="time" step="3600" required aria-label="Cierra" />
      <button type="button" class="enlace peligro-texto" @click="franjas.splice(i, 1)">Quitar</button>
    </div>
    <div class="acciones">
      <button type="button" class="boton secundario" @click="agregar"><Icono nombre="add" /> Agregar franja</button>
      <button type="button" class="enlace" @click="todosLosDias()">Lunes a domingo, 06:00 a 22:00</button>
      <button v-if="franjas.length" type="button" class="enlace peligro-texto" @click="franjas.splice(0)">Quitar todas</button>
    </div>
  </fieldset>
</template>
