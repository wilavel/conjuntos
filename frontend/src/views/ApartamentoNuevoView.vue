<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import PersonaCampos from '../components/PersonaCampos.vue'
import { ultimasInvitaciones } from '../invitaciones'

const router = useRouter()

const nuevaPersona = () => ({ nombre: '', identificacion: '', telefono: '', email: '' })
const form = reactive({
  numero: '', piso: '', area_m2: '', habitaciones: 0, banos: 0, coeficiente: '', deudor: false,
  propietarios: [nuevaPersona()],
})
const error = ref('')
const guardando = ref(false)

async function guardar() {
  guardando.value = true
  error.value = ''
  const datos = {
    ...form,
    piso: form.piso === '' ? null : Number(form.piso),
    area_m2: form.area_m2 === '' ? null : Number(form.area_m2),
    habitaciones: Number(form.habitaciones) || 0,
    banos: Number(form.banos) || 0,
    coeficiente: form.coeficiente === '' ? null : Number(form.coeficiente),
  }
  try {
    const a = await api.crearApartamento(datos)
    ultimasInvitaciones.value = a.invitaciones || []
    router.push(`/admin/apartamentos/${a.id}`)
  } catch (e) {
    error.value = e.message
    guardando.value = false
  }
}
</script>

<template>
  <h1>Nuevo apartamento</h1>
  <form class="formulario" @submit.prevent="guardar">
    <div class="grupo">
      <label>Número<input v-model="form.numero" required maxlength="20" placeholder="502" /></label>
      <label>Piso<input v-model.number="form.piso" type="number" min="0" /></label>
      <label>Área (m²)<input v-model.number="form.area_m2" type="number" min="0" step="any" /></label>
    </div>
    <div class="grupo">
      <label>Habitaciones<input v-model.number="form.habitaciones" type="number" min="0" /></label>
      <label>Baños<input v-model.number="form.banos" type="number" min="0" /></label>
      <label>Coeficiente de copropiedad (%)<input v-model.number="form.coeficiente" type="number" min="0" max="100" step="any" placeholder="0,8523" /></label>
    </div>

    <fieldset v-for="(p, i) in form.propietarios" :key="i">
      <legend>Propietario {{ form.propietarios.length > 1 ? i + 1 : '' }}</legend>
      <PersonaCampos :persona="p" />
      <button v-if="form.propietarios.length > 1" type="button" class="enlace" @click="form.propietarios.splice(i, 1)">
        Quitar este propietario
      </button>
    </fieldset>
    <button type="button" class="boton secundario" @click="form.propietarios.push(nuevaPersona())">
      + Agregar otro propietario
    </button>

    <p class="opcional">
      A cada propietario se le crea su cuenta y se le envía un correo para crear su contraseña. Los
      arrendatarios se agregan después, desde la ficha del apartamento.
    </p>
    <p v-if="error" class="error">{{ error }}</p>
    <div class="acciones">
      <button class="boton" type="submit" :disabled="guardando">Crear apartamento</button>
      <RouterLink to="/admin/apartamentos">Cancelar</RouterLink>
    </div>
  </form>
</template>
