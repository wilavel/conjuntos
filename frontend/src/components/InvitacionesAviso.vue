<script setup>
import { ref } from 'vue'
import Icono from './Icono.vue'

// Resultado de crear cuentas: correo enviado, o enlace para compartir a mano si no hay SMTP
defineProps({ invitaciones: { type: Array, required: true } })
defineEmits(['cerrar'])

const copiado = ref('')
async function copiar(enlace) {
  await navigator.clipboard.writeText(enlace)
  copiado.value = enlace
  setTimeout(() => (copiado.value = ''), 1800)
}
</script>

<template>
  <div v-if="invitaciones.length" class="invitaciones">
    <div class="invitaciones-cabeza">
      <strong>Accesos a la página</strong>
      <button type="button" class="enlace" @click="$emit('cerrar')">Cerrar</button>
    </div>
    <ul>
      <li v-for="i in invitaciones" :key="i.email">
        <!-- La persona ya tenía cuenta: solo se le avisa que quedó en el apartamento -->
        <template v-if="i.vinculada">
          <span>
            <Icono :nombre="i.enviado ? 'mark_email_read' : 'info'" />
            <strong>{{ i.email }}</strong> ya tenía cuenta: no se creó otra.
            <template v-if="i.enviado">Se le envió un correo avisando que es {{ i.rol }} del Apto {{ i.apartamento }}.</template>
            <template v-else>No se pudo enviar el aviso por correo; entra con su contraseña de siempre.</template>
          </span>
        </template>
        <template v-else-if="i.enviado">
          <Icono nombre="mark_email_read" /> {{ i.nueva ? 'Cuenta creada y correo' : 'Correo' }} enviado a <strong>{{ i.email }}</strong> con el
          enlace para crear su contraseña.
        </template>
        <template v-else>
          <span>
            {{ i.nueva ? 'Cuenta creada para' : 'Enlace de acceso para' }} <strong>{{ i.email }}</strong>, pero el
            correo no se pudo enviar (falta configurar el correo saliente). Compártele este enlace:
          </span>
          <span class="invitacion-enlace">
            <input :value="i.enlace" readonly @focus="$event.target.select()" />
            <button type="button" class="boton secundario" @click="copiar(i.enlace)">
              {{ copiado === i.enlace ? 'Copiado' : 'Copiar' }}
            </button>
          </span>
        </template>
      </li>
    </ul>
  </div>
</template>
