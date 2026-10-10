<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { api, nombreApto, fechaCorta } from '../api'
import AdminNav from '../components/AdminNav.vue'
import Icono from '../components/Icono.vue'

const parqueaderos = ref([])
const apartamentos = ref([])
const cargando = ref(true)
const error = ref('')
const aviso = ref('')

onMounted(async () => {
  try {
    ;[parqueaderos.value, apartamentos.value] = await Promise.all([api.parqueaderos(), api.apartamentos()])
  } catch (e) {
    error.value = e.message
  } finally {
    cargando.value = false
  }
})

const TIPOS = { carro: 'Carro', moto: 'Moto' }
const USOS = { residente: 'Residentes', visitante: 'Visitantes' }

// ---------- resumen ----------
const cuenta = (fn) => parqueaderos.value.filter(fn).length
const resumen = computed(() => [
  ['Total', cuenta(() => true)],
  ['Carros', cuenta((p) => p.tipo === 'carro')],
  ['Motos', cuenta((p) => p.tipo === 'moto')],
  ['Residentes', cuenta((p) => p.uso === 'residente')],
  ['Visitantes', cuenta((p) => p.uso === 'visitante')],
  ['Asignados', cuenta((p) => p.apartamento_id)],
  ['Libres (residentes)', cuenta((p) => p.uso === 'residente' && !p.apartamento_id)],
])

// ---------- filtros ----------
const f = reactive({ texto: '', tipo: '', uso: '', estado: '' })
const filtrados = computed(() => {
  const q = f.texto.trim().toLowerCase()
  return parqueaderos.value.filter((p) => {
    if (f.tipo && p.tipo !== f.tipo) return false
    if (f.uso && p.uso !== f.uso) return false
    if (f.estado === 'asignado' && !p.apartamento_id) return false
    if (f.estado === 'libre' && (p.apartamento_id || p.uso !== 'residente')) return false
    if (q && ![p.numero, p.ubicacion, p.apartamento && nombreApto(p.apartamento)].join(' ').toLowerCase().includes(q)) return false
    return true
  })
})

// ---------- crear ----------
const vacio = () => ({ numero: '', tipo: 'carro', uso: 'residente', ubicacion: '', observaciones: '', apartamento_id: null })
const nuevo = ref(null)
const lote = ref(null)

async function accion(fn, mensaje = '') {
  error.value = ''
  aviso.value = ''
  try {
    await fn()
    aviso.value = mensaje
    return true
  } catch (e) {
    error.value = e.message
    return false
  }
}
const recargar = async () => (parqueaderos.value = await api.parqueaderos())

const crear = () =>
  accion(async () => {
    await api.crearParqueadero(nuevo.value)
    nuevo.value = null
    await recargar()
  }, 'Parqueadero creado')

const crearLote = () =>
  accion(async () => {
    const r = await api.crearParqueaderosLote(lote.value)
    aviso.value = `Se crearon ${r.creados} parqueaderos` + (r.omitidos.length ? ` (ya existían: ${r.omitidos.join(', ')})` : '')
    lote.value = null
    await recargar()
  }, '')

// ---------- editar / asignar / eliminar ----------
const editando = ref(null)
const borrador = reactive(vacio())
function editar(p) {
  editando.value = p.id
  Object.assign(borrador, { ...p })
}
const guardar = (p) =>
  accion(async () => {
    const datos = { ...borrador }
    if (datos.uso !== 'residente') datos.apartamento_id = null
    if (!datos.asignado_hasta) datos.asignado_hasta = null
    const r = await api.actualizarParqueadero(p.id, datos)
    parqueaderos.value = parqueaderos.value.map((x) => (x.id === p.id ? r : x))
    editando.value = null
  }, 'Cambios guardados')

