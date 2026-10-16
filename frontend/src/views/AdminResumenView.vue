<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'
import { sesion } from '../sesion'
import Icono from '../components/Icono.vue'

// Portada del panel: cifras rápidas y accesos directos (solo con datos existentes)
const datos = ref({ apartamentos: [], parqueaderos: [], sorteos: [], usuarios: [], noticias: [] })
const cargando = ref(true)

onMounted(async () => {
  const [apartamentos, parqueaderos, sorteos, usuarios, noticias] = await Promise.all([
    api.apartamentos().catch(() => []),
    api.parqueaderos().catch(() => []),
    api.sorteos().catch(() => []),
    api.usuarios().catch(() => []),
    api.noticias({ todas: true }).catch(() => []),
  ])
  datos.value = { apartamentos, parqueaderos, sorteos, usuarios, noticias }
  cargando.value = false
})

const tarjetas = computed(() => {
  const d = datos.value
  const deudores = d.apartamentos.filter((a) => a.deudor).length
  const porVerificar = d.usuarios.filter((u) => !u.rol_staff && !u.verificado).length
  const libres = d.parqueaderos.filter((p) => p.uso === 'residente' && !p.apartamento_id).length
  const abiertos = d.sorteos.filter((s) => s.estado !== 'realizado').length
  const borradores = d.noticias.filter((n) => !n.publicada).length
  return [
    { icono: 'apartment', valor: d.apartamentos.length, texto: 'Apartamentos', ruta: '/admin/apartamentos' },
    { icono: 'money_off', valor: deudores, texto: deudores === 1 ? 'Deudor' : 'Deudores', ruta: '/admin/apartamentos', alerta: deudores > 0 },
    { icono: 'how_to_reg', valor: porVerificar, texto: 'Cuentas por verificar', ruta: '/admin/usuarios', alerta: porVerificar > 0 },
    { icono: 'local_parking', valor: libres, texto: 'Parqueaderos libres', ruta: '/admin/parqueaderos' },
    { icono: 'casino', valor: abiertos, texto: abiertos === 1 ? 'Sorteo sin realizar' : 'Sorteos sin realizar', ruta: '/admin/sorteos' },
    { icono: 'edit_note', valor: borradores, texto: 'Noticias en borrador', ruta: '/admin/noticias' },
  ]
})

const ATAJOS = [
  { icono: 'add_home', texto: 'Nuevo apartamento', ruta: '/admin/apartamentos/nuevo' },
  { icono: 'person_add', texto: 'Nuevo usuario', ruta: '/admin/usuarios' },
  { icono: 'post_add', texto: 'Nueva noticia', ruta: '/admin/noticias/nueva' },
  { icono: 'casino', texto: 'Nuevo sorteo', ruta: '/admin/sorteos' },
]
</script>

<template>
  <div class="panel-encabezado">
    <span class="etiqueta">Resumen</span>
    <h1>Hola, {{ sesion?.nombre?.split(' ')[0] }}</h1>
    <p>Lo más importante de Trend Apartamentos de un vistazo.</p>
  </div>

  <div class="resumen-tarjetas">
    <RouterLink v-for="t in tarjetas" :key="t.texto" :to="t.ruta" class="resumen-tarjeta" :class="{ alerta: t.alerta }">
      <span class="icono-caja"><Icono :nombre="t.icono" /></span>
      <strong>{{ cargando ? '—' : t.valor }}</strong>
      <span>{{ t.texto }}</span>
    </RouterLink>
  </div>

  <h2 class="panel-subtitulo">Accesos rápidos</h2>
  <div class="resumen-atajos">
    <RouterLink v-for="a in ATAJOS" :key="a.texto" :to="a.ruta" class="boton secundario">
      <Icono :nombre="a.icono" /> {{ a.texto }}
    </RouterLink>
  </div>
</template>
