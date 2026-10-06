import { sesion, cerrarSesion } from './sesion'

async function pedir(url, opciones = {}) {
  const token = sesion.value?.token
  if (token) opciones.headers = { ...opciones.headers, Authorization: `Bearer ${token}` }
  const r = await fetch(url, opciones)
  if (r.status === 401 && token) cerrarSesion() // token vencido o inválido
  if (!r.ok) {
    const e = await r.json().catch(() => ({}))
    const detalle = Array.isArray(e.detail) ? e.detail[0]?.msg : e.detail
    throw new Error(detalle?.replace(/^Value error, /, '') || 'No se pudo completar la acción')
  }
  return r.status === 204 ? null : r.json()
}

const json = (metodo, cuerpo) => ({
  method: metodo,
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(cuerpo),
})

export const api = {
  tipos: () => pedir('/api/tipos'),
  edificio: () => pedir('/api/edificio'),
  listar: ({ estado = '', tipoId = '', negocio = '', mias = false, apartamentoId = '' } = {}) => {
    const q = new URLSearchParams()
    if (mias) q.set('mias', 'true')
    if (apartamentoId) q.set('apartamento_id', apartamentoId)
    if (estado) q.set('estado', estado)
    if (tipoId) q.set('tipo_id', tipoId)
    if (negocio) q.set('negocio', negocio)
    return pedir('/api/propiedades' + (q.size ? `?${q}` : ''))
  },
  obtener: (id) => pedir(`/api/propiedades/${id}`),
  crear: (datos) => pedir('/api/propiedades', json('POST', datos)),
  actualizar: (id, datos) => pedir(`/api/propiedades/${id}`, json('PUT', datos)),
  cambiarEstado: (id, estado) => pedir(`/api/propiedades/${id}/estado`, json('PATCH', { estado })),
  eliminar: (id) => pedir(`/api/propiedades/${id}`, { method: 'DELETE' }),
  subirFotos: (id, archivos) => {
    const datos = new FormData()
    archivos.forEach((a) => datos.append('fotos', a))
    return pedir(`/api/propiedades/${id}/fotos`, { method: 'POST', body: datos })
  },
  horarios: (id) => pedir(`/api/propiedades/${id}/horarios`),
  agendarVisita: (id, datos) => pedir(`/api/propiedades/${id}/visitas`, json('POST', datos)),
  visitas: (id) => pedir(`/api/propiedades/${id}/visitas`),
  estadoVisita: (id, estado) => pedir(`/api/visitas/${id}`, json('PATCH', { estado })),
  marcarPrincipal: (id) => pedir(`/api/fotos/${id}/principal`, { method: 'PATCH' }),
  borrarFoto: (id) => pedir(`/api/fotos/${id}`, { method: 'DELETE' }),
  noticias: ({ todas = false, limite = '' } = {}) => {
    const q = new URLSearchParams()
    if (todas) q.set('todas', 'true')
    if (limite) q.set('limite', limite)
    return pedir('/api/noticias' + (q.size ? `?${q}` : ''))
  },
  noticia: (id) => pedir(`/api/noticias/${id}`),
  crearNoticia: (datos) => pedir('/api/noticias', json('POST', datos)),
  actualizarNoticia: (id, datos) => pedir(`/api/noticias/${id}`, json('PUT', datos)),
  eliminarNoticia: (id) => pedir(`/api/noticias/${id}`, { method: 'DELETE' }),
  subirImagenNoticia: (id, archivo) => {
    const datos = new FormData()
    datos.append('imagen', archivo)
    return pedir(`/api/noticias/${id}/imagen`, { method: 'POST', body: datos })
  },
  borrarImagenNoticia: (id) => pedir(`/api/noticias/${id}/imagen`, { method: 'DELETE' }),
  apartamentos: () => pedir('/api/apartamentos'),
  apartamento: (id) => pedir(`/api/apartamentos/${id}`),
  crearApartamento: (datos) => pedir('/api/apartamentos', json('POST', datos)),
  actualizarApartamento: (id, datos) => pedir(`/api/apartamentos/${id}`, json('PUT', datos)),
  eliminarApartamento: (id) => pedir(`/api/apartamentos/${id}`, { method: 'DELETE' }),
  agregarPersona: (aptoId, datos) => pedir(`/api/apartamentos/${aptoId}/personas`, json('POST', datos)),
  actualizarPersona: (id, datos) => pedir(`/api/personas/${id}`, json('PUT', datos)),
  eliminarPersona: (id) => pedir(`/api/personas/${id}`, { method: 'DELETE' }),
  parqueaderos: () => pedir('/api/parqueaderos'),
  crearParqueadero: (datos) => pedir('/api/parqueaderos', json('POST', datos)),
  crearParqueaderosLote: (datos) => pedir('/api/parqueaderos/lote', json('POST', datos)),
  actualizarParqueadero: (id, datos) => pedir(`/api/parqueaderos/${id}`, json('PUT', datos)),
  eliminarParqueadero: (id) => pedir(`/api/parqueaderos/${id}`, { method: 'DELETE' }),
  sorteos: () => pedir('/api/sorteos'),
  sorteo: (id) => pedir(`/api/sorteos/${id}`),
  crearSorteo: (datos) => pedir('/api/sorteos', json('POST', datos)),
  actualizarSorteo: (id, datos) => pedir(`/api/sorteos/${id}`, json('PUT', datos)),
  eliminarSorteo: (id) => pedir(`/api/sorteos/${id}`, { method: 'DELETE' }),
  inscribirApartamento: (id, apartamentoId) => pedir(`/api/sorteos/${id}/postulaciones`, json('POST', { apartamento_id: apartamentoId })),
  postular: (id, apartamentoId) => pedir(`/api/sorteos/${id}/postular`, json('POST', { apartamento_id: apartamentoId })),
  retirarPostulacion: (id) => pedir(`/api/postulaciones/${id}`, { method: 'DELETE' }),
  realizarSorteo: (id) => pedir(`/api/sorteos/${id}/realizar`, { method: 'POST' }),
  misSorteos: () => pedir('/api/mis-sorteos'),
  zonas: () => pedir('/api/zonas'),
  zona: (slug) => pedir(`/api/zonas/${slug}`),
  crearZona: (datos) => pedir('/api/zonas', json('POST', datos)),
  actualizarZona: (id, datos) => pedir(`/api/zonas/${id}`, json('PUT', datos)),
  eliminarZona: (id) => pedir(`/api/zonas/${id}`, { method: 'DELETE' }),
  subirFotosZona: (id, archivos) => {
    const datos = new FormData()
    archivos.forEach((a) => datos.append('fotos', a))
    return pedir(`/api/zonas/${id}/fotos`, { method: 'POST', body: datos })
  },
  borrarFotoZona: (id) => pedir(`/api/fotos-zona/${id}`, { method: 'DELETE' }),
  perfil: () => pedir('/api/perfil'),
  actualizarPerfil: (datos) => pedir('/api/perfil', json('PUT', datos)),
  usuarios: () => pedir('/api/usuarios'),
  verificarUsuario: (id, verificado) => pedir(`/api/usuarios/${id}/verificacion`, json('PATCH', { verificado })),
  cambiarRol: (id, rol) => pedir(`/api/usuarios/${id}/rol`, json('PATCH', { rol })),
  crearUsuario: (datos) => pedir('/api/usuarios', json('POST', datos)),
  restablecerClave: (id, clave) => pedir(`/api/usuarios/${id}/clave`, json('PATCH', { clave })),
  activar: (token, clave) => pedir('/api/activar', json('POST', { token, clave })),
  invitarPersona: (id) => pedir(`/api/personas/${id}/invitacion`, { method: 'POST' }),
  invitarUsuario: (id) => pedir(`/api/usuarios/${id}/invitacion`, { method: 'POST' }),
  cambiarMiClave: (actual, nueva) => pedir('/api/perfil/clave', json('PUT', { actual, nueva })),
  iniciarSesion: (datos) => pedir('/api/sesion', json('POST', datos)),
}

