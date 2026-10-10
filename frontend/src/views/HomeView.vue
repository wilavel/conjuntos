<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { api } from '../api'
import { simboloZona, ZONAS_BASE } from '../zonas'
import Icono from '../components/Icono.vue'
import NoticiaTarjeta from '../components/NoticiaTarjeta.vue'
import AvisoTarjeta from '../components/AvisoTarjeta.vue'
import fondoEdificio from '../assets/edificio_editado.jpg'
import fotoEdificio from '../assets/edificio-trend.webp'

/* ---------- contenido del conjunto (editable) ---------- */

const CONJUNTO = {
  titulo: 'Un edificio pensado para vivir bien',
  parrafos: [
    'Trend Apartamentos es un conjunto residencial de apartamentos en altura administrado por Alianza Grupo Inmobiliario S.A.S. Reúne apartamentos de distintas áreas y tipologías, con zonas comunes pensadas para el encuentro, el descanso y el día a día de sus residentes.',
    'Desde esta página puedes conocer el conjunto, leer las noticias de la administración, revisar los apartamentos en venta y arriendo y entrar a la zona privada de propietarios y residentes.',
  ],
  datos: [
    ['admin_panel_settings', 'Administración', 'Alianza Grupo Inmobiliario S.A.S.'],
    ['apartment', 'Tipo de inmueble', 'Apartamentos en altura, una sola torre'],
    ['location_on', 'Ubicación', 'Bogotá, Colombia'],
    ['deck', 'Zonas comunes', 'Gimnasio, terrazas, coworking, lavandería y parqueaderos'],
  ],
}


const noticias = ref([]) // últimas noticias publicadas del blog
const avisos = ref([]) // últimos apartamentos publicados en venta o arriendo
const totalAvisos = ref(0)
const zonas = ref(ZONAS_BASE) // se reemplazan por las de la administración al cargar

// Detalle de cada zona: foto mostrada (índice por zona) y foto abierta en grande
const fotoActiva = reactive({})
const ampliada = ref(null)
const ancla = (z) => ({ path: '/', hash: `#zona-${z.slug}` })
const parrafos = (texto) => (texto || '').split(/\n\s*\n/).map((t) => t.trim()).filter(Boolean)

onMounted(() => {
  api.noticias({ limite: 3 }).then((n) => (noticias.value = n)).catch(() => {})
  api.listar({ estado: 'publicado' }).then((a) => {
    totalAvisos.value = a.length
    avisos.value = a.slice(0, 3)
  }).catch(() => {})
  api.zonas().then((z) => z.length && (zonas.value = z)).catch(() => {})
})

// Mosaico de 4 columnas: la primera zona ocupa 2x2 y las 4 siguientes llenan su costado.
// Si en la última fila sobran huecos, la última zona se estira para completarla.
const anchoUltima = computed(() => {
  const resto = (zonas.value.length - 5) % 4
  return zonas.value.length > 5 && resto ? `ancho-${5 - resto}` : ''
})

// Franja de valor: lo que ofrece la página (todo es real)
const VALORES = [
  ['deck', 'Zonas comunes', 'Gimnasio, terrazas, coworking y más'],
  ['real_estate_agent', 'Venta y arriendo', 'Avisos de los propietarios del edificio'],
  ['calendar_month', 'Visitas en línea', 'Agenda tu visita desde cada aviso'],
  ['lock', 'Zona privada', 'Actas, PQRS, sorteos y tu cuenta'],
]
</script>

