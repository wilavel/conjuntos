<script setup>
import { reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { ICONOS_ZONA } from '../zonas'
import HorarioAtencion from '../components/HorarioAtencion.vue'

const props = defineProps({ id: String })
const router = useRouter()

const form = reactive({
  nombre: '', icono: 'gimnasio', resumen: '', descripcion: '', horario: '', orden: 0,
  reservable: true, capacidad: 1,
  franjas: [0, 1, 2, 3, 4, 5, 6].map((dia) => ({ dia, inicio: '06:00', fin: '22:00' })),
})
const reservas = ref([])
const zona = ref(null) // zona guardada (para fotos y enlace público)
const archivos = ref([])
const inputFotos = ref(null)
const error = ref('')
const aviso = ref('')
const guardando = ref(false)

function mostrar(z) {
  zona.value = z
  for (const k of Object.keys(form)) form[k] = z[k] ?? form[k]
  form.horario = z.nota_horario || '' // nota libre (el texto del horario sale de las franjas)
  form.franjas = (z.franjas || []).map((f) => ({ ...f }))
}

onMounted(async () => {
  if (!props.id) return
  try {
    // La API pública busca por slug; aquí se busca por id en el listado
    const z = (await api.zonas()).find((x) => String(x.id) === props.id)
    if (!z) throw new Error('Zona no encontrada')
    mostrar(z)
    reservas.value = await api.reservasZona(z.id).catch(() => [])
  } catch (e) {
    error.value = e.message
  }
})

async function accion(fn, mensaje = '') {
  error.value = ''
  aviso.value = ''
  try {
    await fn()
    aviso.value = mensaje
  } catch (e) {
    error.value = e.message
  }
}

const guardar = () =>
  accion(async () => {
    guardando.value = true
    try {
      const datos = { ...form, orden: Number(form.orden) || 0, capacidad: Number(form.capacidad) || 1 }
      if (props.id) mostrar(await api.actualizarZona(props.id, datos))
      else {
        const z = await api.crearZona(datos)
        router.replace(`/admin/zonas/${z.id}`)
        mostrar(z)
      }
    } finally {
      guardando.value = false
    }
  }, 'Cambios guardados')

const subirFotos = () =>
  accion(async () => {
    mostrar(await api.subirFotosZona(zona.value.id, archivos.value))
    archivos.value = []
    inputFotos.value.value = ''
  }, 'Fotos subidas')

const borrarFoto = (foto) =>
  accion(async () => {
    if (!confirm('¿Eliminar esta foto?')) return
    await api.borrarFotoZona(foto.id)
    zona.value.fotos = zona.value.fotos.filter((f) => f.id !== foto.id)
  })

const cancelarReserva = (r) =>
  accion(async () => {
    if (!confirm(`¿Cancelar la reserva del Apto ${r.apartamento.numero}?`)) return
    const nueva = await api.cancelarReserva(r.id)
    reservas.value = reservas.value.map((x) => (x.id === r.id ? nueva : x))
  }, 'Reserva cancelada')

const eliminar = () =>
  accion(async () => {
    if (!confirm('¿Eliminar esta zona y sus fotos?')) return
    await api.eliminarZona(zona.value.id)
    router.push('/admin/zonas')
  })
</script>

<template>
  <RouterLink class="articulo-volver" to="/admin/zonas">← Todas las zonas</RouterLink>
  <div class="encabezado titulo-admin">
    <h1>{{ zona ? zona.nombre : 'Nueva zona común' }}</h1>
    <RouterLink v-if="zona" class="boton secundario" :to="{ path: '/', hash: `#zona-${zona.slug}` }">Ver en el inicio</RouterLink>
  </div>

  <form class="formulario" @submit.prevent="guardar">
    <div class="grupo">
      <label>Nombre<input v-model="form.nombre" required maxlength="100" placeholder="Salón comunal" /></label>
      <label>
        Ícono
        <select v-model="form.icono">
          <option v-for="(i, clave) in ICONOS_ZONA" :key="clave" :value="clave">{{ i.etiqueta }}</option>
        </select>
      </label>
      <label>Orden <span class="opcional">(menor = primero)</span><input v-model.number="form.orden" type="number" /></label>
    </div>
    <label>
      Resumen <span class="opcional">(se muestra en la tarjeta del inicio)</span>
      <input v-model="form.resumen" maxlength="300" />
    </label>
    <label>
      Descripción <span class="opcional">(deja una línea en blanco entre párrafos)</span>
      <textarea v-model="form.descripcion" rows="8"></textarea>
    </label>
    <HorarioAtencion :franjas="form.franjas" />
    <div class="grupo">
      <label class="check">
        <input v-model="form.reservable" type="checkbox" />
        Los apartamentos pueden reservarla
      </label>
      <label v-if="form.reservable">
        Apartamentos a la vez <span class="opcional">(1 = uso exclusivo)</span>
        <input v-model.number="form.capacidad" type="number" min="1" max="50" />
      </label>
    </div>
    <label>
      Nota sobre el horario <span class="opcional">(opcional, ej. «Cerrado festivos»)</span>
      <input v-model="form.horario" maxlength="200" />
    </label>
    <div class="acciones">
      <button class="boton" type="submit" :disabled="guardando">{{ zona ? 'Guardar cambios' : 'Crear zona' }}</button>
      <span v-if="aviso">{{ aviso }}</span>
    </div>
  </form>
  <p v-if="error" class="error">{{ error }}</p>

  <template v-if="zona">
    <h2>Fotos</h2>
    <p class="opcional">La primera foto es la que se muestra primero en el inicio.</p>
    <div class="fotos">
      <figure v-for="(f, i) in zona.fotos" :key="f.id">
        <img :src="f.url" :alt="`Foto ${i + 1}`" />
        <button class="borrar" type="button" @click="borrarFoto(f)">Eliminar</button>
      </figure>
    </div>
    <form class="subida" @submit.prevent="subirFotos">
      <input ref="inputFotos" type="file" accept="image/*" multiple @change="archivos = [...$event.target.files]" />
      <button class="boton" type="submit" :disabled="!archivos.length">Subir fotos</button>
    </form>

    <h2>Próximas reservas</h2>
    <p v-if="!reservas.length" class="vacio">No hay reservas próximas.</p>
    <ul class="personas-lista">
      <li v-for="r in reservas" :key="r.id" :class="{ inactiva: r.estado === 'cancelada' }">
        <div class="persona-datos">
          <strong>{{ r.dia }} {{ new Date(`${r.fecha}T12:00:00`).toLocaleDateString('es-CO', { day: 'numeric', month: 'long' }) }} · {{ r.inicio }} a {{ r.fin }}</strong>
          <span>Apto {{ r.apartamento.numero }}</span>
        </div>
        <div class="persona-acciones">
          <span class="estado" :class="r.estado === 'activa' ? 'publicado' : 'vendido'">{{ r.estado }}</span>
          <button v-if="r.estado === 'activa'" type="button" class="enlace peligro-texto" @click="cancelarReserva(r)">Cancelar</button>
        </div>
      </li>
    </ul>

    <div class="acciones pie">
      <span></span>
      <button class="boton peligro" type="button" @click="eliminar">Eliminar zona</button>
    </div>
  </template>
</template>
