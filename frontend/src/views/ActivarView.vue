<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { guardarSesion } from '../sesion'

// Página del enlace que llega por correo: la persona crea su contraseña
const props = defineProps({ token: String })
const router = useRouter()

const datos = reactive({ clave: '', repetir: '' })
const error = ref('')
const enviando = ref(false)

async function activar() {
  error.value = ''
  if (datos.clave !== datos.repetir) {
    error.value = 'Las contraseñas no coinciden'
    return
  }
  enviando.value = true
  try {
    guardarSesion(await api.activar(props.token, datos.clave))
    router.push('/privado')
  } catch (e) {
    error.value = e.message
    enviando.value = false
  }
}
</script>

<template>
  <div class="privado">
    <form class="formulario" @submit.prevent="activar">
      <div>
        <span class="rotulo">Bienvenido</span>
        <h1>Crea tu contraseña</h1>
        <p class="intro">
          Con ella entrarás a la zona privada de Trend Apartamentos. Usa al menos 8 caracteres.
        </p>
      </div>
      <label>
        Contraseña
        <input v-model="datos.clave" type="password" required minlength="8" maxlength="128" autocomplete="new-password" />
      </label>
      <label>
        Repite la contraseña
        <input v-model="datos.repetir" type="password" required minlength="8" autocomplete="new-password" />
      </label>
      <p v-if="error" class="error">{{ error }}</p>
      <button class="boton" type="submit" :disabled="enviando">
        {{ enviando ? 'Guardando…' : 'Crear contraseña y entrar' }} <span class="flecha" aria-hidden="true">→</span>
      </button>
    </form>
  </div>
</template>
