// Íconos de las zonas comunes (la zona guarda la clave en el campo "icono").
const svg = (trazos) =>
  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" ` +
  `stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${trazos}</svg>`

export const ICONOS_ZONA = {
  gimnasio: { etiqueta: 'Gimnasio', svg: svg('<path d="M6.5 8v8M4 9.5v5M17.5 8v8M20 9.5v5M6.5 12h11"/>') },
  terrazas: { etiqueta: 'Terraza / BBQ', svg: svg('<path d="M5 6h14l-7 7z"/><path d="M12 13v4"/><path d="M8 20h8"/>') },
  coworking: { etiqueta: 'Coworking', svg: svg('<rect x="5" y="5" width="14" height="9.5" rx="1"/><path d="M3 18.5h18"/><path d="M10 14.5l-.5 4M14 14.5l.5 4"/>') },
  lavanderia: { etiqueta: 'Lavandería', svg: svg('<rect x="5" y="3.5" width="14" height="17" rx="2"/><circle cx="12" cy="13" r="3.5"/><path d="M8.5 7h.01M11.5 7h.01"/>') },
  parqueaderos: { etiqueta: 'Parqueadero', svg: svg('<path d="M4.5 15.5l1.6-4.6A1.5 1.5 0 0 1 7.5 10h9a1.5 1.5 0 0 1 1.4 1l1.6 4.5v3.5h-3v-1.5H7.5V19h-3z"/><path d="M8 16.5h.01M16 16.5h.01"/>') },
  salon: { etiqueta: 'Salón comunal', svg: svg('<path d="M4 12a2 2 0 0 1 2-2 2 2 0 0 1 2 2v1h8v-1a2 2 0 0 1 2-2 2 2 0 0 1 2 2v5H4z"/><path d="M7 17v2M17 17v2"/>') },
  piscina: { etiqueta: 'Piscina', svg: svg('<path d="M3 17c1.5 1 3 1 4.5 0s3-1 4.5 0 3 1 4.5 0 3-1 4.5 0"/><path d="M3 20.5c1.5 1 3 1 4.5 0s3-1 4.5 0 3 1 4.5 0 3-1 4.5 0"/><path d="M8 14V5.5a2 2 0 0 1 4 0M16 14V5.5a2 2 0 0 0-4 0M8 9h8"/>') },
  juegos: { etiqueta: 'Zona infantil', svg: svg('<circle cx="12" cy="6" r="2.5"/><path d="M12 8.5V15M8 11h8M9 21l3-6 3 6"/>') },
  'zona-verde': { etiqueta: 'Zona verde', svg: svg('<path d="M12 3.5l5 6.5h-3l4 5.5H6l4-5.5H7z"/><path d="M12 15.5V21"/>') },
  porteria: { etiqueta: 'Portería', svg: svg('<path d="M12 3l7 3v5.5c0 4.3-2.9 7.3-7 8.9-4.1-1.6-7-4.6-7-8.9V6z"/><path d="M9.2 12.2l2 2 3.6-3.8"/>') },
}

export const iconoZona = (clave) => (ICONOS_ZONA[clave] || ICONOS_ZONA['zona-verde']).svg

// Zonas por defecto: el inicio las muestra aunque el backend no responda.
export const ZONAS_BASE = [
  { slug: 'gimnasio', nombre: 'Gimnasio', icono: 'gimnasio', resumen: 'Equipos de cardio y fuerza para entrenar sin salir del conjunto.' },
  { slug: 'terrazas', nombre: 'Terrazas', icono: 'terrazas', resumen: 'Terrazas sociales al aire libre con zona BBQ y mobiliario para compartir.' },
  { slug: 'coworking', nombre: 'Coworking', icono: 'coworking', resumen: 'Puestos de trabajo con wifi y ambiente tranquilo para estudiar o trabajar.' },
  { slug: 'lavanderia', nombre: 'Lavandería', icono: 'lavanderia', resumen: 'Lavadoras y secadoras comunales de uso programado.' },
  { slug: 'parqueaderos', nombre: 'Parqueaderos', icono: 'parqueaderos', resumen: 'Parqueaderos privados para residentes y espacios para visitantes.' },
].map((z, i) => ({ id: `base-${i}`, descripcion: '', horario: '', fotos: [], ...z }))
