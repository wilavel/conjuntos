<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api, cop, capitalizar, ESTADOS } from '../api'

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

function elegirFotos(evento) {
  archivos.value = [...evento.target.files]
}

const subirFotos = () =>
  accion(async () => {
    if (!archivos.value.length) return
    prop.value = await api.subirFotos(props.id, archivos.value)
    archivos.value = []
    inputFotos.value.value = ''
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
    router.push('/admin')
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
        <p class="tipo">{{ prop.tipo }}</p>
        <h1>{{ prop.titulo }}</h1>
        <p class="precio">{{ cop(prop.precio) }}</p>
        <p>{{ [prop.direccion, prop.barrio, prop.ciudad].filter(Boolean).join(', ') }}</p>
      </div>
      <select :value="prop.estado" class="estado" :class="prop.estado" @change="cambiarEstado($event.target.value)">
        <option v-for="e in ESTADOS" :key="e" :value="e">{{ capitalizar(e) }}</option>
      </select>
    </div>

    <dl class="ficha">
      <div v-for="[etiqueta, valor] in datos" :key="etiqueta">
        <dt>{{ etiqueta }}</dt>
        <dd>{{ valor }}</dd>
      </div>
    </dl>

    <h2>Fotos</h2>
    <div class="fotos">
      <figure v-for="(f, i) in prop.fotos" :key="f.id">
        <img :src="f.url" :alt="`Foto ${i + 1}`" />
        <button class="borrar" type="button" @click="borrarFoto(f)">Eliminar</button>
      </figure>
    </div>
    <form class="subida" @submit.prevent="subirFotos">
      <input ref="inputFotos" type="file" accept="image/*" multiple @change="elegirFotos" />
      <button class="boton" type="submit" :disabled="!archivos.length">Subir fotos</button>
    </form>

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
