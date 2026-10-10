<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { api } from '../api'
import AvisoTarjeta from '../components/AvisoTarjeta.vue'

const propiedades = ref([])
const cargando = ref(true)
const error = ref('')
const verFiltros = ref(false) // en móvil el panel de filtros se abre con un botón

const VACIO = {
  negocio: '',
  tipo: '',
  ciudad: '',
  precioMin: '',
  precioMax: '',
  habitaciones: 0,
  banos: 0,
  areaMin: '',
  estrato: '',
  parqueadero: false,
  amoblado: false,
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

const millones = (v) => `$${Math.round(v / 1e6).toLocaleString('es-CO')} M`

// Solo se ofrecen los tipos y ciudades que tienen propiedades publicadas
function conteo(campo) {
  const c = {}
  propiedades.value.forEach((p) => (c[p[campo]] = (c[p[campo]] || 0) + 1))
  return Object.entries(c).sort(([a], [b]) => a.localeCompare(b))
}
const tipos = computed(() => conteo('tipo'))
const ciudades = computed(() => conteo('ciudad').map(([c]) => c))

// Venta y arriendo: las propiedades antiguas sin dato cuentan como venta
const negocioDe = (p) => (p.negocio === 'arriendo' ? 'arriendo' : 'venta')
const conteoNegocio = (n) => propiedades.value.filter((p) => negocioDe(p) === n).length

const filtradas = computed(() => {
  return propiedades.value
    .filter((p) => {
      if (f.negocio && negocioDe(p) !== f.negocio) return false
      if (f.tipo && p.tipo !== f.tipo) return false
      if (f.ciudad && p.ciudad !== f.ciudad) return false
      if (f.precioMin !== '' && p.precio < f.precioMin) return false
      if (f.precioMax !== '' && p.precio > f.precioMax) return false
      if (p.habitaciones < f.habitaciones) return false
      if (p.banos < f.banos) return false
      if (f.areaMin !== '' && area(p) < f.areaMin) return false
      if (f.estrato && p.estrato !== f.estrato) return false
      if (f.parqueadero && !p.parqueaderos) return false
      if (f.amoblado && !(negocioDe(p) === 'arriendo' && p.amoblado)) return false
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
  <section class="seccion">
    <div class="contenedor">
      <div class="seccion-cabeza">
        <div>
          <span class="rotulo">Catálogo</span>
          <h1>Venta y arriendo de apartamentos</h1>
          <dl class="cifras cifras-catalogo">
            <div v-for="[valor, etiqueta] in cifras" :key="etiqueta">
              <dt>{{ etiqueta }}</dt>
              <dd>{{ cargando ? '—' : valor }}</dd>
            </div>
          </dl>
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

      <nav class="chips chips-negocio" aria-label="Venta o arriendo">
        <button type="button" :class="{ activo: !f.negocio }" @click="f.negocio = ''">
          Venta y arriendo <span>{{ propiedades.length }}</span>
        </button>
        <button type="button" :class="{ activo: f.negocio === 'venta' }" @click="f.negocio = 'venta'">
          Venta <span>{{ conteoNegocio('venta') }}</span>
        </button>
        <button type="button" :class="{ activo: f.negocio === 'arriendo' }" @click="f.negocio = 'arriendo'">
          Arriendo <span>{{ conteoNegocio('arriendo') }}</span>
        </button>
      </nav>

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

          <label class="check">
            <input v-model="f.amoblado" type="checkbox" />
            Arriendo amoblado
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
            <AvisoTarjeta v-for="p in filtradas" :key="p.id" :aviso="p" />
          </div>
        </div>
      </div>

    </div>
  </section>
</template>
