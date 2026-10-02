<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { api, cop } from '../api'

const propiedades = ref([])
const cargando = ref(true)
const error = ref('')
const verFiltros = ref(false) // en móvil el panel de filtros se abre con un botón

const VACIO = {
  texto: '',
  tipo: '',
  ciudad: '',
  precioMin: '',
  precioMax: '',
  habitaciones: 0,
  banos: 0,
  areaMin: '',
  estrato: '',
  parqueadero: false,
}
const f = reactive({ ...VACIO })
const orden = ref('recientes')

const ORDENES = {
  recientes: (a, b) => b.id - a.id,
  menor: (a, b) => a.precio - b.precio,
  mayor: (a, b) => b.precio - a.precio,
  area: (a, b) => area(b) - area(a),
}

onMounted(async () => {
  try {
    propiedades.value = await api.listar({ estado: 'publicado' })
  } catch (e) {
    error.value = e.message
  } finally {
    cargando.value = false
  }
})

const area = (p) => p.area_construida_m2 || p.area_lote_m2 || 0

// Silueta nocturna de La Candelaria para la portada (ancho y alto de cada fachada)
const casas = []
for (let x = -10, i = 0; x < 1210; i++) {
  const w = 44 + ((i * 17) % 28)
  casas.push({ x, w, h: 26 + ((i * 11) % 20), luz: i % 3 !== 1 })
  x += w + 3
}
// Torres del Parque (Salmona): siluetas escalonadas en ladrillo
const torres = [
  { x: 830, top: 150, w: 46 },
  { x: 884, top: 128, w: 52 },
  { x: 944, top: 165, w: 44 },
]
const escalones = (t) =>
  `M${t.x} 300V${t.top + 24}H${t.x + 8}V${t.top + 12}H${t.x + 18}V${t.top}H${t.x + t.w}V300Z`

const catalogo = ref(null)
const buscar = () => catalogo.value.scrollIntoView({ behavior: 'smooth' })
const millones = (v) => `$${Math.round(v / 1e6).toLocaleString('es-CO')} M`

// Solo se ofrecen los tipos y ciudades que tienen propiedades publicadas
function conteo(campo) {
  const c = {}
  propiedades.value.forEach((p) => (c[p[campo]] = (c[p[campo]] || 0) + 1))
  return Object.entries(c).sort(([a], [b]) => a.localeCompare(b))
}
const tipos = computed(() => conteo('tipo'))
const ciudades = computed(() => conteo('ciudad').map(([c]) => c))

const filtradas = computed(() => {
  const texto = f.texto.trim().toLowerCase()
  return propiedades.value
    .filter((p) => {
      if (texto && ![p.titulo, p.ciudad, p.barrio, p.descripcion].join(' ').toLowerCase().includes(texto)) return false
      if (f.tipo && p.tipo !== f.tipo) return false
      if (f.ciudad && p.ciudad !== f.ciudad) return false
      if (f.precioMin !== '' && p.precio < f.precioMin) return false
      if (f.precioMax !== '' && p.precio > f.precioMax) return false
      if (p.habitaciones < f.habitaciones) return false
      if (p.banos < f.banos) return false
      if (f.areaMin !== '' && area(p) < f.areaMin) return false
      if (f.estrato && p.estrato !== f.estrato) return false
      if (f.parqueadero && !p.parqueaderos) return false
      return true
    })
    .sort(ORDENES[orden.value])
})

const cifras = computed(() => {
  const ps = propiedades.value
  return [
    [ps.length, 'Propiedades disponibles'],
    [ps.length ? millones(Math.min(...ps.map((p) => p.precio))) : '—', 'Precio desde'],
    [tipos.value.length, 'Tipos de inmueble'],
    [ciudades.value.length, ciudades.value.length === 1 ? 'Ciudad' : 'Ciudades'],
  ]
})

const hayFiltros = computed(() => Object.keys(VACIO).some((k) => f[k] !== VACIO[k]))
const limpiar = () => Object.assign(f, VACIO)
</script>

<template>
  <section class="hero">
    <img
      class="hero-foto"
      src="https://images.unsplash.com/photo-1600585154340-be6161a56a0c?q=80&w=2000&auto=format&fit=crop"
      alt=""
    />
    <div class="hero-velo"></div>
    <div class="hero-trama"></div>


    <div class="hero-contenido contenedor">
      <span class="pildora"><span class="punto"></span>Bogotá · 2.600 msnm</span>
      <h1>Tu hogar entre la <em>niebla</em> y el <u>ladrillo</u>.</h1>
      <p>
        Apartamentos, casas y locales frente a los Cerros Orientales. Encuentra el tuyo, del centro
        histórico a la sabana.
      </p>
      <form class="buscador" role="search" @submit.prevent="buscar">
        <input v-model="f.texto" type="search" placeholder="Barrio, ciudad o palabra clave" aria-label="Buscar" />
        <button class="boton" type="submit"><span>Buscar</span> <span class="flecha" aria-hidden="true">↓</span></button>
      </form>

      <dl class="cifras">
        <div v-for="[valor, etiqueta] in cifras" :key="etiqueta">
          <dt>{{ etiqueta }}</dt>
          <dd>{{ cargando ? '—' : valor }}</dd>
        </div>
      </dl>
    </div>
  </section>

