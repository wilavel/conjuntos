<script setup>
import { ref, reactive } from 'vue'
import { api } from '../api'

const datos = reactive({ nombre: '', email: '', telefono: '', clave: '' })
const confirmacion = ref('')
const error = ref('')
const enviando = ref(false)
const creado = ref(null)

async function registrar() {
  error.value = ''
  if (datos.clave !== confirmacion.value) {
    error.value = 'Las contraseñas no coinciden'
    return
  }
  enviando.value = true
  try {
    creado.value = await api.registrar(datos)
  } catch (e) {
    error.value = e.message
  } finally {
    enviando.value = false
  }
}
</script>

<template>
  <div class="registro">
    <div v-if="creado" class="formulario">
      <span class="rotulo">Cuenta creada</span>
      <h1>Bienvenido, {{ creado.nombre }}</h1>
      <p>Tu cuenta quedó creada con el correo <strong>{{ creado.email }}</strong>.</p>
      <RouterLink class="boton" to="/">Ver propiedades</RouterLink>
    </div>

    <form v-else class="formulario" @submit.prevent="registrar">
      <div>
        <span class="rotulo">Registro</span>
        <h1>Crea tu cuenta</h1>
        <p class="intro">Es gratis y toma menos de un minuto.</p>
      </div>
      <label>
        Nombre
        <input v-model="datos.nombre" required maxlength="100" autocomplete="name" />
      </label>
      <label>
        Correo electrónico
        <input v-model="datos.email" type="email" required maxlength="255" autocomplete="email" />
      </label>
      <label>
        <span>Teléfono <span class="opcional">(opcional)</span></span>
        <input v-model="datos.telefono" type="tel" maxlength="30" autocomplete="tel" />
      </label>
      <div class="grupo">
        <label>
          Contraseña
          <input v-model="datos.clave" type="password" required minlength="8" maxlength="128" autocomplete="new-password" />
        </label>
        <label>
          Repite la contraseña
          <input v-model="confirmacion" type="password" required minlength="8" autocomplete="new-password" />
        </label>
      </div>
      <p v-if="error" class="error">{{ error }}</p>
      <button class="boton" type="submit" :disabled="enviando">
        {{ enviando ? 'Creando cuenta…' : 'Registrarme' }} <span class="flecha" aria-hidden="true">→</span>
      </button>
    </form>
  </div>
</template>
