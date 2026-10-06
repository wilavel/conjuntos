<script setup>
import { reactive, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, cop, nombreApto, fechaLarga } from '../api'
import PersonaCampos from '../components/PersonaCampos.vue'
import InvitacionesAviso from '../components/InvitacionesAviso.vue'
import { ultimasInvitaciones } from '../invitaciones'

const props = defineProps({ id: String })
const router = useRouter()
const route = useRoute()

const apto = ref(null)
const datos = reactive({ numero: '', piso: '', area_m2: '', habitaciones: 0, banos: 0, coeficiente: '', deudor: false })
const error = ref('')
const aviso = ref('')

const ROLES = [
  { rol: 'propietario', lista: 'propietarios', titulo: 'Propietarios', singular: 'propietario' },
  { rol: 'arrendatario', lista: 'arrendatarios', titulo: 'Arrendatarios', singular: 'arrendatario' },
]
const nuevaPersona = () => ({ nombre: '', identificacion: '', telefono: '', email: '' })
const nuevas = reactive({ propietario: null, arrendatario: null }) // formulario de alta abierto por rol
const editando = ref(null) // id de la persona en edición
const borrador = reactive(nuevaPersona())
// Accesos creados (al crear el apartamento o al agregar personas)
const invitaciones = ref(ultimasInvitaciones.value)
ultimasInvitaciones.value = []

function mostrar(a) {
  apto.value = a
  for (const k of Object.keys(datos)) datos[k] = a[k] ?? ''
}

// Desde el listado: ?agregar=propietario|arrendatario abre directo el formulario
const avisos = ref([])
onMounted(async () => {
  await accion(async () => mostrar(await api.apartamento(props.id)))
  const rol = route.query.agregar
  if (rol === 'propietario' || rol === 'arrendatario') {
    nuevas[rol] = nuevaPersona()
    setTimeout(() => document.getElementById(`personas-${rol}`)?.scrollIntoView({ behavior: 'smooth' }), 50)
  }
  avisos.value = await api.listar({ apartamentoId: props.id }).catch(() => [])
})
// Parqueaderos: asignar uno libre de residentes o liberar los asignados
const libres = ref([])
const parqElegido = ref('')
async function cargarLibres() {
  const todos = await api.parqueaderos().catch(() => [])
  libres.value = todos.filter((p) => p.uso === 'residente' && !p.apartamento_id)
}
onMounted(cargarLibres)

const asignarParq = () =>
  accion(async () => {
    const p = libres.value.find((x) => x.id === Number(parqElegido.value))
    if (!p) return
    await api.actualizarParqueadero(p.id, { ...p, apartamento_id: apto.value.id, asignado_hasta: null })
    parqElegido.value = ''
    mostrar(await api.apartamento(props.id))
    await cargarLibres()
  }, 'Parqueadero asignado')

const liberarParq = (p) =>
  accion(async () => {
    if (!confirm(`¿Liberar el parqueadero ${p.numero}?`)) return
    await api.actualizarParqueadero(p.id, { ...p, apartamento_id: null, asignado_hasta: null })
    mostrar(await api.apartamento(props.id))
    await cargarLibres()
  })

const ESTADO_AVISO = { borrador: 'Borrador', publicado: 'Publicado', vendido: 'Cerrado' }

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

// Activos primero; dentro de cada grupo, los más recientes arriba
const ordenar = (lista) => [...lista].sort((a, b) => b.activo - a.activo || b.id - a.id)

const guardarDatos = () =>
  accion(async () => {
    mostrar(
      await api.actualizarApartamento(props.id, {
        ...datos,
        piso: datos.piso === '' ? null : Number(datos.piso),
        area_m2: datos.area_m2 === '' ? null : Number(datos.area_m2),
        habitaciones: Number(datos.habitaciones) || 0,
        banos: Number(datos.banos) || 0,
        coeficiente: datos.coeficiente === '' || datos.coeficiente === null ? null : Number(datos.coeficiente),
      }),
    )
  }, 'Datos guardados')

const agregar = (rol) =>
  accion(async () => {
    const a = await api.agregarPersona(props.id, { ...nuevas[rol], rol })
    mostrar(a)
    invitaciones.value = a.invitaciones || []
    nuevas[rol] = null
  })

