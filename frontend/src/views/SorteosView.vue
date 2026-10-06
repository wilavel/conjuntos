<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api, fechaCorta } from '../api'
import AdminNav from '../components/AdminNav.vue'

const router = useRouter()
const sorteos = ref([])
const parqueaderos = ref([])
const cargando = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    ;[sorteos.value, parqueaderos.value] = await Promise.all([api.sorteos(), api.parqueaderos()])
  } catch (e) {
    error.value = e.message
  } finally {
    cargando.value = false
  }
})

// ---------- nuevo sorteo ----------
const hoy = new Date().toLocaleDateString('en-CA', { timeZone: 'America/Bogota' })
const enDias = (n) => new Date(Date.now() + n * 864e5).toLocaleDateString('en-CA', { timeZone: 'America/Bogota' })
const nuevo = ref(null)
function abrir() {
  nuevo.value = { nombre: '', tipo: 'carro', meses: 6, cierre: enDias(15), inicio: enDias(30), ids: [] }
  marcarTodos()
}
const disponibles = computed(() =>
  parqueaderos.value.filter((p) => p.uso === 'residente' && p.tipo === nuevo.value?.tipo),
)
const marcarTodos = () => (nuevo.value.ids = disponibles.value.map((p) => p.id))

async function crear() {
  error.value = ''
  try {
    const { ids, ...datos } = nuevo.value
    const s = await api.crearSorteo({ ...datos, parqueadero_ids: ids })
    router.push(`/admin/sorteos/${s.id}`)
  } catch (e) {
    error.value = e.message
  }
}
</script>

<template>
  <AdminNav />
  <div class="encabezado titulo-admin">
    <h1>Sorteos de parqueaderos</h1>
    <button v-if="!nuevo" type="button" class="boton" @click="abrir">Nuevo sorteo</button>
  </div>
  <p class="intro-admin">
    Los parqueaderos de residentes se asignan por un periodo (por ejemplo 6 meses) mediante sorteo
    entre los apartamentos que se postulan. Los residentes se postulan desde su zona privada hasta
    la fecha de cierre; la administración también puede inscribir apartamentos.
  </p>

  <form v-if="nuevo" class="formulario usuario-nuevo" @submit.prevent="crear">
    <h2>Nuevo sorteo</h2>
    <div class="grupo">
      <label>Nombre<input v-model="nuevo.nombre" required maxlength="120" placeholder="Parqueaderos 2027-I" /></label>
      <label>
        Tipo
        <select v-model="nuevo.tipo" @change="marcarTodos">
          <option value="carro">Carros</option>
          <option value="moto">Motos</option>
        </select>
      </label>
      <label>Duración (meses)<input v-model.number="nuevo.meses" type="number" min="1" max="60" required /></label>
    </div>
    <div class="grupo">
      <label>Postulaciones hasta<input v-model="nuevo.cierre" type="date" :min="hoy" required /></label>
      <label>La asignación rige desde<input v-model="nuevo.inicio" type="date" required /></label>
    </div>
    <fieldset>
      <legend>Parqueaderos que entran ({{ nuevo.ids.length }} de {{ disponibles.length }})</legend>
      <p v-if="!disponibles.length" class="vacio">
        No hay parqueaderos de residentes para {{ nuevo.tipo }}s. Créalos en
        <RouterLink to="/admin/parqueaderos">Parqueaderos</RouterLink>.
      </p>
      <div class="sorteo-cupos">
        <label v-for="p in disponibles" :key="p.id" class="check">
          <input v-model="nuevo.ids" type="checkbox" :value="p.id" />
          {{ p.numero }}
          <small v-if="p.apartamento">(hoy: Apto {{ p.apartamento.numero }})</small>
        </label>
      </div>
      <div class="acciones">
        <button type="button" class="enlace" @click="marcarTodos">Marcar todos</button>
        <button type="button" class="enlace" @click="nuevo.ids = []">Ninguno</button>
      </div>
    </fieldset>
    <p v-if="error" class="error">{{ error }}</p>
    <div class="acciones">
      <button class="boton" type="submit" :disabled="!nuevo.ids.length">Crear sorteo</button>
      <button type="button" class="enlace" @click="nuevo = null">Cancelar</button>
    </div>
  </form>

  <p v-if="error && !nuevo" class="error">{{ error }}</p>
  <p v-if="cargando">Cargando…</p>
  <p v-else-if="!sorteos.length && !nuevo" class="vacio">Aún no hay sorteos.</p>

  <div class="lista">
    <RouterLink v-for="s in sorteos" :key="s.id" class="fila fila-apto" :to="`/admin/sorteos/${s.id}`">
      <div class="datos">
        <strong>{{ s.nombre }}</strong>
        <span>{{ s.tipo === 'moto' ? 'Motos' : 'Carros' }} · {{ s.num_parqueaderos }} parqueaderos · {{ s.num_postulaciones }} postulados</span>
        <span>Asignación por {{ s.meses }} meses: {{ fechaCorta(s.inicio) }} al {{ fechaCorta(s.fin) }}</span>
      </div>
      <span class="estado" :class="s.estado === 'realizado' ? 'publicado' : 'borrador'">
        {{ s.estado === 'realizado' ? 'realizado' : s.abierto ? 'postulaciones abiertas' : 'postulaciones cerradas' }}
      </span>
    </RouterLink>
  </div>
</template>
