<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api, cop, capitalizar, nombreApto, whatsapp, ESTADOS, MAX_FOTOS } from '../api'
import AgendarVisita from '../components/AgendarVisita.vue'
import VisitasAviso from '../components/VisitasAviso.vue'
import { esAdmin } from '../sesion'
import Icono from '../components/Icono.vue'

const props = defineProps({ id: String })
const router = useRouter()

const prop = ref(null)
const error = ref('')
const copiado = ref(false)
const archivos = ref([])
const inputFotos = ref(null)

onMounted(async () => {
  try {
    prop.value = await api.obtener(props.id)
  } catch (e) {
    error.value = e.message
  }
})

// Solo se muestran los datos que la propiedad realmente tiene
const datos = computed(() => {
  const p = prop.value
  if (!p) return []
  const filas = []
  const add = (etiqueta, valor) => {
    if (valor !== null && valor !== undefined && valor !== '') filas.push([etiqueta, valor])
  }
  add('Negocio', p.negocio === 'arriendo' ? 'Arriendo' : 'Venta')
  if (p.negocio === 'arriendo') add('Amoblado', p.amoblado ? 'Sí' : 'No')
  add('Área construida', p.area_construida_m2 ? `${p.area_construida_m2} m²` : null)
  add('Área del lote', p.area_lote_m2 ? `${p.area_lote_m2} m²` : null)
  add('Habitaciones', p.habitaciones || null)
  add('Baños', p.banos || null)
  add('Parqueaderos', p.parqueaderos || null)
  add('Pisos', p.pisos > 1 ? p.pisos : null)
  add('Piso', p.piso)
  if (p.anio_construccion) {
    const edad = new Date().getFullYear() - p.anio_construccion
    const nota = edad > 0 ? `${edad} años` : edad === 0 ? 'nueva' : 'sobre planos'
    add('Año de construcción', `${p.anio_construccion} (${nota})`)
  }
  add('Estrato', p.estrato)
  add('Administración', p.administracion ? `${cop(p.administracion)} al mes` : null)
  return filas
})

async function accion(fn) {
  error.value = ''
  try {
    await fn()
  } catch (e) {
    error.value = e.message
  }
}

const cambiarEstado = (estado) =>
  accion(async () => (prop.value = await api.cambiarEstado(props.id, estado)))

// Máximo 10 fotos por aviso: se avisa antes de subir
const disponibles = computed(() => MAX_FOTOS - (prop.value?.fotos.length || 0))
const avisoFotos = ref('')
function elegirFotos(evento) {
  avisoFotos.value = ''
  let lista = [...evento.target.files]
  if (lista.length > disponibles.value) {
    avisoFotos.value = `Solo caben ${disponibles.value} fotos más; se subirán las primeras ${disponibles.value}.`
    lista = lista.slice(0, disponibles.value)
  }
  const pesadas = lista.filter((a) => a.size > 15 * 1024 * 1024)
  if (pesadas.length) {
    avisoFotos.value = `Estas fotos pesan más de 15 MB y no se subirán: ${pesadas.map((a) => a.name).join(', ')}`
    lista = lista.filter((a) => a.size <= 15 * 1024 * 1024)
  }
  archivos.value = lista
}

const subirFotos = () =>
  accion(async () => {
    if (!archivos.value.length) return
    prop.value = await api.subirFotos(props.id, archivos.value)
    archivos.value = []
    inputFotos.value.value = ''
  })

// Foto que se ve en grande (por defecto, la principal)
const vistaId = ref(null)
const vista = computed(() => prop.value.fotos.find((f) => f.id === vistaId.value) || prop.value.fotos[0])

const hacerPrincipal = (foto) =>
  accion(async () => {
    prop.value = await api.marcarPrincipal(foto.id)
    vistaId.value = foto.id
  })

const borrarFoto = (foto) =>
  accion(async () => {
    if (!confirm('¿Eliminar esta foto?')) return
    await api.borrarFoto(foto.id)
    prop.value.fotos = prop.value.fotos.filter((f) => f.id !== foto.id)
  })

const eliminar = () =>
  accion(async () => {
    if (!confirm('¿Eliminar esta propiedad y sus fotos?')) return
    await api.eliminar(props.id)
    const apto = prop.value.apartamento
    router.push(!esAdmin.value ? '/privado' : apto ? `/admin/apartamentos/${apto.id}` : '/admin/apartamentos')
  })

async function copiar() {
  await navigator.clipboard.writeText(prop.value.anuncio)
  copiado.value = true
  setTimeout(() => (copiado.value = false), 1800)
}
</script>