<!-- Cerros orientales, Monserrate, Torres del Parque y La Candelaria de noche -->
  <svg class="horizonte" viewBox="0 50 1200 250" aria-hidden="true">
    <defs>
      <pattern id="ventanas" width="8" height="9" patternUnits="userSpaceOnUse">
        <rect x="2" y="3" width="4" height="4" fill="#d98a39" opacity=".55" />
      </pattern>
    </defs>
    <path d="M0 170L90 138L170 150L260 108L340 124L420 96L520 118L600 92L700 114L800 84L900 110L1000 80L1100 104L1200 88V300H0Z" fill="#343a37" />
    <path d="M0 222C120 202 210 190 300 170C380 160 425 140 470 102L500 90L530 102C600 132 650 140 720 150C800 160 860 122 920 96L950 88L980 100C1050 140 1120 165 1200 176V300H0Z" fill="#2d3b32" />
    <g fill="#f7f5f0" opacity=".85">
      <rect x="490" y="76" width="22" height="14" />
      <polygon points="488,77 501,69 514,77" fill="#b85032" />
      <rect x="497" y="63" width="7" height="12" />
      <polygon points="496,64 500.5,58 505,64" fill="#b85032" />
    </g>
    <rect x="949" y="72" width="3" height="16" fill="#f7f5f0" opacity=".7" />
    <rect x="944" y="76" width="13" height="3" fill="#f7f5f0" opacity=".7" />
    <path d="M0 252C200 232 350 226 500 236C700 249 900 226 1200 242V300H0Z" fill="#25252b" />

    <g v-for="t in torres" :key="t.x">
      <path :d="escalones(t)" fill="#8c3820" />
      <path :d="escalones(t)" fill="url(#ventanas)" />
    </g>

    <g fill="#2d2d34">
      <rect x="330" y="196" width="18" height="104" />
      <rect x="402" y="196" width="18" height="104" />
      <rect x="346" y="222" width="58" height="78" />
      <polygon points="344,224 375,202 406,224" />
      <circle cx="339" cy="192" r="8" /><circle cx="411" cy="192" r="8" />
      <rect x="365" y="250" width="20" height="30" rx="10" fill="#d98a39" opacity=".5" />
    </g>

    <g v-for="c in casas" :key="c.x" :transform="`translate(${c.x} ${300 - c.h})`">
      <polygon :points="`-3,5 ${c.w + 3},5 ${c.w - 5},-4 5,-4`" fill="#5a2a1a" />
      <rect y="5" :width="c.w" :height="c.h - 5" fill="#1e1e22" />
      <template v-if="c.h > 34 && c.luz">
        <rect x="6" y="11" width="8" height="9" fill="#d98a39" opacity=".7" />
        <rect :x="c.w - 14" y="11" width="8" height="9" fill="#d98a39" opacity=".45" />
      </template>
    </g>
  </svg>

  <section ref="catalogo" class="seccion">
    <div class="contenedor">
      <div class="seccion-cabeza">
        <div>
          <span class="rotulo">Catálogo</span>
          <h2>Propiedades disponibles</h2>
        </div>
        <nav v-if="tipos.length" class="chips" aria-label="Tipo de propiedad">
          <button type="button" :class="{ activo: !f.tipo }" @click="f.tipo = ''">
            Todos <span>{{ propiedades.length }}</span>
          </button>
          <button v-for="[t, n] in tipos" :key="t" type="button" :class="{ activo: f.tipo === t }" @click="f.tipo = t">
            {{ t }} <span>{{ n }}</span>
          </button>
        </nav>
      </div>

      <div class="catalogo">
        <aside class="panel" :class="{ abierto: verFiltros }">
          <div class="panel-cabeza">
            <h2>Filtros</h2>
            <button v-if="hayFiltros" type="button" class="enlace" @click="limpiar">Limpiar</button>
          </div>

          <label v-if="ciudades.length > 1">
            Ciudad
            <select v-model="f.ciudad">
              <option value="">Todas</option>
              <option v-for="c in ciudades" :key="c">{{ c }}</option>
            </select>
          </label>

          <fieldset class="rango">
            <legend>Precio</legend>
            <input v-model.number="f.precioMin" type="number" min="0" step="1000000" placeholder="Mínimo" aria-label="Precio mínimo" />
            <input v-model.number="f.precioMax" type="number" min="0" step="1000000" placeholder="Máximo" aria-label="Precio máximo" />
          </fieldset>

          <fieldset>
            <legend>Habitaciones</legend>
            <div class="segmentos">
              <button v-for="n in [0, 1, 2, 3, 4]" :key="n" type="button" :class="{ activo: f.habitaciones === n }" @click="f.habitaciones = n">
                {{ n ? `${n}+` : 'Todas' }}
              </button>
            </div>
          </fieldset>

          <fieldset>
            <legend>Baños</legend>
            <div class="segmentos">
              <button v-for="n in [0, 1, 2, 3]" :key="n" type="button" :class="{ activo: f.banos === n }" @click="f.banos = n">
                {{ n ? `${n}+` : 'Todos' }}
              </button>
            </div>
          </fieldset>

          <label>
            Área mínima (m²)
            <input v-model.number="f.areaMin" type="number" min="0" placeholder="Ej: 60" />
          </label>

          <label>
            Estrato
            <select v-model.number="f.estrato">
              <option value="">Cualquiera</option>
              <option v-for="n in 6" :key="n" :value="n">{{ n }}</option>
            </select>
          </label>

          <label class="check">
            <input v-model="f.parqueadero" type="checkbox" />
            Con parqueadero
          </label>
        </aside>

        <div class="resultados">
          <div class="resultados-cabeza">
            <p>
              <strong>{{ filtradas.length }}</strong>
              {{ filtradas.length === 1 ? 'propiedad' : 'propiedades' }}
            </p>
            <div class="resultados-acciones">
              <button type="button" class="boton secundario solo-movil" @click="verFiltros = !verFiltros">
                {{ verFiltros ? 'Ocultar filtros' : 'Filtros' }}
              </button>
              <select v-model="orden" aria-label="Ordenar">
                <option value="recientes">Más recientes</option>
                <option value="menor">Menor precio</option>
                <option value="mayor">Mayor precio</option>
                <option value="area">Mayor área</option>
              </select>
            </div>
          </div>

          <p v-if="error" class="error">{{ error }}</p>
          <p v-else-if="cargando">Cargando…</p>
          <div v-else-if="!propiedades.length" class="vacio">Todavía no hay propiedades publicadas.</div>
          <div v-else-if="!filtradas.length" class="vacio">
            Ninguna propiedad coincide con los filtros.
            <button type="button" class="enlace" @click="limpiar">Limpiar filtros</button>
          </div>

          <div class="tarjetas">
            <RouterLink v-for="p in filtradas" :key="p.id" class="tarjeta" :to="`/propiedades/${p.id}`">
              <div class="tarjeta-foto">
                <img v-if="p.fotos.length" :src="p.fotos[0].url" :alt="p.titulo" loading="lazy" />
                <div v-else class="sin-foto">Sin foto</div>
                <span class="insignia">{{ p.tipo }}</span>
              </div>
              <div class="tarjeta-cuerpo">
                <span class="tarjeta-lugar">{{ [p.barrio, p.ciudad].filter(Boolean).join(' | ') }}</span>
                <h3>{{ p.titulo }}</h3>
                <p class="tarjeta-precio">{{ cop(p.precio) }}</p>
                <ul class="rasgos">
                  <li v-if="p.habitaciones">{{ p.habitaciones }} hab.</li>
                  <li v-if="p.banos">{{ p.banos }} {{ p.banos === 1 ? 'baño' : 'baños' }}</li>
                  <li v-if="area(p)">{{ area(p) }} m²</li>
                  <li v-if="p.parqueaderos">{{ p.parqueaderos }} parq.</li>
                  <li v-if="p.estrato">Estrato {{ p.estrato }}</li>
                </ul>
              </div>
            </RouterLink>
          </div>
        </div>
      </div>
    </div>
  </section>

  <section class="llamado seccion">
    <div class="contenedor">
      <div>
        <span class="rotulo">Únete</span>
        <h2>El ladrillo no es solo materia; es la memoria cálida de la sabana.</h2>
        <p>
          Crea tu cuenta y encuentra un hogar con carácter bogotano: fachadas en ladrillo, luz del
          altiplano y vista a los cerros.
        </p>
      </div>
      <div class="llamado-caja">
        <h3>Crea tu cuenta gratis</h3>
        <p>Toma menos de un minuto.</p>
        <RouterLink class="boton" to="/registro">Registrarme <span class="flecha" aria-hidden="true">→</span></RouterLink>
      </div>
    </div>
  </section>
</template>
