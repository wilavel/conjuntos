<script setup>
import { reactive, ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, nombreApto, idYoutube } from '../api'
import { sesion, esAdmin } from '../sesion'
import HorarioVisitas from '../components/HorarioVisitas.vue'

const props = defineProps({ id: String })
const router = useRouter()
const route = useRoute()

const edificio = ref(null) // valores por defecto: todos son apartamentos del mismo edificio en Bogotá
const apartamentos = ref([]) // apartamentos que se pueden elegir
const form = reactive({
  apartamento_id: '',
  negocio: 'arriendo',
  amoblado: false,
  titulo: '',
  precio: '',
  administracion: '',
  descripcion: '',
  video_youtube: '',
  telefonos: [''],
  duracion_visita: 30,
  disponibilidad: [],
})

// Horario propuesto: lunes a viernes de 9:00 a 17:00 (se edita o se quita a gusto)
const HORARIO_BASE = () => [0, 1, 2, 3, 4].map((dia) => ({ dia, inicio: '09:00', fin: '17:00' }))
form.disponibilidad = HORARIO_BASE()
const error = ref('')
const guardando = ref(false)

// La ubicación, el estrato y el año los pone el backend con los datos del edificio

onMounted(async () => {
  try {
    edificio.value = await api.edificio()
    if (esAdmin.value) {
      apartamentos.value = await api.apartamentos()
    } else {
      // El propietario solo publica sus propios apartamentos
      apartamentos.value = (sesion.value?.apartamentos || []).filter((a) => a.rol === 'propietario')
      if (apartamentos.value.length === 1) form.apartamento_id = apartamentos.value[0].id
    }
    // Desde la ficha del apartamento llega ya elegido
    const elegido = Number(route.query.apartamento)
    if (!props.id && apartamentos.value.some((a) => a.id === elegido)) form.apartamento_id = elegido
    if (props.id) {
      const p = await api.obtener(props.id)
      for (const k of Object.keys(form)) form[k] = p[k] ?? ''
      if (p.video_youtube) form.video_youtube = `https://youtu.be/${p.video_youtube}`
      form.telefonos = p.telefonos?.length ? [...p.telefonos] : ['']
      form.duracion_visita = p.duracion_visita || 30
      // Si el aviso aún no tiene horario se propone el de lunes a viernes
      form.disponibilidad = p.disponibilidad?.length ? p.disponibilidad.map((f) => ({ ...f })) : HORARIO_BASE()
    }
  } catch (e) {
    error.value = e.message
  }
})

// Características del apartamento elegido (se editan en el apartamento, no en el aviso)
const apto = computed(() => apartamentos.value.find((x) => x.id === form.apartamento_id))
const caracteristicas = computed(() => {
  const a = apto.value
  if (!a) return []
  return [
    a.area_m2 && `${a.area_m2} m²`,
    a.piso != null && `Piso ${a.piso}`,
    `${a.habitaciones} ${a.habitaciones === 1 ? 'habitación' : 'habitaciones'}`,
    `${a.banos} ${a.banos === 1 ? 'baño' : 'baños'}`,
    `${a.parqueaderos} ${a.parqueaderos === 1 ? 'parqueadero' : 'parqueaderos'}`,
  ].filter(Boolean)
})

// Vista previa del video mientras se pega el enlace
const video = computed(() => idYoutube(form.video_youtube))

const sugerencia = computed(() => {
  const partes = ['Apartamento']
  const h = apto.value?.habitaciones
  if (h) partes.push(`de ${h} ${h === 1 ? 'habitación' : 'habitaciones'}`)
  if (form.negocio === 'arriendo' && form.amoblado) partes.push('amoblado')
  partes.push(form.negocio === 'arriendo' ? 'en arriendo' : 'en venta')
  return `${partes.join(' ')} en ${edificio.value?.nombre || 'Trend Apartamentos'}`
})

async function guardar() {
  guardando.value = true
  error.value = ''
  const datos = { ...form, titulo: form.titulo.trim() || sugerencia.value }
  if (form.negocio !== 'arriendo') datos.amoblado = false
  datos.telefonos = form.telefonos.map((t) => t.trim()).filter(Boolean)
  datos.administracion = form.administracion === '' ? null : Number(form.administracion)
  try {
    const p = props.id ? await api.actualizar(props.id, datos) : await api.crear(datos)
    router.push(`/propiedades/${p.id}`)
  } catch (e) {
    error.value = e.message
    guardando.value = false
  }
}

const volver = computed(() => {
  if (props.id) return `/propiedades/${props.id}`
  if (!esAdmin.value) return '/privado'
  return form.apartamento_id ? `/admin/apartamentos/${form.apartamento_id}` : '/admin/apartamentos'
})
</script>

