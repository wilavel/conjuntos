<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { api, nombreApto, PERFILES } from '../api'
import { sesion, esSuperadmin } from '../sesion'
import AdminNav from '../components/AdminNav.vue'
import InvitacionesAviso from '../components/InvitacionesAviso.vue'

const usuarios = ref([])
const cargando = ref(true)
const error = ref('')
const filtro = ref('pendientes')

onMounted(async () => {
  try {
    usuarios.value = await api.usuarios()
  } catch (e) {
    error.value = e.message
  } finally {
    cargando.value = false
  }
})

// Pendiente = cuenta de residente sin verificar
const pendiente = (u) => !u.rol_staff && !u.verificado
const FILTROS = {
  pendientes: ['Por verificar', pendiente],
  residentes: ['Residentes', (u) => !u.rol_staff && u.verificado],
  staff: ['Administración', (u) => !!u.rol_staff],
  todos: ['Todos', () => true],
}
const lista = computed(() => usuarios.value.filter(FILTROS[filtro.value][1]))
const cuenta = (clave) => usuarios.value.filter(FILTROS[clave][1]).length

function reemplazar(u) {
  usuarios.value = usuarios.value.map((x) => (x.id === u.id ? u : x))
}

async function accion(fn) {
  error.value = ''
  try {
    reemplazar(await fn())
  } catch (e) {
    error.value = e.message
  }
}

// Alta de cuentas: solo la administración crea usuarios
const vacio = () => ({ nombre: '', email: '', identificacion: '', telefono: '', clave: '' })
const nuevo = ref(null)
const aviso = ref('')

async function crear() {
  error.value = ''
  aviso.value = ''
  try {
    const u = await api.crearUsuario(nuevo.value)
    usuarios.value = [u, ...usuarios.value]
    aviso.value = `Cuenta creada para ${u.email}. Entrégale la contraseña temporal; podrá cambiarla en la zona privada.`
    nuevo.value = null
    filtro.value = 'todos'
  } catch (e) {
    error.value = e.message
  }
}

function restablecer(u) {
  const clave = prompt(`Nueva contraseña temporal para ${u.nombre} (mínimo 8 caracteres):`)
  if (!clave) return
  accion(async () => {
    const r = await api.restablecerClave(u.id, clave)
    aviso.value = `Contraseña de ${u.nombre} actualizada.`
    return r
  })
}
// Enlace para que la persona cree una contraseña nueva (por correo o para compartir)
const invitaciones = ref([])
async function enviarAcceso(u) {
  error.value = ''
  try {
    invitaciones.value = [await api.invitarUsuario(u.id)]
  } catch (e) {
    error.value = e.message
  }
}

// Un administrador no cambia contraseñas de otras cuentas de la administración
const puedeRestablecer = (u) => esSuperadmin.value || !u.rol_staff || u.id === sesion.value?.id

const verificar = (u, valor) => accion(() => api.verificarUsuario(u.id, valor))
const cambiarRol = (u, rol) => {
  const texto = rol ? `¿Dar perfil de administrador a ${u.nombre}?` : `¿Quitar el perfil de administrador a ${u.nombre}?`
  if (confirm(texto)) accion(() => api.cambiarRol(u.id, rol))
}
</script>

<template>
  <AdminNav />
  <div class="encabezado titulo-admin">
    <h1>Usuarios</h1>
    <button v-if="!nuevo" type="button" class="boton" @click="nuevo = vacio()">Nuevo usuario</button>
  </div>

  <form v-if="nuevo" class="formulario usuario-nuevo" @submit.prevent="crear">
    <h2>Nueva cuenta</h2>
    <div class="grupo">
      <label>Nombre completo<input v-model="nuevo.nombre" required maxlength="100" /></label>
      <label>Correo<input v-model="nuevo.email" type="email" required maxlength="255" /></label>
    </div>
    <div class="grupo">
      <label>Identificación<input v-model="nuevo.identificacion" required maxlength="30" placeholder="1020304050" /></label>
      <label>Teléfono <span class="opcional">(opcional)</span><input v-model="nuevo.telefono" maxlength="30" /></label>
      <label>Contraseña temporal<input v-model="nuevo.clave" required minlength="8" maxlength="128" autocomplete="new-password" /></label>
    </div>
    <p class="opcional">
      Si la identificación figura activa en un apartamento, la persona entra directamente como
      propietario o arrendatario.
    </p>
    <div class="acciones">
      <button class="boton" type="submit">Crear cuenta</button>
      <button type="button" class="enlace" @click="nuevo = null">Cancelar</button>
    </div>
  </form>
  <p v-if="aviso" class="aviso-ok">{{ aviso }}</p>
  <InvitacionesAviso :invitaciones="invitaciones" @cerrar="invitaciones = []" />
  <p class="intro-admin">
    Al verificar una cuenta, la persona recibe el perfil de <strong>propietario</strong> o
    <strong>arrendatario</strong> según los apartamentos donde figura <em>activa</em> con la misma
    identificación. Las cuentas que crea la administración quedan verificadas desde el inicio.
  </p>

  <nav class="filtros barra-filtros">
    <a v-for="(f, clave) in FILTROS" :key="clave" href="#" :class="{ activo: filtro === clave }" @click.prevent="filtro = clave">
      {{ f[0] }} ({{ cuenta(clave) }})
    </a>
  </nav>

  <p v-if="error" class="error">{{ error }}</p>
  <p v-if="cargando">Cargando…</p>
  <p v-else-if="!lista.length" class="vacio">No hay usuarios en este grupo.</p>

  <ul class="personas-lista">
    <li v-for="u in lista" :key="u.id">
      <div class="persona-datos">
        <strong>{{ u.nombre }}</strong>
        <span>{{ u.email }}<template v-if="u.telefono"> · {{ u.telefono }}</template></span>
        <span>Identificación: {{ u.identificacion || 'sin registrar' }}</span>
        <span v-if="u.coincidencias.length">
          Figura en: {{ u.coincidencias.map((a) => `${nombreApto(a)} (${a.rol})`).join(', ') }}
        </span>
        <span v-else-if="!u.rol_staff">No figura activa en ningún apartamento.</span>
      </div>
      <div class="persona-acciones">
        <span class="perfil-insignia" :class="u.rol">{{ PERFILES[u.rol] }}</span>
        <template v-if="!u.rol_staff">
          <button v-if="!u.verificado" type="button" class="boton" :disabled="!u.coincidencias.length" @click="verificar(u, true)">
            Verificar
          </button>
          <button v-else type="button" class="enlace" @click="verificar(u, false)">Quitar verificación</button>
        </template>
        <button v-if="puedeRestablecer(u)" type="button" class="enlace" @click="enviarAcceso(u)">Enviar acceso</button>
        <button v-if="puedeRestablecer(u)" type="button" class="enlace" @click="restablecer(u)">Cambiar contraseña</button>
        <template v-if="esSuperadmin && u.rol !== 'superadmin'">
          <button v-if="u.rol_staff !== 'admin'" type="button" class="enlace" @click="cambiarRol(u, 'admin')">Hacer administrador</button>
          <button v-else type="button" class="enlace peligro-texto" @click="cambiarRol(u, '')">Quitar administrador</button>
        </template>
      </div>
    </li>
  </ul>
</template>