<template>
  <p v-if="error" class="error">{{ error }}</p>
  <template v-if="prop">
    <div class="encabezado">
      <div>
        <p class="tipo">{{ prop.tipo }}<template v-if="prop.apartamento"> · {{ nombreApto(prop.apartamento) }}</template></p>
        <h1>{{ prop.titulo }}</h1>
        <p class="precio">{{ cop(prop.precio) }}</p>
        <p>{{ [prop.direccion, prop.barrio, prop.ciudad].filter(Boolean).join(', ') }}</p>
      </div>
      <select v-if="prop.puede_editar" :value="prop.estado" class="estado" :class="prop.estado" @change="cambiarEstado($event.target.value)">
        <option v-for="e in ESTADOS" :key="e" :value="e">{{ capitalizar(e) }}</option>
      </select>
    </div>

    <!-- A dónde llamar -->
    <div v-if="prop.telefonos?.length" class="contacto">
      <span class="rotulo">Contacto</span>
      <ul>
        <li v-for="t in prop.telefonos" :key="t">
          <a class="contacto-tel" :href="`tel:${t.replace(/[^\d+]/g, '')}`"><Icono nombre="call" /> {{ t }}</a>
          <a class="boton secundario" :href="`tel:${t.replace(/[^\d+]/g, '')}`">Llamar</a>
          <a class="boton boton-whatsapp" :href="whatsapp(t)" target="_blank" rel="noopener">WhatsApp</a>
        </li>
      </ul>
    </div>

    <dl class="ficha">
      <div v-for="[etiqueta, valor] in datos" :key="etiqueta">
        <dt>{{ etiqueta }}</dt>
        <dd>{{ valor }}</dd>
      </div>
    </dl>

    <h2 v-if="prop.puede_editar || prop.fotos.length">
      Fotos <span v-if="prop.puede_editar" class="contador-fotos">{{ prop.fotos.length }} / {{ MAX_FOTOS }}</span>
    </h2>
    <!-- Foto principal, completa (sin recortar) -->
    <figure v-if="prop.fotos.length" class="foto-principal">
      <div class="tarjeta-foto-fondo" :style="{ backgroundImage: `url(${vista.url})` }" aria-hidden="true"></div>
      <img :src="vista.url" :alt="prop.titulo" />
    </figure>
    <div class="fotos">
      <figure v-for="(f, i) in prop.fotos" :key="f.id" :class="{ activa: vista.id === f.id }">
        <button type="button" class="foto-miniatura" :aria-label="`Ver foto ${i + 1}`" @click="vistaId = f.id">
          <img :src="f.url" :alt="`Foto ${i + 1}`" />
        </button>
        <span v-if="f.principal" class="insignia insignia-principal">★ Principal</span>
        <template v-if="prop.puede_editar">
          <button v-if="!f.principal" class="borrar hacer-principal" type="button" @click="hacerPrincipal(f)">Hacer principal</button>
          <button class="borrar" type="button" @click="borrarFoto(f)">Eliminar</button>
        </template>
      </figure>
    </div>

    <!-- Subir fotos: solo quien puede editar el aviso -->
    <template v-if="prop.puede_editar">
      <form v-if="disponibles > 0" class="subida" @submit.prevent="subirFotos">
        <input ref="inputFotos" type="file" accept="image/jpeg,image/png,image/webp" multiple @change="elegirFotos" />
        <button class="boton" type="submit" :disabled="!archivos.length">
          Subir {{ archivos.length ? archivos.length : '' }} {{ archivos.length === 1 ? 'foto' : 'fotos' }}
        </button>
      </form>
      <p v-else class="opcional">Ya tienes las {{ MAX_FOTOS }} fotos permitidas. Elimina una para subir otra.</p>
      <p v-if="avisoFotos" class="error">{{ avisoFotos }}</p>
      <ul class="consejos-fotos">
        <li><strong>Tamaño sugerido:</strong> horizontales, 1600 × 1200 px (proporción 4:3), en JPG.</li>
        <li>Hasta {{ MAX_FOTOS }} fotos de máximo 15 MB cada una; las más grandes se reducen solas.</li>
        <li>La primera foto es la portada del aviso: usa la mejor (sala o vista principal).</li>
        <li>Toma las fotos de día, con luces encendidas y espacios ordenados.</li>
      </ul>
    </template>

    <template v-if="prop.video_youtube">
      <h2>Video</h2>
      <div class="video">
        <iframe
          :src="`https://www.youtube-nocookie.com/embed/${prop.video_youtube}`"
          :title="`Video de ${prop.titulo}`"
          allow="accelerometer; encrypted-media; gyroscope; picture-in-picture"
          allowfullscreen
          loading="lazy"
        ></iframe>
      </div>
    </template>

    <AgendarVisita v-if="prop.estado === 'publicado'" :aviso-id="prop.id" />
    <VisitasAviso v-if="prop.puede_editar" :aviso-id="prop.id" />

    <!-- Herramientas de la administración -->
    <template v-if="prop.puede_editar">

      <h2>Texto del anuncio</h2>
      <textarea :value="prop.anuncio" rows="14" readonly></textarea>
      <div class="acciones">
        <button class="boton" type="button" @click="copiar">Copiar anuncio</button>
        <span v-if="copiado">Copiado</span>
      </div>

      <div class="acciones pie">
        <RouterLink class="boton secundario" :to="`/propiedades/${prop.id}/editar`">Editar datos</RouterLink>
        <button class="boton peligro" type="button" @click="eliminar">Eliminar propiedad</button>
      </div>
    </template>
  </template>
</template>