<template>
  <!-- PORTADA: texto a la izquierda, foto del edificio en tarjeta a la derecha -->
  <section class="portada">
    <!-- Foto del edificio de fondo, fundida en blanco hacia el texto -->
    <div class="portada-fondo" :style="{ backgroundImage: `url(${fondoEdificio})` }" aria-hidden="true"></div>
    <div class="portada-velo" aria-hidden="true"></div>
    <div class="portada-brillo" aria-hidden="true"></div>
    <div class="contenedor portada-interior">
      <div class="pildora-badge">
        <span class="punto"></span>
        <span class="pildora-badge-texto">Trend Apartamentos · Bogotá</span>
        <span class="pildora-badge-extra">Administración Alianza Grupo Inmobiliario</span>
      </div>
      <div class="portada-grid">
        <div class="portada-texto">
          <span class="etiqueta">Conjunto residencial · Una sola torre</span>
          <h1>Bienvenido a <span class="subrayado">Trend</span>, tu comunidad</h1>
          <p>
            Espacio de propietarios y residentes del conjunto Trend Apartamentos: conoce el edificio,
            sus zonas comunes, los apartamentos en venta y arriendo y las noticias de la administración.
          </p>
          <div class="portada-acciones">
            <RouterLink class="boton boton-grande" :to="{ path: '/', hash: '#conjunto' }">
              Conocer el conjunto <Icono nombre="arrow_downward" />
            </RouterLink>
            <RouterLink class="boton secundario boton-grande" to="/venta-arriendo">
              <Icono nombre="real_estate_agent" /> Venta y arriendo
            </RouterLink>
          </div>
          <dl class="metricas">
            <div><dd>{{ zonas.length }}</dd><dt>Zonas comunes</dt></div>
            <div><dd>{{ totalAvisos }}</dd><dt>{{ totalAvisos === 1 ? 'Apartamento disponible' : 'Apartamentos disponibles' }}</dt></div>
            <div><dd>24/7</dd><dt>Zona privada en línea</dt></div>
          </dl>
        </div>
        <div class="portada-visual">
          <div class="portada-tarjeta">
            <span class="icono-caja grande"><Icono nombre="apartment" /></span>
            <span class="portada-tarjeta-texto">
              <strong>Trend Apartamentos</strong>
              <small>Bogotá, Colombia</small>
            </span>
            <span class="portada-tarjeta-dato">
              <small>Zonas</small>
              <strong>{{ zonas.length }} espacios</strong>
            </span>
          </div>
          <div class="portada-sello">
            <span><Icono nombre="verified" /> Administración</span>
            <strong>Alianza Grupo Inmobiliario S.A.S.</strong>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- FRANJA DE VALOR -->
  <section class="franja">
    <div class="contenedor franja-grid">
      <div v-for="[icono, titulo, texto] in VALORES" :key="titulo" class="franja-item">
        <span class="icono-circulo"><Icono :nombre="icono" /></span>
        <span><strong>{{ titulo }}</strong><small>{{ texto }}</small></span>
      </div>
    </div>
  </section>

  <!-- EL CONJUNTO: datos a la izquierda, foto a la derecha -->
  <section id="conjunto" class="seccion">
    <div class="contenedor conjunto-grid">
      <div class="conjunto-texto">
        <span class="etiqueta">El conjunto</span>
        <h2>{{ CONJUNTO.titulo }}</h2>
        <p v-for="texto in CONJUNTO.parrafos" :key="texto">{{ texto }}</p>
        <ul class="lista-datos">
          <li v-for="[icono, etiqueta, valor] in CONJUNTO.datos" :key="etiqueta">
            <span class="icono-caja"><Icono :nombre="icono" /></span>
            <span><strong>{{ etiqueta }}</strong><small>{{ valor }}</small></span>
          </li>
        </ul>
      </div>
      <figure class="conjunto-foto">
        <img :src="fotoEdificio" alt="Torre Trend Apartamentos" loading="lazy" />
        <figcaption><Icono nombre="location_on" /> Trend Apartamentos · Bogotá</figcaption>
      </figure>
    </div>
  </section>

  <!-- ZONAS COMUNES: mosaico (bento) que baja al detalle de cada espacio -->
  <section id="zonas" class="seccion seccion-blanca">
    <div class="contenedor">
      <div class="seccion-titulo centrado">
        <span class="etiqueta">Zonas comunes</span>
        <h2>Espacios que puedes disfrutar</h2>
        <p>Haz clic en cada espacio para ver su descripción, su horario y sus fotos.</p>
      </div>
      <div class="bento">
        <RouterLink v-for="(z, i) in zonas" :key="z.id" class="bento-item" :class="[{ grande: i === 0 }, i === zonas.length - 1 && anchoUltima]" :to="ancla(z)">
          <img v-if="z.fotos.length" :src="z.fotos[0].url" :alt="z.nombre" loading="lazy" />
          <span v-else class="bento-sin-foto"><Icono :nombre="simboloZona(z.icono)" /></span>
          <span class="bento-velo"></span>
          <span class="bento-texto">
            <Icono :nombre="simboloZona(z.icono)" />
            <strong>{{ z.nombre }}</strong>
            <small>{{ z.resumen }}</small>
            <span class="bento-ver">Ver detalle <Icono nombre="arrow_downward" /></span>
          </span>
        </RouterLink>
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
            <div v-else class="zona-fila-principal zona-fila-sin-foto"><Icono :nombre="simboloZona(z.icono)" /></div>
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
            <span class="icono-caja"><Icono :nombre="simboloZona(z.icono)" /></span>
            <h3>{{ z.nombre }}</h3>
            <p v-for="(texto, i) in parrafos(z.descripcion || z.resumen)" :key="i">{{ texto }}</p>
            <p v-if="z.horario" class="zona-fila-horario"><Icono nombre="schedule" /> {{ z.horario }}</p>
            <RouterLink v-if="z.reservable && z.franjas?.length" class="boton" :to="{ path: '/privado', query: { reservar: z.slug } }">
              <Icono nombre="event_available" /> Reservar · 1 o 2 horas
            </RouterLink>
            <RouterLink class="enlace-subir" :to="{ path: '/', hash: '#zonas' }"><Icono nombre="arrow_upward" /> Volver a los espacios</RouterLink>
          </div>
        </article>
      </div>

      <div v-if="ampliada" class="visor" role="dialog" aria-label="Foto ampliada" @click="ampliada = null">
        <img :src="ampliada" alt="" />
        <button type="button" class="visor-cerrar" aria-label="Cerrar">×</button>
      </div>
    </div>
  </section>

  <!-- APARTAMENTOS DISPONIBLES -->
  <section v-if="avisos.length" class="seccion">
    <div class="contenedor">
      <div class="seccion-titulo">
        <div>
          <span class="etiqueta">Venta y arriendo</span>
          <h2>Apartamentos <span class="texto-acento">disponibles</span></h2>
        </div>
        <p>Avisos publicados por los propietarios del edificio. Agenda tu visita desde cada aviso.</p>
      </div>
      <div class="tarjetas">
        <AvisoTarjeta v-for="a in avisos" :key="a.id" :aviso="a" />
      </div>
      <div class="centrado-acciones">
        <RouterLink class="boton secundario" to="/venta-arriendo">Ver todos los apartamentos <Icono nombre="arrow_forward" /></RouterLink>
      </div>
    </div>
  </section>

  <!-- NOTICIAS -->
  <section v-if="noticias.length" class="seccion seccion-blanca">
    <div class="contenedor">
      <div class="seccion-titulo">
        <div>
          <span class="etiqueta">Blog</span>
          <h2>Últimas noticias</h2>
        </div>
        <RouterLink class="boton secundario" to="/noticias">Ver todas <Icono nombre="arrow_forward" /></RouterLink>
      </div>
      <div class="tarjetas">
        <NoticiaTarjeta v-for="n in noticias" :key="n.id" :noticia="n" />
      </div>
    </div>
  </section>

  <!-- LLAMADO: ZONA PRIVADA -->
  <section class="seccion">
    <div class="contenedor">
      <div class="llamado-caja">
        <span class="icono-circulo grande"><Icono nombre="lock" /></span>
        <div>
          <h3>Zona privada de propietarios y residentes</h3>
          <p>Actas, reglamento, cuotas, PQRS, sorteos de parqueaderos y tus avisos. Si aún no tienes usuario, solicítalo a la administración.</p>
        </div>
        <RouterLink class="boton oscuro" to="/privado">Entrar a la zona privada</RouterLink>
      </div>
    </div>
  </section>
</template>
