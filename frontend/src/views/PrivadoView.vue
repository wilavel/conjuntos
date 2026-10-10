<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, cop, nombreApto, fechaCorta, PERFILES } from '../api'
import ReservarZona from '../components/ReservarZona.vue'
import Icono from '../components/Icono.vue'
import { sesion as usuario, guardarSesion, cerrarSesion, actualizarPerfil } from '../sesion'

const route = useRoute()
const router = useRouter()
const datos = reactive({ email: '', clave: '' })
const error = ref('')
const entrando = ref(false)

// Qué ve cada perfil en la zona privada
const RECURSOS = [
  ['Actas y decisiones', 'Asambleas y consejo', ['superadmin', 'admin', 'propietario']],
  ['Reglamento de propiedad horizontal', 'Documento vigente', ['superadmin', 'admin', 'propietario', 'arrendatario']],
  ['Cuotas de administración', 'Estado de cuenta', ['superadmin', 'admin', 'propietario']],
  ['PQRS y solicitudes', 'Radica y sigue tus casos', ['superadmin', 'admin', 'propietario', 'arrendatario']],
  ['Reserva de zonas comunes', 'Gimnasio, terrazas, coworking y más', ['superadmin', 'admin', 'propietario', 'arrendatario']],
  ['Directorio y contactos', 'Administración y consejo', ['superadmin', 'admin', 'propietario', 'arrendatario']],
]
const recursos = computed(() => RECURSOS.filter(([, , perfiles]) => perfiles.includes(usuario.value?.rol)))

// Cuenta pendiente: puede corregir su identificación
const datosPerfil = reactive({ identificacion: '', telefono: '' })
const avisoPerfil = ref('')
watch(
  usuario,
  (u) => {
    datosPerfil.identificacion = u?.identificacion || ''
    datosPerfil.telefono = u?.telefono || ''
  },
  { immediate: true },
)

// Avisos de venta o arriendo de los apartamentos del propietario
const esPropietario = computed(() => (usuario.value?.apartamentos || []).some((a) => a.rol === 'propietario'))
const avisos = ref([])
watch(
  esPropietario,
  async (si) => {
    avisos.value = si ? await api.listar({ mias: true }).catch(() => []) : []
  },
  { immediate: true },
)
const ESTADO_AVISO = { borrador: 'Borrador', publicado: 'Publicado', vendido: 'Cerrado' }

// Visitas agendadas a los avisos de mis apartamentos
const visitas = ref([])
const cargarVisitas = async () => (visitas.value = esPropietario.value ? await api.misVisitas().catch(() => []) : [])
watch(esPropietario, cargarVisitas, { immediate: true })
const porConfirmar = (avisoId) => visitas.value.filter((v) => v.aviso.id === avisoId && v.estado === 'pendiente').length
const fechaVisita = (v) => new Date(`${v.fecha}T12:00:00`).toLocaleDateString('es-CO', { weekday: 'long', day: 'numeric', month: 'long' })
async function cambiarVisita(v, estado) {
  if (estado === 'cancelada' && !confirm(`¿Cancelar la visita de ${v.nombre}?`)) return
  try {
    await api.estadoVisita(v.id, estado)
    await cargarVisitas()
  } catch (e) {
    alert(e.message)
  }
}

// Sorteos de parqueaderos: postular mis apartamentos y ver resultados
const sorteos = ref([])
const errorSorteo = ref('')
async function cargarSorteos() {
  sorteos.value = usuario.value?.apartamentos?.length ? await api.misSorteos().catch(() => []) : []
}
watch(() => usuario.value?.apartamentos?.length, cargarSorteos, { immediate: true })

async function postular(s, a) {
  errorSorteo.value = ''
  try {
    await api.postular(s.id, a.id)
    await cargarSorteos()
  } catch (e) {
    errorSorteo.value = e.message
  }
}
async function retirar(a) {
  if (!confirm(`¿Retirar la postulación del Apto ${a.numero}?`)) return
  errorSorteo.value = ''
  try {
    await api.retirarPostulacion(a.postulacion.id)
    await cargarSorteos()
  } catch (e) {
    errorSorteo.value = e.message
  }
}

