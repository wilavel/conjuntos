<script setup>
// Campos de un propietario o arrendatario; edita directamente el objeto recibido.
defineProps({ persona: { type: Object, required: true } })
</script>

<template>
  <div class="grupo">
    <label>Nombre completo<input v-model="persona.nombre" required maxlength="150" /></label>
    <label>Identificación<input v-model="persona.identificacion" required maxlength="30" placeholder="1020304050" /></label>
    <label>Teléfono <span class="opcional">(opcional)</span><input v-model="persona.telefono" maxlength="30" /></label>
    <label>Correo <span class="opcional">(se le crea su cuenta y se le envía el acceso)</span><input v-model="persona.email" type="email" required maxlength="255" /></label>
  </div>
</template>
