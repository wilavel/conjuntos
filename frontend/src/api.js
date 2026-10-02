async function pedir(url, opciones = {}) {
  const r = await fetch(url, opciones)
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
  listar: ({ estado = '', tipoId = '' } = {}) => {
    const q = new URLSearchParams()
    if (estado) q.set('estado', estado)
    if (tipoId) q.set('tipo_id', tipoId)
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
  borrarFoto: (id) => pedir(`/api/fotos/${id}`, { method: 'DELETE' }),
  registrar: (datos) => pedir('/api/usuarios', json('POST', datos)),
}

export const cop = (v) => '$' + Number(v).toLocaleString('es-CO')
export const ESTADOS = ['borrador', 'publicado', 'vendido']
export const capitalizar = (t) => t.charAt(0).toUpperCase() + t.slice(1)