// Reservas de zonas comunes (propietarios y arrendatarios)
const tieneApartamento = computed(() => !!usuario.value?.apartamentos?.length)
const reservas = ref([])
const cargarReservas = async () => (reservas.value = tieneApartamento.value ? await api.misReservas().catch(() => []) : [])
watch(tieneApartamento, cargarReservas, { immediate: true })
onMounted(() => {
  if (route.query.reservar) setTimeout(() => document.getElementById('reservas')?.scrollIntoView({ behavior: 'smooth' }), 400)
})
const zonaPedida = typeof route.query.reservar === 'string' ? route.query.reservar : ''
const fechaReserva = (r) => new Date(`${r.fecha}T12:00:00`).toLocaleDateString('es-CO', { weekday: 'long', day: 'numeric', month: 'long' })
async function cancelarReserva(r) {
  if (!confirm(`¿Cancelar la reserva de ${r.zona.nombre}?`)) return
  try {
    await api.cancelarReserva(r.id)
    await cargarReservas()
  } catch (e) {
    alert(e.message)
  }
}

// Cambio de contraseña (la cuenta la crea la administración con una contraseña temporal)
const claves = reactive({ actual: '', nueva: '', repetir: '' })
const avisoClave = ref('')
const errorClave = ref('')
const verClave = ref(false)

async function cambiarClave() {
  avisoClave.value = ''
  errorClave.value = ''
  if (claves.nueva !== claves.repetir) {
    errorClave.value = 'Las contraseñas nuevas no coinciden'
    return
  }
  try {
    await api.cambiarMiClave(claves.actual, claves.nueva)
    Object.assign(claves, { actual: '', nueva: '', repetir: '' })
    avisoClave.value = 'Contraseña actualizada'
    verClave.value = false
  } catch (e) {
    errorClave.value = e.message
  }
}

async function guardarPerfil() {
  error.value = ''
  avisoPerfil.value = ''
  try {
    actualizarPerfil(await api.actualizarPerfil(datosPerfil))
    avisoPerfil.value = 'Datos actualizados. La administración revisará tu cuenta.'
  } catch (e) {
    error.value = e.message
  }
}

async function entrar() {
  error.value = ''
  entrando.value = true
  try {
    const sesion = await api.iniciarSesion({ email: datos.email, clave: datos.clave })
    guardarSesion(sesion)
    datos.clave = ''
    // Si venía de una pantalla de administración, vuelve a ella
    const volver = route.query.volver
    if (sesion.es_admin && typeof volver === 'string' && volver.startsWith('/')) router.push(volver)
  } catch (e) {
    error.value = e.message
  } finally {
    entrando.value = false
  }
}

const salir = cerrarSesion

// Si ya hay sesión de administración y venía de una pantalla de administración, vuelve a ella
const volverA = route.query.volver
if (usuario.value?.es_admin && typeof volverA === 'string' && volverA.startsWith('/')) router.replace(volverA)
</script>

