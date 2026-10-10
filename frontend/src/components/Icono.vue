<script setup>
// Ícono de Material Symbols: <Icono nombre="bed" />
defineProps({ nombre: { type: String, required: true }, relleno: Boolean })
</script>

<template>
  <span class="material-symbols-outlined" :class="{ relleno }" aria-hidden="true">{{ nombre }}</span>
</template>
