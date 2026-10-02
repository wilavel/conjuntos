<script setup>
import { reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'

const props = defineProps({ id: String })
const router = useRouter()

const tipos = ref([])
const form = reactive({
  tipo_id: '',
  titulo: '',
  precio: '',
  administracion: '',
  area_construida_m2: '',
  area_lote_m2: '',
  habitaciones: 0,
  banos: 0,
  parqueaderos: 0,
  pisos: 1,
  piso: '',
  anio_construccion: '',
  estrato: '',
  ciudad: '',
  barrio: '',
  direccion: '',
  descripcion: '',
})
const anioMax = new Date().getFullYear() + 5
const error = ref('')
const guardando = ref(false)

// Campos numéricos opcionales: vacío se envía como null
const OPCIONALES = ['administracion', 'area_construida_m2', 'area_lote_m2', 'piso', 'anio_construccion', 'estrato']

onMounted(async () => {
  try {
    tipos.value = await api.tipos()
    if (props.id) {
      const p = await api.obtener(props.id)
      for (const k of Object.keys(form)) form[k] = p[k] ?? ''
    }
  } catch (e) {
    error.value = e.message
  }
})

async function guardar() {
  guardando.value = true
  error.value = ''
  const datos = { ...form }
  for (const k of OPCIONALES) datos[k] = form[k] === '' || form[k] === null ? null : Number(form[k])
  for (const k of ['habitaciones', 'banos', 'parqueaderos']) datos[k] = form[k] || 0
  datos.pisos = form.pisos || 1
  try {
    const p = props.id ? await api.actualizar(props.id, datos) : await api.crear(datos)
    router.push(`/propiedades/${p.id}`)
  } catch (e) {
    error.value = e.message
    guardando.value = false
  }
}
</script>

<template>
  <h1>{{ id ? 'Editar propiedad' : 'Nueva propiedad' }}</h1>
  <form class="formulario" @submit.prevent="guardar">
    <div class="grupo">
      <label>
        Tipo de propiedad
        <select v-model="form.tipo_id" required>
          <option value="" disabled>Selecciona un tipo</option>
          <option v-for="t in tipos" :key="t.id" :value="t.id">{{ t.nombre }}</option>
        </select>
      </label>
      <label>Precio (COP)<input v-model.number="form.precio" type="number" min="0" required /></label>
      <label>Administración mensual (COP)<input v-model.number="form.administracion" type="number" min="0" /></label>
    </div>
    <label>
      Título
      <input v-model="form.titulo" required maxlength="200" placeholder="Casa de 4 habitaciones en Suba" />
    </label>

    <fieldset>
      <legend>Áreas y distribución</legend>
      <div class="grupo">
        <label>Área construida (m²)<input v-model.number="form.area_construida_m2" type="number" min="0" step="any" /></label>
        <label>Área del lote (m²)<input v-model.number="form.area_lote_m2" type="number" min="0" step="any" /></label>
        <label>Año de construcción<input v-model.number="form.anio_construccion" type="number" min="1800" :max="anioMax" placeholder="2015" /></label>
      </div>
      <div class="grupo">
        <label>Habitaciones<input v-model.number="form.habitaciones" type="number" min="0" /></label>
        <label>Baños<input v-model.number="form.banos" type="number" min="0" /></label>
        <label>Parqueaderos<input v-model.number="form.parqueaderos" type="number" min="0" /></label>
      </div>
      <div class="grupo">
        <label>Cantidad de pisos<input v-model.number="form.pisos" type="number" min="1" /></label>
        <label>Piso en el que queda<input v-model.number="form.piso" type="number" min="0" /></label>
        <label>Estrato<input v-model.number="form.estrato" type="number" min="1" max="6" /></label>
      </div>
    </fieldset>

    <fieldset>
      <legend>Ubicación</legend>
      <div class="grupo">
        <label>Ciudad<input v-model="form.ciudad" required maxlength="100" /></label>
        <label>Barrio<input v-model="form.barrio" maxlength="100" /></label>
      </div>
      <label>
        Dirección
        <input v-model="form.direccion" required maxlength="255" />
      </label>
    </fieldset>

    <label>
      Descripción
      <textarea v-model="form.descripcion" rows="8"></textarea>
    </label>
    <p v-if="error" class="error">{{ error }}</p>
    <div class="acciones">
      <button class="boton" type="submit" :disabled="guardando">Guardar</button>
      <RouterLink :to="id ? `/propiedades/${id}` : '/admin'">Cancelar</RouterLink>
    </div>
  </form>
</template>
