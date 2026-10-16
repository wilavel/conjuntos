<script setup>
import { DOCUMENTOS } from '../api'

// Campos de un propietario o arrendatario (persona natural o empresa); edita el objeto recibido.
// Con sinIdentificacion se ocultan los campos del documento (en el directorio no se cambian).
const props = defineProps({ persona: { type: Object, required: true }, sinIdentificacion: Boolean })

function cambiarTipo(tipo) {
  props.persona.tipo_persona = tipo
  if (tipo === 'juridica') props.persona.tipo_documento = 'NIT'
  else if (props.persona.tipo_documento === 'NIT') props.persona.tipo_documento = 'CC'
}
</script>

<template>
  <div class="tipo-persona" role="radiogroup" aria-label="Tipo de propietario">
    <button type="button" :class="{ activo: persona.tipo_persona !== 'juridica' }" @click="cambiarTipo('natural')">Persona natural</button>
    <button type="button" :class="{ activo: persona.tipo_persona === 'juridica' }" @click="cambiarTipo('juridica')">Empresa</button>
  </div>
  <div class="grupo">
    <label>
      {{ persona.tipo_persona === 'juridica' ? 'Razón social' : 'Nombre completo' }}
      <input v-model="persona.nombre" required maxlength="150" />
    </label>
    <template v-if="!sinIdentificacion">
      <label>
        Tipo de documento
        <select v-model="persona.tipo_documento" :disabled="persona.tipo_persona === 'juridica'">
          <option v-for="(texto, clave) in DOCUMENTOS" :key="clave" :value="clave" :disabled="clave === 'NIT' && persona.tipo_persona !== 'juridica'">{{ texto }}</option>
        </select>
      </label>
      <label>Número<input v-model="persona.identificacion" required maxlength="30" :placeholder="persona.tipo_persona === 'juridica' ? '900.123.456-7' : '1020304050'" /></label>
    </template>
    <label v-if="persona.tipo_persona === 'juridica'">Representante legal<input v-model="persona.representante" required maxlength="150" /></label>
  </div>
  <div class="grupo">
    <label>Teléfono <span class="opcional">(opcional)</span><input v-model="persona.telefono" maxlength="30" /></label>
    <label>Correo <span class="opcional">(se le crea su cuenta y se le envía el acceso)</span><input v-model="persona.email" type="email" required maxlength="255" /></label>
  </div>
</template>