<template>
  <div class="privado">
    <template v-if="usuario">
      <div class="privado-encabezado">
        <div>
          <span class="rotulo">Zona privada</span>
          <h1>Hola, {{ usuario.nombre }}</h1>
          <span class="perfil-insignia" :class="usuario.rol">{{ PERFILES[usuario.rol] }}</span>
        </div>
        <div class="acciones-admin">
          <RouterLink v-if="usuario.es_admin" class="boton" to="/admin">Administrar</RouterLink>
          <button class="boton secundario" type="button" @click="salir">Cerrar sesión</button>
        </div>
      </div>

      <p v-if="route.query.volver && !usuario.es_admin" class="error">
        Tu cuenta no tiene permiso de administración.
      </p>

      <div v-if="usuario.apartamentos?.length" class="privado-aptos">
        <span class="rotulo">Mis apartamentos</span>
        <ul>
          <li v-for="a in usuario.apartamentos" :key="`${a.id}-${a.rol}`">
            <strong>{{ nombreApto(a) }}</strong>
            <span>{{ a.rol === 'propietario' ? 'Propietario' : 'Arrendatario' }}</span>
          </li>
        </ul>
      </div>

      <section v-if="esPropietario" class="mis-avisos">
        <div class="personas-cabeza">
          <span class="rotulo">Mis avisos de venta y arriendo</span>
          <RouterLink class="boton" to="/nuevo">Publicar aviso <span class="flecha" aria-hidden="true">→</span></RouterLink>
        </div>
        <p v-if="!avisos.length" class="vacio">
          Aún no tienes avisos. Publica tu apartamento en venta o arriendo y aparecerá en la página de
          Venta y arriendo.
        </p>
        <div class="lista">
          <RouterLink v-for="p in avisos" :key="p.id" class="fila" :to="`/propiedades/${p.id}`">
            <img v-if="p.fotos.length" :src="p.fotos[0].url" alt="" />
            <div v-else class="sin-foto">Sin foto</div>
            <div class="datos">
              <strong>{{ p.titulo }}</strong>
              <span>{{ p.negocio === 'arriendo' ? 'Arriendo' : 'Venta' }} · {{ cop(p.precio) }}</span>
              <span v-if="p.apartamento">{{ nombreApto(p.apartamento) }}</span>
              <span v-if="porConfirmar(p.id)" class="peligro-texto"><Icono nombre="event" /> {{ porConfirmar(p.id) }} {{ porConfirmar(p.id) === 1 ? 'visita' : 'visitas' }} por confirmar</span>
            </div>
            <span class="estado" :class="p.estado">{{ ESTADO_AVISO[p.estado] }}</span>
          </RouterLink>
        </div>
      </section>

      <section v-if="tieneApartamento" id="reservas" class="mis-avisos">
        <span class="rotulo">Reservar zonas comunes</span>
        <ReservarZona :zona-inicial="zonaPedida" @reservado="cargarReservas" />
        <template v-if="reservas.length">
          <span class="rotulo mis-reservas-titulo">Mis reservas</span>
          <ul class="personas-lista">
            <li v-for="r in reservas" :key="r.id" :class="{ inactiva: r.estado === 'cancelada' }">
              <div class="persona-datos">
                <strong>{{ r.zona.nombre }} · {{ fechaReserva(r) }}</strong>
                <span><Icono nombre="schedule" /> {{ r.inicio }} a {{ r.fin }} · Apto {{ r.apartamento.numero }}</span>
              </div>
              <div class="persona-acciones">
                <span class="estado" :class="r.estado === 'activa' ? 'publicado' : 'vendido'">{{ r.estado }}</span>
                <button v-if="r.estado === 'activa'" type="button" class="enlace peligro-texto" @click="cancelarReserva(r)">Cancelar</button>
              </div>
            </li>
          </ul>
        </template>
      </section>

      <section v-if="esPropietario" class="mis-avisos">
        <span class="rotulo">Visitas agendadas</span>
        <p v-if="!visitas.length" class="vacio">No hay visitas próximas a tus avisos.</p>
        <ul class="personas-lista visitas-propietario">
          <li v-for="v in visitas" :key="v.id" :class="{ inactiva: v.estado === 'cancelada' }">
            <div class="persona-datos">
              <strong>{{ fechaVisita(v) }} · {{ v.hora }}</strong>
              <span>{{ v.nombre }} · <a :href="`tel:${v.telefono}`">{{ v.telefono }}</a> · <a :href="`mailto:${v.email}`">{{ v.email }}</a></span>
              <span v-if="v.mensaje">«{{ v.mensaje }}»</span>
              <small>Aviso: <RouterLink :to="`/propiedades/${v.aviso.id}`">{{ v.aviso.titulo }}</RouterLink></small>
            </div>
            <div class="persona-acciones">
              <span class="estado" :class="{ pendiente: 'borrador', confirmada: 'publicado', cancelada: 'vendido' }[v.estado]">{{ v.estado }}</span>
              <button v-if="v.estado === 'pendiente'" type="button" class="enlace" @click="cambiarVisita(v, 'confirmada')">Confirmar</button>
              <button v-if="v.estado !== 'cancelada'" type="button" class="enlace peligro-texto" @click="cambiarVisita(v, 'cancelada')">Cancelar</button>
            </div>
          </li>
        </ul>
      </section>

      <section v-if="sorteos.length" class="mis-avisos">
        <span class="rotulo">Sorteos de parqueaderos</span>
        <p v-if="errorSorteo" class="error">{{ errorSorteo }}</p>
        <article v-for="s in sorteos" :key="s.id" class="sorteo-tarjeta">
          <div>
            <strong>{{ s.nombre }}</strong>
            <span>
              {{ s.num_parqueaderos }} parqueaderos de {{ s.tipo === 'moto' ? 'moto' : 'carro' }} por
              {{ s.meses }} meses ({{ fechaCorta(s.inicio) }} al {{ fechaCorta(s.fin) }})
            </span>
            <span v-if="s.estado !== 'realizado'">
              {{ s.abierto ? `Postulaciones hasta el ${fechaCorta(s.cierre)}` : 'Postulaciones cerradas; pronto se realizará el sorteo' }}
            </span>
          </div>
          <ul>
            <li v-for="a in s.apartamentos" :key="a.id">
              <span>Apto {{ a.numero }}</span>
              <template v-if="s.estado === 'realizado'">
                <strong v-if="a.postulacion?.parqueadero" class="sorteo-gano"><Icono nombre="celebration" /> Parqueadero {{ a.postulacion.parqueadero }}</strong>
                <span v-else-if="a.postulacion?.excluido" class="peligro-texto">No participó: tenía saldo pendiente</span>
                <span v-else-if="a.postulacion">Lista de espera · posición {{ a.postulacion.posicion }}</span>
              </template>
              <template v-else-if="a.postulacion">
                <span class="estado publicado">postulado</span>
                <button v-if="s.abierto" type="button" class="enlace peligro-texto" @click="retirar(a)">Retirar</button>
              </template>
              <span v-else-if="s.abierto && a.deudor" class="peligro-texto">
                Tiene saldo pendiente: ponte al día con la administración para postularte
              </span>
              <button v-else-if="s.abierto" type="button" class="boton" @click="postular(s, a)">Postular</button>
            </li>
          </ul>
        </article>
      </section>

      <form v-if="usuario.rol === 'residente'" class="formulario privado-pendiente" @submit.prevent="guardarPerfil">
        <div>
          <h2>Tu cuenta está pendiente de verificación</h2>
          <p class="intro">
            La administración confirmará que tu identificación corresponde a un propietario o
            arrendatario activo del conjunto. Mientras tanto, revisa que tus datos estén correctos.
          </p>
        </div>
        <div class="grupo">
          <label>Identificación<input v-model="datosPerfil.identificacion" required maxlength="30" /></label>
          <label>Teléfono <span class="opcional">(opcional)</span><input v-model="datosPerfil.telefono" maxlength="30" /></label>
        </div>
        <p v-if="avisoPerfil">{{ avisoPerfil }}</p>
        <button class="boton secundario" type="submit">Guardar mis datos</button>
      </form>

      <ul v-if="recursos.length" class="privado-lista">
        <li v-for="[titulo, detalle] in recursos" :key="titulo">
          <strong>{{ titulo }}</strong>
          <span>{{ detalle }}</span>
        </li>
      </ul>

      <div class="privado-clave">
        <button v-if="!verClave" type="button" class="enlace" @click="verClave = true">Cambiar mi contraseña</button>
        <form v-else class="formulario" @submit.prevent="cambiarClave">
          <h2>Cambiar contraseña</h2>
          <label>Contraseña actual<input v-model="claves.actual" type="password" required autocomplete="current-password" /></label>
          <div class="grupo">
            <label>Nueva contraseña<input v-model="claves.nueva" type="password" required minlength="8" autocomplete="new-password" /></label>
            <label>Repite la nueva<input v-model="claves.repetir" type="password" required minlength="8" autocomplete="new-password" /></label>
          </div>
          <p v-if="errorClave" class="error">{{ errorClave }}</p>
          <div class="acciones">
            <button class="boton" type="submit">Guardar contraseña</button>
            <button type="button" class="enlace" @click="verClave = false">Cancelar</button>
          </div>
        </form>
        <p v-if="avisoClave">{{ avisoClave }}</p>
      </div>
    </template>

    <form v-else class="formulario" @submit.prevent="entrar">
      <div>
        <span class="rotulo">Zona privada</span>
        <h1>Ingresa a tu cuenta</h1>
        <p class="intro">
          Espacio de propietarios y residentes: actas, reglamento, cuotas, PQRS y reserva de zonas
          comunes. Si aún no tienes usuario, solicítalo a la administración del conjunto.
        </p>
      </div>
      <label>
        Correo electrónico
        <input v-model="datos.email" type="email" required autocomplete="email" />
      </label>
      <label>
        Contraseña
        <input v-model="datos.clave" type="password" required autocomplete="current-password" />
      </label>
      <p v-if="error" class="error">{{ error }}</p>
      <button class="boton" type="submit" :disabled="entrando">
        {{ entrando ? 'Ingresando…' : 'Ingresar' }} <span class="flecha" aria-hidden="true">→</span>
      </button>
    </form>
  </div>
</template>
