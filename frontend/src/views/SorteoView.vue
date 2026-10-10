<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api, nombreApto, fechaCorta } from '../api'
import Icono from '../components/Icono.vue'

const props = defineProps({ id: String })
const router = useRouter()

const sorteo = ref(null)
const apartamentos = ref([])
const error = ref('')
const realizando = ref(false)

async function cargar() {
  sorteo.value = await api.sorteo(props.id)
}
onMounted(async () => {
  try {
    await cargar()
    apartamentos.value = await api.apartamentos()
  } catch (e) {
    error.value = e.message
  }
})

const realizado = computed(() => sorteo.value?.estado === 'realizado')
const ganadores = computed(() => sorteo.value.postulaciones.filter((p) => p.parqueadero))
const espera = computed(() => sorteo.value.postulaciones.filter((p) => p.posicion && !p.parqueadero))
const excluidos = computed(() => sorteo.value.postulaciones.filter((p) => p.excluido))
const deudoresPostulados = computed(() => sorteo.value.postulaciones.filter((p) => p.apartamento.deudor).length)

async function accion(fn) {
  error.value = ''
  try {
    await fn()
  } catch (e) {
    error.value = e.message
  }
}

// ---------- lista de chequeo: marcar = inscribir, desmarcar = retirar ----------
const postulacionDe = computed(() => new Map(sorteo.value.postulaciones.map((p) => [p.apartamento.id, p])))
const guardando = ref(new Set()) // apartamentos con cambio en curso

async function alternar(a, marcado) {
  guardando.value = new Set(guardando.value).add(a.id)
  error.value = ''
  try {
    if (marcado) await api.inscribirApartamento(props.id, a.id)
    else await api.retirarPostulacion(postulacionDe.value.get(a.id).id)
    await cargar()
  } catch (e) {
    error.value = e.message
  } finally {
    const s = new Set(guardando.value)
    s.delete(a.id)
    guardando.value = s
  }
}

const alDia = computed(() => apartamentos.value.filter((a) => !a.deudor))
async function marcarTodos() {
  for (const a of alDia.value) if (!postulacionDe.value.has(a.id)) await alternar(a, true)
}
async function desmarcarTodos() {
  if (!confirm('¿Retirar a todos los apartamentos del sorteo?')) return
  for (const a of apartamentos.value) if (postulacionDe.value.has(a.id)) await alternar(a, false)
}

const realizar = () =>
  accion(async () => {
    const s = sorteo.value
    const texto =
      `¿Realizar el sorteo ahora?\n\n${s.postulaciones.length} apartamentos para ${s.parqueaderos.length} parqueaderos. ` +
      `Los parqueaderos sorteados se asignarán del ${fechaCorta(s.inicio)} al ${fechaCorta(s.fin)} ` +
      `(reemplaza su asignación actual). No se puede deshacer.`
    if (!confirm(texto)) return
    realizando.value = true
    try {
      sorteo.value = await api.realizarSorteo(props.id)
    } finally {
      realizando.value = false
    }
  })

const eliminar = () =>
  accion(async () => {
    if (!confirm('¿Eliminar este sorteo y sus postulaciones?')) return
    await api.eliminarSorteo(props.id)
    router.push('/admin/sorteos')
  })
</script>

