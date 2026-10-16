# Trend Apartamentos: una sola imagen con el backend (FastAPI) y el frontend compilado.

# ---------- Etapa 1: compilar el frontend (Vue + Vite) ----------
FROM node:22-alpine AS frontend
WORKDIR /src/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---------- Etapa 2: backend + frontend compilado ----------
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY backend/requirements.txt backend/
# tzdata: zona horaria de Bogotá para visitas, reservas y sorteos
RUN pip install --no-cache-dir -r backend/requirements.txt tzdata

COPY backend/app backend/app
COPY --from=frontend /src/frontend/dist frontend/dist
# Foto del edificio que usa la primera noticia al crear la base de datos
COPY frontend/src/assets/edificio-trend.webp frontend/src/assets/

# Usuario sin privilegios; las fotos subidas van al volumen /app/backend/uploads
RUN useradd --create-home trend && mkdir -p backend/uploads && chown -R trend /app/backend/uploads
USER trend

WORKDIR /app/backend
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/tipos', timeout=4)"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