<template>
  <h1>{{ id ? 'Editar aviso' : 'Nuevo aviso de venta o arriendo' }}</h1>
  <p v-if="edificio" class="intro-admin">
    Apartamento en <strong>{{ edificio.nombre }}</strong>, {{ edificio.ciudad }}. La ubicación se toma del
    edificio.
  </p>

  <p v-if="!apartamentos.length" class="vacio">
    <template v-if="esAdmin">
      Primero crea el apartamento en <RouterLink to="/admin/apartamentos">Apartamentos</RouterLink>; los
      avisos se publican sobre un apartamento del conjunto.
    </template>
    <template v-else>
      Tu cuenta no figura como propietario activo de ningún apartamento. Si es un error, comunícate
      con la administración.
    </template>
  </p>

  <form v-else class="formulario" @submit.prevent="guardar">
    <div class="grupo">
      <label>
        Apartamento
        <select v-model="form.apartamento_id" required>
          <option value="" disabled>Elige el apartamento</option>
          <option v-for="a in apartamentos" :key="a.id" :value="a.id">{{ nombreApto(a) }}</option>
        </select>
      </label>
      <label>
        Negocio
        <select v-model="form.negocio" required>
          <option value="arriendo">Arriendo</option>
          <option value="venta">Venta</option>
        </select>
      </label>
      <label v-if="form.negocio === 'arriendo'">
        ¿Se arrienda amoblado?
        <select v-model="form.amoblado">
          <option :value="false">Sin amoblar</option>
          <option :value="true">Amoblado</option>
        </select>
      </label>
      <label>{{ form.negocio === 'arriendo' ? 'Canon mensual (COP)' : 'Precio (COP)' }}<input v-model.number="form.precio" type="number" min="0" required /></label>
      <label>Administración mensual (COP)<input v-model.number="form.administracion" type="number" min="0" /></label>
    </div>
    <label>
      Título <span class="opcional">(si lo dejas vacío: «{{ sugerencia }}»)</span>
      <input v-model="form.titulo" maxlength="200" :placeholder="sugerencia" />
    </label>

    <div v-if="apto" class="caracteristicas-apto">
      <span class="rotulo">Características del apartamento</span>
      <ul class="rasgos">
        <li v-for="c in caracteristicas" :key="c">{{ c }}</li>
      </ul>
      <p class="opcional">
        Se toman del apartamento.
        <template v-if="esAdmin">
          Para corregirlas, edita el <RouterLink :to="`/admin/apartamentos/${apto.id}`">apartamento</RouterLink>.
        </template>
        <template v-else>Si algo no corresponde, pide a la administración que lo corrija.</template>
      </p>
    </div>

    <label>
      Descripción
      <textarea v-model="form.descripcion" rows="8" placeholder="Iluminado, vista exterior, cocina integral, cerca a…"></textarea>
    </label>
    <fieldset>
      <legend>Teléfonos de contacto</legend>
      <div v-for="(t, i) in form.telefonos" :key="i" class="telefono-fila">
        <input v-model="form.telefonos[i]" type="tel" maxlength="30" :required="i === 0" placeholder="300 123 4567" :aria-label="`Teléfono ${i + 1}`" />
        <button v-if="form.telefonos.length > 1" type="button" class="enlace peligro-texto" @click="form.telefonos.splice(i, 1)">Quitar</button>
      </div>
      <button v-if="form.telefonos.length < 5" type="button" class="enlace" @click="form.telefonos.push('')">+ Agregar otro teléfono</button>
      <p class="opcional">Se muestran en el aviso con botones para llamar y escribir por WhatsApp.</p>
    </fieldset>

    <HorarioVisitas v-model:duracion="form.duracion_visita" :franjas="form.disponibilidad" />

    <label>
      Video de YouTube <span class="opcional">(opcional: un recorrido corto, de 1 a 3 minutos)</span>
      <input v-model="form.video_youtube" type="url" placeholder="https://www.youtube.com/watch?v=… o https://youtu.be/…" />
    </label>
    <p v-if="form.video_youtube && !video" class="error">Pega el enlace de un video de YouTube.</p>
    <div v-if="video" class="video video-previa">
      <iframe :src="`https://www.youtube-nocookie.com/embed/${video}`" title="Vista previa del video" allowfullscreen loading="lazy"></iframe>
    </div>
    <p class="opcional">
      Consejo: en YouTube súbelo como «No listado» si no quieres que aparezca en búsquedas; igual se
      verá en el aviso.
    </p>

    <p v-if="error" class="error">{{ error }}</p>
    <div class="acciones">
      <button class="boton" type="submit" :disabled="guardando">{{ id ? 'Guardar' : 'Crear aviso' }}</button>
      <RouterLink :to="volver">Cancelar</RouterLink>
    </div>
    <p v-if="!id" class="opcional">Después de crearlo podrás subir hasta 10 fotos y publicarlo.</p>
  </form>
</template>
