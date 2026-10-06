<script setup>
import { reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { ICONOS_ZONA } from '../zonas'

const props = defineProps({ id: String })
const router = useRouter()

const form = reactive({ nombre: '', icono: 'gimnasio', resumen: '', descripcion: '', horario: '', orden: 0 })
const zona = ref(null) // zona guardada (para fotos y enlace público)
const archivos = ref([])
const inputFotos = ref(null)
const error = ref('')
const aviso = ref('')
const guardando = ref(false)

function mostrar(z) {
  zona.value = z
  for (const k of Object.keys(form)) form[k] = z[k] ?? form[k]
}

onMounted(async () => {
  if (!props.id) return
  try {
    // La API pública busca por slug; aquí se busca por id en el listado
    const z = (await api.zonas()).find((x) => String(x.id) === props.id)
    if (!z) throw new Error('Zona no encontrada')
    mostrar(z)
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
      const datos = { ...form, orden: Number(form.orden) || 0 }
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
    <label>
      Horario <span class="opcional">(opcional)</span>
      <input v-model="form.horario" maxlength="200" placeholder="Lunes a domingo, 5:00 a. m. a 10:00 p. m." />
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

    <div class="acciones pie">
      <span></span>
      <button class="boton peligro" type="button" @click="eliminar">Eliminar zona</button>
    </div>
  </template>
</template>