const asignar = (p, aptoId) =>
  accion(async () => {
    // Asignación manual: nueva y sin vencimiento (se puede fijar con Editar)
    const r = await api.actualizarParqueadero(p.id, { ...p, apartamento_id: aptoId || null, asignado_hasta: null })
    parqueaderos.value = parqueaderos.value.map((x) => (x.id === p.id ? r : x))
  })

const eliminar = (p) =>
  accion(async () => {
    if (!confirm(`¿Eliminar el parqueadero ${p.numero}?`)) return
    await api.eliminarParqueadero(p.id)
    parqueaderos.value = parqueaderos.value.filter((x) => x.id !== p.id)
  })
</script>

<template>
  <AdminNav />
  <div class="encabezado titulo-admin">
    <h1>Parqueaderos</h1>
    <div class="acciones-admin">
      <button v-if="!nuevo && !lote" type="button" class="boton secundario" @click="lote = { prefijo: 'P-', desde: 1, hasta: 10, tipo: 'carro', uso: 'residente', ubicacion: '' }">Crear varios</button>
      <button v-if="!nuevo && !lote" type="button" class="boton" @click="nuevo = vacio()">Nuevo parqueadero</button>
    </div>
  </div>

  <dl class="resumen-parq">
    <div v-for="[etiqueta, valor] in resumen" :key="etiqueta">
      <dt>{{ etiqueta }}</dt>
      <dd>{{ cargando ? '—' : valor }}</dd>
    </div>
  </dl>

  <!-- Nuevo parqueadero -->
  <form v-if="nuevo" class="formulario usuario-nuevo" @submit.prevent="crear">
    <h2>Nuevo parqueadero</h2>
    <div class="grupo">
      <label>Número<input v-model="nuevo.numero" required maxlength="20" placeholder="P-12" /></label>
      <label>Tipo<select v-model="nuevo.tipo"><option value="carro">Carro</option><option value="moto">Moto</option></select></label>
      <label>Uso<select v-model="nuevo.uso"><option value="residente">Residentes</option><option value="visitante">Visitantes</option></select></label>
      <label>Ubicación <span class="opcional">(opcional)</span><input v-model="nuevo.ubicacion" maxlength="60" placeholder="Sótano 1" /></label>
    </div>
    <label v-if="nuevo.uso === 'residente'">
      Asignar a <span class="opcional">(opcional)</span>
      <select v-model="nuevo.apartamento_id">
        <option :value="null">Sin asignar</option>
        <option v-for="a in apartamentos" :key="a.id" :value="a.id">{{ nombreApto(a) }}</option>
      </select>
    </label>
    <div class="acciones">
      <button class="boton" type="submit">Crear</button>
      <button type="button" class="enlace" @click="nuevo = null">Cancelar</button>
    </div>
  </form>

  <!-- Crear varios -->
  <form v-if="lote" class="formulario usuario-nuevo" @submit.prevent="crearLote">
    <h2>Crear varios parqueaderos</h2>
    <p class="opcional">
      Ejemplo: prefijo «P-» del 1 al 40 crea P-1, P-2 … P-40. Los números que ya existan se omiten.
    </p>
    <div class="grupo">
      <label>Prefijo<input v-model="lote.prefijo" maxlength="10" placeholder="P-" /></label>
      <label>Desde<input v-model.number="lote.desde" type="number" min="0" required /></label>
      <label>Hasta<input v-model.number="lote.hasta" type="number" min="0" required /></label>
    </div>
    <div class="grupo">
      <label>Tipo<select v-model="lote.tipo"><option value="carro">Carro</option><option value="moto">Moto</option></select></label>
      <label>Uso<select v-model="lote.uso"><option value="residente">Residentes</option><option value="visitante">Visitantes</option></select></label>
      <label>Ubicación <span class="opcional">(opcional)</span><input v-model="lote.ubicacion" maxlength="60" placeholder="Sótano 1" /></label>
    </div>
    <p class="opcional">Se crearán {{ Math.max(0, lote.hasta - lote.desde + 1) }}: {{ lote.prefijo }}{{ lote.desde }} … {{ lote.prefijo }}{{ lote.hasta }}</p>
    <div class="acciones">
      <button class="boton" type="submit">Crear parqueaderos</button>
      <button type="button" class="enlace" @click="lote = null">Cancelar</button>
    </div>
  </form>

  <p v-if="aviso" class="aviso-ok">{{ aviso }}</p>
  <p v-if="error" class="error">{{ error }}</p>

  <!-- Filtros -->
  <div v-if="parqueaderos.length" class="filtros-parq">
    <input v-model="f.texto" type="search" placeholder="Buscar número, ubicación o apartamento" aria-label="Buscar" />
    <select v-model="f.tipo" aria-label="Tipo"><option value="">Carros y motos</option><option value="carro">Carros</option><option value="moto">Motos</option></select>
    <select v-model="f.uso" aria-label="Uso"><option value="">Residentes y visitantes</option><option value="residente">Residentes</option><option value="visitante">Visitantes</option></select>
    <select v-model="f.estado" aria-label="Estado"><option value="">Todos</option><option value="asignado">Asignados</option><option value="libre">Libres</option></select>
  </div>

  <p v-if="cargando">Cargando…</p>
  <p v-else-if="!parqueaderos.length" class="vacio">
    Aún no hay parqueaderos. Usa <strong>Crear varios</strong> para registrarlos todos de una vez.
  </p>
  <p v-else-if="!filtrados.length" class="vacio">Ningún parqueadero coincide con los filtros.</p>

  <ul class="personas-lista">
    <li v-for="p in filtrados" :key="p.id">
      <form v-if="editando === p.id" class="persona-edicion" @submit.prevent="guardar(p)">
        <div class="grupo">
          <label>Número<input v-model="borrador.numero" required maxlength="20" /></label>
          <label>Tipo<select v-model="borrador.tipo"><option value="carro">Carro</option><option value="moto">Moto</option></select></label>
          <label>Uso<select v-model="borrador.uso"><option value="residente">Residentes</option><option value="visitante">Visitantes</option></select></label>
          <label>Ubicación<input v-model="borrador.ubicacion" maxlength="60" /></label>
        </div>
        <div class="grupo">
          <label>Observaciones<input v-model="borrador.observaciones" maxlength="255" /></label>
          <label v-if="borrador.apartamento_id">Asignado hasta <span class="opcional">(vacío = sin vencimiento)</span><input v-model="borrador.asignado_hasta" type="date" /></label>
        </div>
        <div class="acciones">
          <button class="boton" type="submit">Guardar</button>
          <button type="button" class="enlace" @click="editando = null">Cancelar</button>
        </div>
      </form>
      <template v-else>
        <div class="persona-datos">
          <strong><Icono :nombre="p.tipo === 'moto' ? 'two_wheeler' : 'directions_car'" /> {{ p.numero }}</strong>
          <span>{{ TIPOS[p.tipo] }} · {{ USOS[p.uso] }}<template v-if="p.ubicacion"> · {{ p.ubicacion }}</template></span>
          <span v-if="p.apartamento_id && p.asignado_hasta">Asignado hasta el {{ fechaCorta(p.asignado_hasta) }}</span>
          <span v-if="p.observaciones">{{ p.observaciones }}</span>
        </div>
        <div class="persona-acciones">
          <select v-if="p.uso === 'residente'" class="parq-asignar" :value="p.apartamento_id ?? ''" aria-label="Apartamento asignado" @change="asignar(p, Number($event.target.value) || null)">
            <option value="">Sin asignar</option>
            <option v-for="a in apartamentos" :key="a.id" :value="a.id">{{ nombreApto(a) }}</option>
          </select>
          <span v-else class="perfil-insignia">Visitantes</span>
          <button type="button" class="enlace" @click="editar(p)">Editar</button>
          <button type="button" class="enlace peligro-texto" @click="eliminar(p)">Eliminar</button>
        </div>
      </template>
    </li>
  </ul>
</template>
