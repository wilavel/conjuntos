<script setup>
import { ref, reactive, onMounted } from 'vue'
import { api } from '../api'
import { iconoZona, ZONAS_BASE } from '../zonas'
import NoticiaTarjeta from '../components/NoticiaTarjeta.vue'
import AvisoTarjeta from '../components/AvisoTarjeta.vue'
import fondoEdificio from '../assets/edificio_editado.jpg'
import logoTrend from '../assets/logo-trend-claro.png'

/* ---------- contenido del conjunto (editable) ---------- */

const CONJUNTO = {
  titulo: 'Un edificio pensado para vivir bien',
  parrafos: [
    'Trend Apartamentos es un conjunto residencial de apartamentos en altura administrado por Alianza Grupo Inmobiliario S.A.S. Reúne apartamentos de distintas áreas y tipologías, con zonas comunes pensadas para el encuentro, el descanso y el día a día de sus residentes.',
    'Desde esta página puedes conocer el conjunto, leer las noticias de la administración, revisar los apartamentos en venta y arriendo y entrar a la zona privada de propietarios y residentes.',
  ],
  datos: [
    ['Administración', 'Alianza Grupo Inmobiliario S.A.S.'],
    ['Tipo de inmueble', 'Apartamentos'],
    ['Anuncios', 'Venta y arriendo'],
    ['Zonas comunes', 'Gimnasio, terrazas, coworking, lavandería y parqueaderos'],
  ],
}


const noticias = ref([]) // últimas noticias publicadas del blog
const avisos = ref([]) // últimos apartamentos publicados en venta o arriendo
const zonas = ref(ZONAS_BASE) // se reemplazan por las de la administración al cargar

// Detalle de cada zona: foto mostrada (índice por zona) y foto abierta en grande
const fotoActiva = reactive({})
const ampliada = ref(null)
const ancla = (z) => ({ path: '/', hash: `#zona-${z.slug}` })
const parrafos = (texto) => (texto || '').split(/\n\s*\n/).map((t) => t.trim()).filter(Boolean)

onMounted(() => {
  api.noticias({ limite: 3 }).then((n) => (noticias.value = n)).catch(() => {})
  api.listar({ estado: 'publicado' }).then((a) => (avisos.value = a.slice(0, 3))).catch(() => {})
  api.zonas().then((z) => z.length && (zonas.value = z)).catch(() => {})
})
</script>

