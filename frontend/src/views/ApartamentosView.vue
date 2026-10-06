<script setup>
import { ref, computed, onMounted } from 'vue'
import { api, nombreApto, coef } from '../api'
import AdminNav from '../components/AdminNav.vue'

const apartamentos = ref([])
const cargando = ref(true)
const error = ref('')
const busqueda = ref('')

onMounted(async () => {
  try {
    apartamentos.value = await api.apartamentos()
  } catch (e) {
    error.value = e.message
  } finally {
    cargando.value = false
  }
})

// Entre todos los apartamentos los coeficientes deben sumar 100 %
const sumaCoeficientes = computed(() => apartamentos.value.reduce((t, a) => t + (a.coeficiente || 0), 0))
const deudores = computed(() => apartamentos.value.filter((a) => a.deudor).length)
const sinCoeficiente = computed(() => apartamentos.value.filter((a) => !a.coeficiente).length)

const activos = (lista) => lista.filter((p) => p.activo)

// Busca por número, nombre o identificación de cualquier persona del apartamento
const filtrados = computed(() => {
  const q = busqueda.value.trim().toLowerCase()
  if (!q) return apartamentos.value
  return apartamentos.value.filter((a) =>
    [a.numero, ...[...a.propietarios, ...a.arrendatarios].flatMap((p) => [p.nombre, p.identificacion])]
      .join(' ')
      .toLowerCase()
      .includes(q),
  )
})
</script>

<template>
  <AdminNav />
  <div class="encabezado titulo-admin">
    <h1>Apartamentos</h1>
    <RouterLink class="boton" to="/admin/apartamentos/nuevo">Nuevo apartamento</RouterLink>
  </div>

  <input v-if="apartamentos.length" v-model="busqueda" type="search" class="busqueda-admin"
    placeholder="Buscar por número, nombre o identificación" aria-label="Buscar apartamentos" />

  <p v-if="error" class="error">{{ error }}</p>
  <p v-else-if="cargando">Cargando…</p>
  <p v-else-if="!apartamentos.length" class="vacio">
    Aún no hay apartamentos. <RouterLink to="/admin/apartamentos/nuevo">Crea el primero</RouterLink>.
  </p>
  <p v-else-if="!filtrados.length" class="vacio">Ningún apartamento coincide con la búsqueda.</p>
  <p v-else class="opcional">
    {{ apartamentos.length }} apartamentos, ordenados por número · Suma de coeficientes:
    <strong :class="{ 'peligro-texto': Math.abs(sumaCoeficientes - 100) > 0.001 }">{{ coef(Math.round(sumaCoeficientes * 1e6) / 1e6) }}</strong>
    <template v-if="sinCoeficiente"> ({{ sinCoeficiente }} sin coeficiente)</template>
    <template v-if="deudores"> · <strong class="peligro-texto">{{ deudores }} {{ deudores === 1 ? 'deudor' : 'deudores' }}</strong></template>
  </p>

  <div class="lista">
    <article v-for="a in filtrados" :key="a.id" class="fila fila-apto">
      <RouterLink class="datos" :to="`/admin/apartamentos/${a.id}`">
        <strong>{{ nombreApto(a) }} <span v-if="a.deudor" class="perfil-insignia deudor">Deudor</span></strong>
        <span v-if="a.piso !== null || a.area_m2 || a.habitaciones || a.coeficiente">
          {{ [a.piso !== null && `Piso ${a.piso}`, a.area_m2 && `${a.area_m2} m²`, a.habitaciones && `${a.habitaciones} hab.`, a.coeficiente && `Coef. ${coef(a.coeficiente)}`].filter(Boolean).join(' · ') }}
        </span>
        <span>Propietarios: {{ activos(a.propietarios).map((p) => p.nombre).join(', ') || '—' }}</span>
        <span>Arrendatarios: {{ activos(a.arrendatarios).map((p) => p.nombre).join(', ') || '—' }}</span>
      </RouterLink>
      <div class="fila-acciones">
        <RouterLink class="boton secundario" :to="`/admin/apartamentos/${a.id}`">Ver</RouterLink>
        <RouterLink class="enlace" :to="{ path: `/admin/apartamentos/${a.id}`, query: { agregar: 'propietario' } }">+ Propietario</RouterLink>
        <RouterLink class="enlace" :to="{ path: `/admin/apartamentos/${a.id}`, query: { agregar: 'arrendatario' } }">+ Arrendatario</RouterLink>
      </div>
    </article>
  </div>
</template>
