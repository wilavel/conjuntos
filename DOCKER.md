# Trend Apartamentos en Docker

La aplicación corre en dos contenedores: **app** (FastAPI + el frontend compilado) y **db**
(PostgreSQL 18, solo visible para la app). Los datos viven en volúmenes, así que actualizar o
reconstruir la app no borra nada.

| Volumen | Contenido |
|---|---|
| `trend_datos_db` | Base de datos |
| `trend_uploads` | Fotos subidas (avisos, zonas, noticias) |

La app también se conecta a la red compartida **`proxy`**, donde el túnel o proxy de todas las
aplicaciones del PC la encuentra como `http://trend:8000`.

## Primera vez

```bash
docker network create proxy            # una sola vez para todo el PC (si no existe)
cp .env.docker.example .env            # y pon una contraseña larga en DB_PASSWORD
docker compose up -d --build
```

- ⚠️ Cambia `DB_PASSWORD` **antes** del primer `docker compose up`: PostgreSQL fija la contraseña
  solo al crear la base. Si la cambias después, la app falla con *password authentication failed*.
  Para cambiarla más tarde: `docker compose exec db psql -U trend -d conjuntos -c "ALTER USER trend PASSWORD 'nueva';"`,
  pon la misma en `.env` y ejecuta `docker compose up -d`.
- La configuración de la aplicación (correo, super admin, edificio, `SITIO_URL`…) sigue en
  `backend/.env`. El `DATABASE_URL` de ese archivo se ignora: en Docker la base es el contenedor `db`.
- Para entrar desde este PC: http://localhost:8080 (cambia el puerto con `TREND_PUERTO` en `.env`).

Crear la cuenta de super admin (su correo debe estar en `SUPERADMIN_EMAILS` de `backend/.env`):

```bash
docker compose exec app python -m app.crear_usuario
```

## Pasar los datos que ya tienes (PostgreSQL instalado en el PC)

Hazlo **antes** de arrancar la app por primera vez, para que no cree datos iniciales encima.

```bash
# 1. Exportar la base actual (toma la dirección de backend/.env)
URL=$(grep '^DATABASE_URL=' backend/.env | cut -d= -f2- | sed 's/+psycopg//')
pg_dump --no-owner --no-acl "$URL" > respaldo.sql

# 2. Arrancar solo la base de datos del contenedor y cargar el respaldo
docker compose up -d db
docker compose exec -T db psql -U trend -d conjuntos < respaldo.sql

# 3. Copiar las fotos al volumen (docker cp funciona aunque SELinux esté activo, como en Fedora)
docker create --name trend-copia -v trend_uploads:/destino alpine
docker cp backend/uploads/. trend-copia:/destino/
docker rm trend-copia
docker run --rm -v trend_uploads:/destino alpine chown -R 1000:1000 /destino

# 4. Arrancar la aplicación
docker compose up -d --build
```

Cuando confirmes que todo está bien, puedes apagar el PostgreSQL del PC y el `uvicorn` de desarrollo.

## Uso diario

```bash
docker compose up -d --build      # actualizar después de cambiar el código
docker compose ps                 # estado (la app tiene chequeo de salud)
docker compose logs -f app        # ver registros
docker compose restart app        # reiniciar (p. ej. tras cambiar backend/.env)
docker compose down               # detener (los datos se conservan)
```

> ⚠️ **No uses `docker compose down -v`**: la `-v` borra los volúmenes, es decir, la base de datos
> y las fotos.

## Respaldos

```bash
mkdir -p ~/respaldos/trend
docker compose exec -T db pg_dump -U trend conjuntos > ~/respaldos/trend/db-$(date +%F).sql
docker run --rm -v trend_uploads:/datos:ro -v ~/respaldos/trend:/r alpine \
  tar czf /r/uploads-$(date +%F).tar.gz -C /datos .
```

Restaurar la base: `docker compose exec -T db psql -U trend -d conjuntos < db-AAAA-MM-DD.sql`
(sobre una base vacía).

## Publicarla en internet

Con un Cloudflare Tunnel conectado a la red `proxy`, apunta el subdominio
(p. ej. `trend.tudominio.com`) a `http://trend:8000` y pon esa dirección en `SITIO_URL`
de `backend/.env` para que los enlaces de los correos funcionen.