const datosPersona = (p) => ({
  nombre: p.nombre, identificacion: p.identificacion, telefono: p.telefono, email: p.email, activo: p.activo,
})

const cambiarEstado = (p) =>
  accion(async () => mostrar(await api.actualizarPersona(p.id, { ...datosPersona(p), activo: !p.activo })))

function editar(p) {
  editando.value = p.id
  Object.assign(borrador, datosPersona(p))
}

const guardarPersona = (p) =>
  accion(async () => {
    mostrar(await api.actualizarPersona(p.id, { ...borrador, activo: p.activo }))
    editando.value = null
  })

const enviarAcceso = (p) =>
  accion(async () => {
    invitaciones.value = [await api.invitarPersona(p.id)]
  })

const borrarPersona = (p) =>
  accion(async () => {
    if (!confirm(`¿Borrar a ${p.nombre}? Si solo dejó de ser ${p.rol}, mejor márcalo como inactivo para conservar el historial.`)) return
    mostrar(await api.eliminarPersona(p.id))
  })

const eliminar = () =>
  accion(async () => {
    if (!confirm('¿Eliminar este apartamento con todos sus propietarios y arrendatarios?')) return
    await api.eliminarApartamento(props.id)
    router.push('/admin/apartamentos')
  })
</script>

<template>
  <RouterLink class="articulo-volver" to="/admin/apartamentos">← Todos los apartamentos</RouterLink>
  <p v-if="!apto && !error">Cargando…</p>
  <p v-if="error" class="error">{{ error }}</p>

  <template v-if="apto">
    <div class="encabezado titulo-admin">
      <h1>{{ nombreApto(apto) }} <span v-if="apto.deudor" class="perfil-insignia deudor">Deudor</span></h1>
      <button class="boton peligro" type="button" @click="eliminar">Eliminar apartamento</button>
    </div>

    <InvitacionesAviso :invitaciones="invitaciones" @cerrar="invitaciones = []" />

    <form class="formulario" @submit.prevent="guardarDatos">
      <div class="grupo">
        <label>Número<input v-model="datos.numero" required maxlength="20" /></label>
        <label>Piso<input v-model.number="datos.piso" type="number" min="0" /></label>
        <label>Área (m²)<input v-model.number="datos.area_m2" type="number" min="0" step="any" /></label>
      </div>
      <div class="grupo">
        <label>Habitaciones<input v-model.number="datos.habitaciones" type="number" min="0" /></label>
        <label>Baños<input v-model.number="datos.banos" type="number" min="0" /></label>
        <label>Coeficiente de copropiedad (%)<input v-model.number="datos.coeficiente" type="number" min="0" max="100" step="any" placeholder="0,8523" /></label>
      </div>
      <label class="check">
        <input v-model="datos.deudor" type="checkbox" />
        Deudor: tiene saldo pendiente con la administración (no puede participar en sorteos)
      </label>
      <div class="acciones">
        <button class="boton secundario" type="submit">Guardar datos</button>
        <span v-if="aviso">{{ aviso }}</span>
      </div>
    </form>

    <section v-for="r in ROLES" :id="`personas-${r.rol}`" :key="r.rol" class="personas">
      <div class="personas-cabeza">
        <h2>{{ r.titulo }}</h2>
        <button v-if="!nuevas[r.rol]" type="button" class="boton secundario" @click="nuevas[r.rol] = nuevaPersona()">
          + Agregar {{ r.singular }}
        </button>
      </div>

      <form v-if="nuevas[r.rol]" class="formulario" @submit.prevent="agregar(r.rol)">
        <PersonaCampos :persona="nuevas[r.rol]" />
        <div class="acciones">
          <button class="boton" type="submit">Agregar</button>
          <button type="button" class="enlace" @click="nuevas[r.rol] = null">Cancelar</button>
        </div>
      </form>

      <p v-if="!apto[r.lista].length" class="vacio">
        {{ r.rol === 'arrendatario' ? 'Sin arrendatarios: lo habita o lo administra el propietario.' : 'Sin propietarios.' }}
      </p>

      <ul class="personas-lista">
        <li v-for="p in ordenar(apto[r.lista])" :key="p.id" :class="{ inactiva: !p.activo }">
          <form v-if="editando === p.id" class="persona-edicion" @submit.prevent="guardarPersona(p)">
            <PersonaCampos :persona="borrador" />
            <div class="acciones">
              <button class="boton" type="submit">Guardar</button>
              <button type="button" class="enlace" @click="editando = null">Cancelar</button>
            </div>
          </form>
          <template v-else>
            <div class="persona-datos">
              <strong>{{ p.nombre }}</strong>
              <span>{{ p.identificacion }}</span>
              <span v-if="p.telefono || p.email">{{ [p.telefono, p.email].filter(Boolean).join(' · ') }}</span>
              <small>Registrado el {{ fechaLarga(p.creado) }}</small>
            </div>
            <div class="persona-acciones">
              <span class="estado" :class="p.activo ? 'publicado' : 'vendido'">{{ p.activo ? 'activo' : 'inactivo' }}</span>
              <button type="button" class="enlace" @click="cambiarEstado(p)">{{ p.activo ? 'Inactivar' : 'Activar' }}</button>
              <button type="button" class="enlace" @click="editar(p)">Editar</button>
              <button v-if="p.activo && p.email" type="button" class="enlace" @click="enviarAcceso(p)">Enviar acceso</button>
              <button type="button" class="enlace peligro-texto" @click="borrarPersona(p)">Borrar</button>
            </div>
          </template>
        </li>
      </ul>
    </section>

    <section class="personas">
      <div class="personas-cabeza">
        <h2>Parqueaderos</h2>
        <RouterLink class="enlace" to="/admin/parqueaderos">Ver todos los parqueaderos</RouterLink>
      </div>
      <p v-if="!apto.parqueaderos_asignados.length" class="vacio">Este apartamento no tiene parqueaderos asignados.</p>
      <ul class="personas-lista">
        <li v-for="p in apto.parqueaderos_asignados" :key="p.id">
          <div class="persona-datos">
            <strong>{{ p.tipo === 'moto' ? '🏍️' : '🚗' }} {{ p.numero }}</strong>
            <span>{{ p.tipo === 'moto' ? 'Moto' : 'Carro' }}<template v-if="p.ubicacion"> · {{ p.ubicacion }}</template></span>
          </div>
          <button type="button" class="enlace peligro-texto" @click="liberarParq(p)">Liberar</button>
        </li>
      </ul>
      <form v-if="libres.length" class="subida" @submit.prevent="asignarParq">
        <select v-model="parqElegido" required aria-label="Parqueadero libre">
          <option value="" disabled>Elige un parqueadero libre de residentes</option>
          <option v-for="p in libres" :key="p.id" :value="p.id">
            {{ p.numero }} · {{ p.tipo === 'moto' ? 'moto' : 'carro' }}<template v-if="p.ubicacion"> · {{ p.ubicacion }}</template>
          </option>
        </select>
        <button class="boton secundario" type="submit">Asignar</button>
      </form>
      <p v-else class="opcional">No hay parqueaderos libres de residentes. Créalos en <RouterLink to="/admin/parqueaderos">Parqueaderos</RouterLink>.</p>
    </section>

    <section class="personas">
      <div class="personas-cabeza">
        <h2>Avisos de venta y arriendo</h2>
        <RouterLink class="boton secundario" :to="{ path: '/nuevo', query: { apartamento: apto.id } }">+ Publicar aviso</RouterLink>
      </div>
      <p v-if="!avisos.length" class="vacio">Este apartamento no tiene avisos.</p>
      <div class="lista">
        <RouterLink v-for="p in avisos" :key="p.id" class="fila" :to="`/propiedades/${p.id}`">
          <img v-if="p.fotos.length" :src="p.fotos[0].url" alt="" />
          <div v-else class="sin-foto">Sin foto</div>
          <div class="datos">
            <strong>{{ p.titulo }}</strong>
            <span>{{ p.negocio === 'arriendo' ? 'Arriendo' : 'Venta' }} · {{ cop(p.precio) }}</span>
          </div>
          <span class="estado" :class="p.estado">{{ ESTADO_AVISO[p.estado] }}</span>
        </RouterLink>
      </div>
    </section>
  </template>
</template>
