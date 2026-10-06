import { createRouter, createWebHashHistory } from 'vue-router'
import { esAdmin, puedePublicar } from './sesion'
import HomeView from './views/HomeView.vue'
import PrivadoView from './views/PrivadoView.vue'
import FormView from './views/FormView.vue'
import DetalleView from './views/DetalleView.vue'
import BlogView from './views/BlogView.vue'
import VentaArriendoView from './views/VentaArriendoView.vue'
import NoticiaView from './views/NoticiaView.vue'
import NoticiasAdminView from './views/NoticiasAdminView.vue'
import NoticiaFormView from './views/NoticiaFormView.vue'
import ApartamentosView from './views/ApartamentosView.vue'
import ApartamentoNuevoView from './views/ApartamentoNuevoView.vue'
import ApartamentoView from './views/ApartamentoView.vue'
import ZonasAdminView from './views/ZonasAdminView.vue'
import ZonaFormView from './views/ZonaFormView.vue'
import UsuariosView from './views/UsuariosView.vue'
import ActivarView from './views/ActivarView.vue'
import ParqueaderosView from './views/ParqueaderosView.vue'
import SorteosView from './views/SorteosView.vue'
import SorteoView from './views/SorteoView.vue'

// Historial con # para no necesitar configuración extra en el servidor.
const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', component: HomeView, meta: { ancho: true } },
    { path: '/privado', component: PrivadoView },
    { path: '/activar/:token', component: ActivarView, props: true },
    { path: '/admin', redirect: '/admin/apartamentos' },
    { path: '/nuevo', component: FormView, meta: { publicar: true } },
    { path: '/propiedades/:id', component: DetalleView, props: true },
    { path: '/propiedades/:id/editar', component: FormView, props: true, meta: { publicar: true } },
    { path: '/venta-arriendo', component: VentaArriendoView, meta: { ancho: true } },
    { path: '/noticias', component: BlogView },
    { path: '/noticias/:id', component: NoticiaView, props: true },
    { path: '/admin/noticias', component: NoticiasAdminView, meta: { admin: true } },
    { path: '/admin/noticias/nueva', component: NoticiaFormView, meta: { admin: true } },
    { path: '/admin/noticias/:id/editar', component: NoticiaFormView, props: true, meta: { admin: true } },
    { path: '/admin/apartamentos', component: ApartamentosView, meta: { admin: true } },
    { path: '/admin/apartamentos/nuevo', component: ApartamentoNuevoView, meta: { admin: true } },
    { path: '/admin/apartamentos/:id', component: ApartamentoView, props: true, meta: { admin: true } },
    { path: '/admin/parqueaderos', component: ParqueaderosView, meta: { admin: true } },
    { path: '/admin/sorteos', component: SorteosView, meta: { admin: true } },
    { path: '/admin/sorteos/:id', component: SorteoView, props: true, meta: { admin: true } },
    { path: '/admin/zonas', component: ZonasAdminView, meta: { admin: true } },
    { path: '/admin/zonas/nueva', component: ZonaFormView, meta: { admin: true } },
    { path: '/admin/zonas/:id', component: ZonaFormView, props: true, meta: { admin: true } },
    { path: '/admin/usuarios', component: UsuariosView, meta: { admin: true } },
  ],
  // Con #seccion (ej. /#zona-gimnasio) baja hasta esa sección; si no, arriba.
  // Las zonas se cargan de la API, así que se espera a que la sección exista.
  scrollBehavior: (to) => {
    if (!to.hash) return { top: 0 }
    return new Promise((resolve) => {
      // Espera también las fuentes: al cargar cambian la altura del texto y moverían la sección
      const inicio = Date.now()
      const buscar = () => {
        if (document.querySelector(to.hash)) {
          const listo = document.fonts ? document.fonts.ready : Promise.resolve()
          listo.then(() => resolve({ el: to.hash, top: 84, behavior: 'smooth' }))
        }
        else if (Date.now() - inicio > 3000) resolve({ top: 0 })
        else setTimeout(buscar, 50)
      }
      buscar()
    })
  },
})

// Las pantallas de administración piden iniciar sesión con una cuenta de administrador.
router.beforeEach((to) => {
  if (to.meta.admin && !esAdmin.value) return { path: '/privado', query: { volver: to.fullPath } }
  // Crear o editar avisos: administración o propietarios
  if (to.meta.publicar && !puedePublicar.value) return { path: '/privado', query: { volver: to.fullPath } }
})

export default router