<template>
  <section class="hero">
    <div class="hero-fondo" :style="{ backgroundImage: `url(${fondoEdificio})` }" aria-hidden="true"></div>
    <div class="hero-velo" aria-hidden="true"></div>

    <div class="hero-contenido contenedor">
      <div class="hero-texto">
        <img class="hero-logo" :src="logoTrend" alt="Trend Apartamentos" />
        <span class="pildora"><span class="punto"></span>Administración Alianza Grupo Inmobiliario</span>
        <h1>Bienvenido a <em>Trend</em>, tu comunidad.</h1>
        <p>
          Espacio de propietarios y residentes del conjunto Trend Apartamentos: conoce el edificio,
          sus zonas comunes y las noticias de la administración.
        </p>
        <div class="hero-acciones">
          <RouterLink class="boton" :to="{ path: '/', hash: '#conjunto' }">
            Conocer el conjunto <span class="flecha" aria-hidden="true">↓</span>
          </RouterLink>
          <RouterLink class="boton boton-claro" to="/noticias">Ver noticias</RouterLink>
        </div>
      </div>
    </div>

    <div class="contenedor hero-pie">
      <ul v-if="zonas.length" class="hero-zonas" aria-label="Zonas comunes">
        <li v-for="z in zonas" :key="z.id">
          <RouterLink :to="ancla(z)">
            <span class="hero-zona-icono" v-html="iconoZona(z.icono)"></span>{{ z.nombre }}
          </RouterLink>
        </li>
      </ul>
    </div>
  </section>

  <section id="conjunto" class="seccion">
    <div class="contenedor">
      <div class="conjunto">
        <div class="conjunto-texto">
          <span class="rotulo">El conjunto</span>
          <h2>{{ CONJUNTO.titulo }}</h2>
          <p v-for="texto in CONJUNTO.parrafos" :key="texto">{{ texto }}</p>
        </div>
        <dl class="conjunto-datos">
          <div v-for="[etiqueta, valor] in CONJUNTO.datos" :key="etiqueta">
            <dt>{{ etiqueta }}</dt>
            <dd>{{ valor }}</dd>
          </div>
        </dl>
      </div>

      <div id="zonas" class="zonas">
        <div class="zonas-cabeza">
          <div>
            <span class="rotulo">Zonas comunes</span>
            <h3>Espacios que puedes disfrutar</h3>
          </div>
          <p class="zonas-nota">Haz clic en cada espacio para ver su descripción y sus fotos.</p>
        </div>
        <div class="zonas-grid">
          <RouterLink v-for="z in zonas" :key="z.id" class="zona" :to="ancla(z)">
            <span class="zona-icono" v-html="iconoZona(z.icono)"></span>
            <h4>{{ z.nombre }}</h4>
            <p>{{ z.resumen }}</p>
            <span class="noticia-leer">Ver detalle <span class="flecha" aria-hidden="true">↓</span></span>
          </RouterLink>
        </div>
      </div>

      <!-- Detalle de cada zona: los botones de arriba bajan hasta aquí -->
      <div class="zonas-detalle">
        <article v-for="z in zonas" :id="`zona-${z.slug}`" :key="z.id" class="zona-fila">
          <div class="zona-fila-fotos">
            <button
              v-if="z.fotos.length"
              type="button"
              class="zona-fila-principal"
              @click="ampliada = z.fotos[fotoActiva[z.slug] || 0].url"
            >
              <img :src="z.fotos[fotoActiva[z.slug] || 0].url" :alt="z.nombre" loading="lazy" />
            </button>
            <div v-else class="zona-fila-principal zona-fila-sin-foto" v-html="iconoZona(z.icono)"></div>
            <div v-if="z.fotos.length > 1" class="zona-fila-miniaturas">
              <button
                v-for="(f, i) in z.fotos"
                :key="f.id"
                type="button"
                :class="{ activo: (fotoActiva[z.slug] || 0) === i }"
                :aria-label="`Ver foto ${i + 1} de ${z.nombre}`"
                @click="fotoActiva[z.slug] = i"
              >
                <img :src="f.url" alt="" loading="lazy" />
              </button>
            </div>
          </div>
          <div class="zona-fila-texto">
            <span class="zona-icono" v-html="iconoZona(z.icono)"></span>
            <h3>{{ z.nombre }}</h3>
            <p v-for="(texto, i) in parrafos(z.descripcion || z.resumen)" :key="i">{{ texto }}</p>
            <p v-if="z.horario" class="zona-fila-horario"><strong>Horario:</strong> {{ z.horario }}</p>
            <RouterLink class="enlace-subir" :to="{ path: '/', hash: '#zonas' }">↑ Volver a los espacios</RouterLink>
          </div>
        </article>
      </div>

      <div v-if="ampliada" class="visor" role="dialog" aria-label="Foto ampliada" @click="ampliada = null">
        <img :src="ampliada" alt="" />
        <button type="button" class="visor-cerrar" aria-label="Cerrar">×</button>
      </div>
    </div>
  </section>

  <section v-if="avisos.length" class="seccion">
    <div class="contenedor">
      <div class="seccion-cabeza">
        <div>
          <span class="rotulo">Venta y arriendo</span>
          <h2>Apartamentos disponibles</h2>
        </div>
        <RouterLink class="boton secundario" to="/venta-arriendo">
          Ver todos <span class="flecha" aria-hidden="true">→</span>
        </RouterLink>
      </div>
      <div class="tarjetas">
        <AvisoTarjeta v-for="a in avisos" :key="a.id" :aviso="a" />
      </div>
    </div>
  </section>

  <section v-if="noticias.length" class="seccion noticias-inicio">
    <div class="contenedor">
      <div class="seccion-cabeza">
        <div>
          <span class="rotulo">Blog</span>
          <h2>Últimas noticias</h2>
        </div>
        <RouterLink class="boton secundario" to="/noticias">
          Ver todas <span class="flecha" aria-hidden="true">→</span>
        </RouterLink>
      </div>
      <div class="tarjetas">
        <NoticiaTarjeta v-for="n in noticias" :key="n.id" :noticia="n" />
      </div>
    </div>
  </section>

  <section class="seccion seccion-privada">
    <div class="contenedor">
      <div class="zona-privada zona-privada-inicio">
        <div>
          <span class="rotulo">Residentes</span>
          <h3>Zona privada de propietarios</h3>
          <p>
            Actas, reglamento de propiedad horizontal, cuotas de administración, PQRS y reserva de
            zonas comunes. Solo para propietarios y residentes registrados.
          </p>
        </div>
        <RouterLink class="boton" to="/privado">
          Entrar a la zona privada <span class="flecha" aria-hidden="true">→</span>
        </RouterLink>
      </div>
    </div>
  </section>

  <section class="llamado seccion">
    <div class="contenedor">
      <div>
        <span class="rotulo">Comunidad</span>
        <h2>Tú también haces parte de Trend Apartamentos.</h2>
        <p>
          Propietarios y arrendatarios tienen acceso a la zona privada: actas, reglamento, cuotas,
          PQRS y reserva de zonas comunes.
        </p>
      </div>
      <div class="llamado-caja">
        <h3>Ingresa a tu cuenta</h3>
        <p>¿Aún no tienes usuario? Solicítalo a la administración del conjunto.</p>
        <RouterLink class="boton" to="/privado">Ingresar <span class="flecha" aria-hidden="true">→</span></RouterLink>
      </div>
    </div>
  </section>
</template>
