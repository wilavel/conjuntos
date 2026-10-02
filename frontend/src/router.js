import { createRouter, createWebHashHistory } from 'vue-router'
import HomeView from './views/HomeView.vue'
import RegistroView from './views/RegistroView.vue'
import ListaView from './views/ListaView.vue'
import FormView from './views/FormView.vue'
import DetalleView from './views/DetalleView.vue'

// Historial con # para no necesitar configuración extra en el servidor.
export default createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', component: HomeView, meta: { ancho: true } },
    { path: '/registro', component: RegistroView },
    { path: '/admin', component: ListaView },
    { path: '/nuevo', component: FormView },
    { path: '/propiedades/:id', component: DetalleView, props: true },
    { path: '/propiedades/:id/editar', component: FormView, props: true },
  ],
  scrollBehavior: () => ({ top: 0 }),
})
