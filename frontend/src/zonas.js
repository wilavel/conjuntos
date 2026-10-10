// Íconos de las zonas comunes (Material Symbols). La zona guarda la clave en el campo "icono".
export const ICONOS_ZONA = {
  gimnasio: { etiqueta: 'Gimnasio', simbolo: 'fitness_center' },
  terrazas: { etiqueta: 'Terraza / BBQ', simbolo: 'outdoor_grill' },
  coworking: { etiqueta: 'Coworking', simbolo: 'laptop_mac' },
  lavanderia: { etiqueta: 'Lavandería', simbolo: 'local_laundry_service' },
  parqueaderos: { etiqueta: 'Parqueadero', simbolo: 'directions_car' },
  salon: { etiqueta: 'Salón comunal', simbolo: 'celebration' },
  piscina: { etiqueta: 'Piscina', simbolo: 'pool' },
  juegos: { etiqueta: 'Zona infantil', simbolo: 'toys' },
  'zona-verde': { etiqueta: 'Zona verde', simbolo: 'park' },
  porteria: { etiqueta: 'Portería', simbolo: 'shield_person' },
}

export const simboloZona = (clave) => (ICONOS_ZONA[clave] || ICONOS_ZONA['zona-verde']).simbolo
export const iconoZona = (clave) =>
  `<span class="material-symbols-outlined" aria-hidden="true">${simboloZona(clave)}</span>`

// Zonas por defecto: el inicio las muestra aunque el backend no responda.
export const ZONAS_BASE = [
  { slug: 'gimnasio', nombre: 'Gimnasio', icono: 'gimnasio', resumen: 'Equipos de cardio y fuerza para entrenar sin salir del conjunto.' },
  { slug: 'terrazas', nombre: 'Terrazas', icono: 'terrazas', resumen: 'Terrazas sociales al aire libre con zona BBQ y mobiliario para compartir.' },
  { slug: 'coworking', nombre: 'Coworking', icono: 'coworking', resumen: 'Puestos de trabajo con wifi y ambiente tranquilo para estudiar o trabajar.' },
  { slug: 'lavanderia', nombre: 'Lavandería', icono: 'lavanderia', resumen: 'Lavadoras y secadoras comunales de uso programado.' },
  { slug: 'parqueaderos', nombre: 'Parqueaderos', icono: 'parqueaderos', resumen: 'Parqueaderos privados para residentes y espacios para visitantes.' },
].map((z, i) => ({ id: `base-${i}`, descripcion: '', horario: '', fotos: [], ...z }))
