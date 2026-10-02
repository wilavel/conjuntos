# Anuncios de propiedades

FastAPI (API JSON) + PostgreSQL + Vue 3 (Vite).

```
anuncios/
├── backend/    # FastAPI, SQLAlchemy, fotos en uploads/
└── frontend/   # Vue 3 + Vue Router + Vite
```

## Desarrollo (dos terminales)

**Backend**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # edita usuario y clave de PostgreSQL
uvicorn app.main:app --reload
```

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

Abre http://localhost:5173. Vite reenvía `/api` y `/uploads` al backend (puerto 8000).
Sin `.env` el backend usa SQLite (`anuncios.db`).

## Producción (un solo proceso)

```bash
cd frontend && npm run build
cd ../backend && uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Si existe `frontend/dist`, FastAPI lo sirve en `/` junto con la API.
Pon Caddy o Nginx delante para el HTTPS.

## Base de datos

Crea la base una sola vez (`CREATE DATABASE anuncios OWNER wilson;`). Las tablas se crean
solas al arrancar el backend:

| Tabla | Contenido |
|---|---|
| `tipos_propiedad` | Catálogo: Apartamento, Casa, Apartaestudio, Local comercial, Oficina, Bodega, Lote, Finca |
| `propiedades` | Precio, administración, área construida, área del lote, habitaciones, baños, parqueaderos, pisos, piso, año de construcción, estrato, ciudad, barrio, dirección, descripción y estado |
| `fotos` | Fotos de cada propiedad |

Para agregar un tipo nuevo, inserta una fila en `tipos_propiedad` (desde DBeaver) o agrégalo a
`TIPOS_INICIALES` en `backend/app/main.py`.

Si ya habías arrancado la versión anterior (tablas `apartamentos` y `fotos`), bórralas antes:

```sql
DROP TABLE IF EXISTS fotos, apartamentos;
```

Si ya tenías la tabla `propiedades` con la columna `antiguedad_anios`:

```sql
ALTER TABLE propiedades DROP COLUMN antiguedad_anios;
ALTER TABLE propiedades ADD COLUMN anio_construccion integer;
```

## API

| Método | Ruta | Descripción |
|---|---|---|
| GET | /api/tipos | Tipos de propiedad |
| GET | /api/propiedades?estado=&tipo_id= | Listado |
| POST | /api/propiedades | Crear |
| GET / PUT / DELETE | /api/propiedades/{id} | Ver, editar, eliminar |
| PATCH | /api/propiedades/{id}/estado | Cambiar estado |
| POST | /api/propiedades/{id}/fotos | Subir fotos (multipart) |
| DELETE | /api/fotos/{id} | Eliminar foto |

Documentación interactiva en http://127.0.0.1:8000/docs
