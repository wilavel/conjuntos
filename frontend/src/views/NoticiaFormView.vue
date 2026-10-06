<script setup>
import { reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'

const props = defineProps({ id: String })
const router = useRouter()

const form = reactive({ titulo: '', resumen: '', contenido: '', publicada: false })
const imagen = ref(null) // URL de la imagen actual
const archivo = ref(null) // imagen nueva elegida en el formulario
const error = ref('')
const guardando = ref(false)

onMounted(async () => {
  if (!props.id) return
  try {
    const n = await api.noticia(props.id)
    for (const k of Object.keys(form)) form[k] = n[k] ?? form[k]
    imagen.value = n.imagen
  } catch (e) {
    error.value = e.message
  }
})

const elegir = (e) => (archivo.value = e.target.files[0] || null)

async function guardar() {
  guardando.value = true
  error.value = ''
  try {
    const n = props.id ? await api.actualizarNoticia(props.id, form) : await api.crearNoticia(form)
    if (archivo.value) await api.subirImagenNoticia(n.id, archivo.value)
    router.push('/admin/noticias')
  } catch (e) {
    error.value = e.message
    guardando.value = false
  }
}

async function quitarImagen() {
  try {
    imagen.value = (await api.borrarImagenNoticia(props.id)).imagen
  } catch (e) {
    error.value = e.message
  }
}

async function eliminar() {
  if (!confirm('¿Eliminar esta noticia? No se puede deshacer.')) return
  try {
    await api.eliminarNoticia(props.id)
    router.push('/admin/noticias')
  } catch (e) {
    error.value = e.message
  }
}
</script>

<template>
  <h1>{{ id ? 'Editar noticia' : 'Nueva noticia' }}</h1>
  <form class="formulario" @submit.prevent="guardar">
    <label>
      Título
      <input v-model="form.titulo" required maxlength="200" placeholder="Mantenimiento del gimnasio" />
    </label>
    <label>
      Resumen <span class="opcional">(se muestra en las tarjetas, máx. 300 caracteres)</span>
      <textarea v-model="form.resumen" rows="2" maxlength="300"></textarea>
    </label>
    <label>
      Contenido <span class="opcional">(deja una línea en blanco entre párrafos)</span>
      <textarea v-model="form.contenido" rows="12"></textarea>
    </label>

    <fieldset>
      <legend>Imagen de portada</legend>
      <div v-if="imagen" class="fotos">
        <figure>
          <img :src="imagen" alt="Imagen actual de la noticia" />
          <button type="button" class="borrar" @click="quitarImagen">Quitar</button>
        </figure>
      </div>
      <input type="file" accept="image/*" @change="elegir" />
    </fieldset>

    <label class="check">
      <input v-model="form.publicada" type="checkbox" />
      Publicada (visible en el blog y en el inicio)
    </label>

    <p v-if="error" class="error">{{ error }}</p>
    <div class="acciones pie">
      <div class="acciones">
        <button class="boton" type="submit" :disabled="guardando">Guardar</button>
        <RouterLink to="/admin/noticias">Cancelar</RouterLink>
      </div>
      <button v-if="id" type="button" class="boton peligro" @click="eliminar">Eliminar</button>
    </div>
  </form>
</template>