// Id de un video de YouTube a partir del enlace (watch?v=, youtu.be/, shorts/) o null
export function idYoutube(texto) {
  const t = (texto || '').trim()
  if (/^[\w-]{11}$/.test(t)) return t
  const m = t.match(/(?:youtube\.com\/(?:watch\?(?:.*&)?v=|shorts\/|embed\/|live\/)|youtu\.be\/)([\w-]{11})/)
  return m ? m[1] : null
}
// Coeficiente de copropiedad: 0.8523 -> "0,8523 %"
export const coef = (v) => `${Number(v).toLocaleString('es-CO', { maximumFractionDigits: 6 })} %`
// "2026-10-16" -> "16 de octubre de 2026" (sin desfase de zona horaria)
export const fechaCorta = (iso) =>
  iso ? new Date(`${iso}T12:00:00`).toLocaleDateString('es-CO', { day: 'numeric', month: 'long', year: 'numeric' }) : ''
export const MAX_FOTOS = 10
export const DIAS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

// Enlace de WhatsApp: celulares colombianos de 10 dígitos llevan el prefijo 57
export function whatsapp(telefono) {
  let n = (telefono || '').replace(/\D/g, '')
  if (n.length === 10 && n.startsWith('3')) n = '57' + n
  return `https://wa.me/${n}`
}

export const cop = (v) => '$' + Number(v).toLocaleString('es-CO')
export const ESTADOS = ['borrador', 'publicado', 'vendido']
export const NEGOCIOS = ['venta', 'arriendo']
// El edificio tiene una sola torre: "Apto 502"
export const nombreApto = (a) => `Apto ${a.numero}`

// Fecha de una noticia: "5 de octubre de 2026"
export const fechaLarga = (v) =>
  new Date(v).toLocaleDateString('es-CO', { day: 'numeric', month: 'long', year: 'numeric' })
export const PERFILES = {
  superadmin: 'Super admin',
  admin: 'Administrador',
  propietario: 'Propietario',
  arrendatario: 'Arrendatario',
  residente: 'Pendiente de verificación',
}
export const capitalizar = (t) => t.charAt(0).toUpperCase() + t.slice(1)
