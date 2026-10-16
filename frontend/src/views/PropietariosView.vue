<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { api, nombreApto, coef, documento } from '../api'
import PersonaCampos from '../components/PersonaCampos.vue'
import Icono from '../components/Icono.vue'

// Directorio: cada persona o empresa una sola vez, con todos sus apartamentos.
// Al editar aquí, los datos se actualizan en todos sus apartamentos.
const rol = ref('propietario')
const lista = ref([])
const cargando = ref(true)
const error = ref('')
const aviso = ref('')
const busqueda = ref('')
const filtro = ref('todos')

async function cargar() {
  cargando.value = true
  error.value = ''
  try {
    lista.value = await api.directorio(rol.value)
  } catch (e) {
    error.value = e.message
  } finally {
    cargando.value = false
  }
}
watch(rol, cargar, { immediate: true })

const FILTROS = {
  todos: ['Todos', () => true],
  varios: ['Con varios apartamentos', (p) => p.apartamentos.length > 1],
  empresas: ['Empresas', (p) => p.tipo_persona === 'juridica'],
  mora: ['Con mora', (p) => p.en_mora],
  sincuenta: ['Sin cuenta', (p) => !p.tiene_cuenta],
}
const filtrados = computed(() => {
  const q = busqueda.value.trim().toLowerCase()
  return lista.value.filter(FILTROS[filtro.value][1]).filter((p) =>
    !q || [p.nombre, p.identificacion, p.email, p.representante, ...p.apartamentos.map((a) => a.numero)].join(' ').toLowerCase().includes(q),
  )
})
const cuenta = (clave) => lista.value.filter(FILTROS[clave][1]).length

// ---------- edición (en todos sus apartamentos) ----------
const editando = ref(null)
const borrador = reactive({})
function editar(p) {
  editando.value = p.identificacion
  Object.assign(borrador, {
    nombre: p.nombre, tipo_persona: p.tipo_persona, tipo_documento: p.tipo_documento,
    representante: p.representante, telefono: p.telefono, email: p.email,
  })
}
async function guardar(p) {
  error.value = ''
  aviso.value = ''
  try {
    const r = await api.actualizarDirectorio(p.identificacion, { ...borrador })
    aviso.value = `Datos de ${borrador.nombre} actualizados en ${r.actualizados} ${r.actualizados === 1 ? 'registro' : 'registros'}.`
    editando.value = null
    await cargar()
  } catch (e) {
    error.value = e.message
  }
}
</script>

<template>
  <div class="encabezado titulo-admin">
    <div>
      <h1>Directorio</h1>
      <p class="intro-admin">
        Cada persona o empresa aparece una sola vez con todos sus apartamentos. Al editar sus datos
        aquí, se actualizan en todos ellos.
      </p>
    </div>
  </div>

  <div class="pestanas-directorio">
    <button type="button" :class="{ activo: rol === 'propietario' }" @click="rol = 'propietario'"><Icono nombre="real_estate_agent" /> Propietarios</button>
    <button type="button" :class="{ activo: rol === 'arrendatario' }" @click="rol = 'arrendatario'"><Icono nombre="key" /> Arrendatarios</button>
  </div>

  <input v-model="busqueda" type="search" class="busqueda-admin" placeholder="Buscar por nombre, documento, correo o apartamento" aria-label="Buscar" />
  <nav class="filtros barra-filtros">
    <a v-for="(f, clave) in FILTROS" :key="clave" href="#" :class="{ activo: filtro === clave }" @click.prevent="filtro = clave">
      {{ f[0] }} ({{ cuenta(clave) }})
    </a>
  </nav>

  <p v-if="aviso" class="aviso-ok">{{ aviso }}</p>
  <p v-if="error" class="error">{{ error }}</p>
  <p v-if="cargando">Cargando…</p>
  <p v-else-if="!filtrados.length" class="vacio">No hay {{ rol === 'propietario' ? 'propietarios' : 'arrendatarios' }} en este grupo.</p>

  <div class="directorio">
    <article v-for="p in filtrados" :key="p.identificacion" class="directorio-ficha">
      <form v-if="editando === p.identificacion" class="persona-edicion" @submit.prevent="guardar(p)">
        <p class="opcional">{{ documento(p) }} · el documento no se cambia aquí.</p>
        <PersonaCampos :persona="borrador" sin-identificacion />
        <div class="acciones">
          <button class="boton" type="submit">Guardar en {{ p.apartamentos.length }} {{ p.apartamentos.length === 1 ? 'apartamento' : 'apartamentos' }}</button>
          <button type="button" class="enlace" @click="editando = null">Cancelar</button>
        </div>
      </form>
      <template v-else>
        <div class="directorio-cabeza">
          <span class="icono-circulo"><Icono :nombre="p.tipo_persona === 'juridica' ? 'business' : 'person'" /></span>
          <div class="directorio-nombre">
            <strong>
              {{ p.nombre }}
              <span v-if="p.tipo_persona === 'juridica'" class="perfil-insignia">Empresa</span>
              <span v-if="p.en_mora" class="perfil-insignia deudor">En mora</span>
            </strong>
            <span>{{ documento(p) }}<template v-if="p.representante"> · Rep. legal: {{ p.representante }}</template></span>
            <span>
              <a :href="`mailto:${p.email}`">{{ p.email }}</a><template v-if="p.telefono"> · <a :href="`tel:${p.telefono}`">{{ p.telefono }}</a></template>
              <template v-if="!p.tiene_cuenta"> · <em>sin cuenta en la página</em></template>
            </span>
          </div>
          <button type="button" class="boton secundario" @click="editar(p)"><Icono nombre="edit" /> Editar</button>
        </div>
        <div class="directorio-aptos">
          <RouterLink v-for="a in p.apartamentos" :key="a.id" :to="`/admin/apartamentos/${a.id}`" class="directorio-apto" :class="{ deudor: a.deudor }">
            <strong>{{ nombreApto(a) }}</strong>
            <small v-if="a.coeficiente">{{ coef(a.coeficiente) }}</small>
            <small v-if="a.deudor" class="peligro-texto">En mora</small>
          </RouterLink>
        </div>
        <p class="directorio-total">
          {{ p.apartamentos.length }} {{ p.apartamentos.length === 1 ? 'apartamento' : 'apartamentos' }}
          <template v-if="rol === 'propietario' && p.suma_coeficientes"> · coeficiente total {{ coef(p.suma_coeficientes) }}</template>
        </p>
      </template>
    </article>
  </div>
</template>