<template>
  <RouterLink class="articulo-volver" to="/admin/sorteos">← Todos los sorteos</RouterLink>
  <p v-if="error" class="error">{{ error }}</p>
  <template v-if="sorteo">
    <div class="encabezado titulo-admin">
      <div>
        <h1>{{ sorteo.nombre }}</h1>
        <p class="intro-admin">
          {{ sorteo.tipo === 'moto' ? 'Motos' : 'Carros' }} · asignación por {{ sorteo.meses }} meses, del
          {{ fechaCorta(sorteo.inicio) }} al {{ fechaCorta(sorteo.fin) }} · postulaciones hasta el
          {{ fechaCorta(sorteo.cierre) }}
        </p>
      </div>
      <button v-if="!realizado" type="button" class="boton peligro" @click="eliminar">Eliminar</button>
    </div>

    <dl class="resumen-parq">
      <div><dt>Parqueaderos</dt><dd>{{ sorteo.parqueaderos.length }}</dd></div>
      <div><dt>Postulados</dt><dd>{{ sorteo.postulaciones.length }}</dd></div>
      <div>
        <dt>Estado</dt>
        <dd class="resumen-texto">{{ realizado ? 'Realizado' : sorteo.abierto ? 'Postulaciones abiertas' : 'Postulaciones cerradas' }}</dd>
      </div>
    </dl>

    <!-- Resultados -->
    <template v-if="realizado">
      <div class="aviso-ok">
        Sorteo realizado el {{ new Date(sorteo.realizado_en).toLocaleString('es-CO') }} · semilla de
        constancia: <code>{{ sorteo.semilla }}</code> (permite reproducir el mismo orden).
      </div>
      <h2>Parqueaderos asignados</h2>
      <ul class="personas-lista">
        <li v-for="p in ganadores" :key="p.id">
          <div class="persona-datos">
            <strong>{{ p.posicion }}. {{ nombreApto(p.apartamento) }}</strong>
            <span>Parqueadero {{ p.parqueadero }} · {{ fechaCorta(sorteo.inicio) }} al {{ fechaCorta(sorteo.fin) }}</span>
          </div>
          <span class="perfil-insignia propietario"><Icono nombre="directions_car" /> {{ p.parqueadero }}</span>
        </li>
      </ul>
      <template v-if="espera.length">
        <h2>Lista de espera</h2>
        <p class="opcional">Si se libera un parqueadero, asígnalo en este orden desde Parqueaderos.</p>
        <ul class="personas-lista">
          <li v-for="p in espera" :key="p.id">
            <div class="persona-datos"><strong>{{ p.posicion }}. {{ nombreApto(p.apartamento) }}</strong></div>
            <span class="estado borrador">en espera</span>
          </li>
        </ul>
      </template>
      <template v-if="excluidos.length">
        <h2>Excluidos por mora</h2>
        <ul class="personas-lista">
          <li v-for="p in excluidos" :key="p.id">
            <div class="persona-datos"><strong>{{ nombreApto(p.apartamento) }}</strong><span>Tenía saldo pendiente al momento del sorteo</span></div>
            <span class="perfil-insignia deudor">Excluido</span>
          </li>
        </ul>
      </template>
    </template>

    <!-- Postulaciones (antes del sorteo) -->
    <template v-else>
      <div class="personas-cabeza">
        <h2>Apartamentos postulados</h2>
        <button type="button" class="boton" :disabled="!sorteo.postulaciones.length || realizando" @click="realizar">
          {{ realizando ? 'Sorteando…' : 'Realizar sorteo' }}
        </button>
      </div>
      <p v-if="deudoresPostulados" class="error">
        {{ deudoresPostulados }} de los postulados figura{{ deudoresPostulados === 1 ? '' : 'n' }} como deudor{{ deudoresPostulados === 1 ? '' : 'es' }}:
        si siguen así al realizar el sorteo, no participarán.
      </p>
      <p class="opcional">
        {{ sorteo.postulaciones.length }} de {{ apartamentos.length }} apartamentos postulados. Marca o
        desmarca para inscribir o retirar; los residentes también se postulan desde su zona privada.
      </p>
      <div class="acciones">
        <button type="button" class="enlace" @click="marcarTodos">Marcar todos los que están al día</button>
        <button v-if="sorteo.postulaciones.length" type="button" class="enlace peligro-texto" @click="desmarcarTodos">Desmarcar todos</button>
      </div>
      <ul class="chequeo-aptos">
        <li v-for="a in apartamentos" :key="a.id" :class="{ marcado: postulacionDe.has(a.id), deudor: a.deudor }">
          <label>
            <input
              type="checkbox"
              :checked="postulacionDe.has(a.id)"
              :disabled="guardando.has(a.id) || (a.deudor && !postulacionDe.has(a.id))"
              @change="alternar(a, $event.target.checked)"
            />
            <strong>{{ nombreApto(a) }}</strong>
          </label>
          <span v-if="a.deudor" class="perfil-insignia deudor">
            {{ postulacionDe.has(a.id) ? 'Deudor: quedará excluido' : 'Deudor' }}
          </span>
          <small v-else-if="postulacionDe.has(a.id)">
            Postulado el {{ new Date(postulacionDe.get(a.id).creado).toLocaleDateString('es-CO') }}
          </small>
        </li>
      </ul>
    </template>

    <h2>Parqueaderos en el sorteo</h2>
    <p class="sorteo-cupos-lista">
      <span v-for="p in sorteo.parqueaderos" :key="p.id" class="perfil-insignia">{{ p.numero }}</span>
    </p>
  </template>
</template>
