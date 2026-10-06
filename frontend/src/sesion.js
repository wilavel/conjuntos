import { ref, computed } from 'vue'

// Sesión guardada en el navegador: datos del usuario y el token firmado por el backend.
const CLAVE = 'trend-sesion'

function leer() {
  try {
    const s = JSON.parse(localStorage.getItem(CLAVE) || 'null')
    return s?.token ? s : null // las sesiones antiguas sin token ya no sirven
  } catch {
    return null
  }
}

export const sesion = ref(leer())
export const rol = computed(() => sesion.value?.rol || '')
export const esAdmin = computed(() => ['superadmin', 'admin'].includes(rol.value))
export const esSuperadmin = computed(() => rol.value === 'superadmin')
// Puede publicar avisos: administración o propietario activo de algún apartamento
export const puedePublicar = computed(
  () => esAdmin.value || (sesion.value?.apartamentos || []).some((a) => a.rol === 'propietario'),
)

export function guardarSesion(datos) {
  sesion.value = datos
  try {
    localStorage.setItem(CLAVE, JSON.stringify(datos))
  } catch {
    /* sin almacenamiento la sesión dura hasta recargar */
  }
}

// Actualiza el perfil sin tocar el token (el rol puede cambiar con el tiempo).
export function actualizarPerfil(datos) {
  if (sesion.value) guardarSesion({ ...datos, token: sesion.value.token })
}

export function cerrarSesion() {
  sesion.value = null
  try {
    localStorage.removeItem(CLAVE)
  } catch {
    /* nada que borrar */
  }
}
