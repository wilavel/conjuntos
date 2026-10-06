<template>
  <nav class="filtros admin-nav" aria-label="Secciones de administración">
    <RouterLink to="/admin/apartamentos" :class="{ activo: $route.path.startsWith('/admin/apartamentos') }">Apartamentos</RouterLink>
    <RouterLink to="/admin/parqueaderos" :class="{ activo: $route.path.startsWith('/admin/parqueaderos') }">Parqueaderos</RouterLink>
    <RouterLink to="/admin/sorteos" :class="{ activo: $route.path.startsWith('/admin/sorteos') }">Sorteos</RouterLink>
    <RouterLink to="/admin/noticias" :class="{ activo: $route.path.startsWith('/admin/noticias') }">Noticias</RouterLink>
    <RouterLink to="/admin/zonas" :class="{ activo: $route.path.startsWith('/admin/zonas') }">Zonas comunes</RouterLink>
    <RouterLink to="/admin/usuarios" :class="{ activo: $route.path.startsWith('/admin/usuarios') }">Usuarios</RouterLink>
  </nav>
</template>
