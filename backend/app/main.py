import hashlib
import re
import secrets
import shutil
import uuid
from datetime import date
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, Response, UploadFile
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageOps
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .db import SessionLocal, engine, get_db
from .models import Base, Foto, Propiedad, TipoPropiedad, Usuario

BASE_DIR = Path(__file__).parent
UPLOADS = BASE_DIR.parent / "uploads"
UPLOADS.mkdir(exist_ok=True)
DIST = BASE_DIR.parent.parent / "frontend" / "dist"

ESTADOS = ["borrador", "publicado", "vendido"]
TIPOS_INICIALES = [
    "Apartamento", "Casa", "Apartaestudio", "Local comercial",
    "Oficina", "Bodega", "Lote", "Finca",
]

CAMPOS = [
    "id", "tipo_id", "titulo", "precio", "administracion",
    "area_construida_m2", "area_lote_m2", "habitaciones", "banos", "parqueaderos",
    "pisos", "piso", "anio_construccion", "estrato",
    "ciudad", "barrio", "direccion", "descripcion", "estado",
]

Base.metadata.create_all(engine)  # más adelante puedes pasar a Alembic

# Carga los tipos iniciales si aún no existen (puedes agregar más desde DBeaver).
with SessionLocal() as s:
    existentes = {n for (n,) in s.execute(select(TipoPropiedad.nombre))}
    for nombre in TIPOS_INICIALES:
        if nombre not in existentes:
            s.add(TipoPropiedad(nombre=nombre))
    s.commit()

app = FastAPI(title="Anuncios de propiedades")


# ---------- esquemas ----------

class PropiedadIn(BaseModel):
    tipo_id: int
    titulo: str = Field(min_length=1, max_length=200)
    precio: int = Field(ge=0)
    administracion: int | None = Field(None, ge=0)
    area_construida_m2: float | None = Field(None, ge=0)
    area_lote_m2: float | None = Field(None, ge=0)
    habitaciones: int = Field(0, ge=0)
    banos: int = Field(0, ge=0)
    parqueaderos: int = Field(0, ge=0)
    pisos: int = Field(1, ge=1)
    piso: int | None = Field(None, ge=0)
    anio_construccion: int | None = Field(None, ge=1800, le=date.today().year + 5)
    estrato: int | None = Field(None, ge=1, le=6)
    ciudad: str = Field(min_length=1, max_length=100)
    barrio: str = ""
    direccion: str = Field(min_length=1, max_length=255)
    descripcion: str = ""

    @model_validator(mode="after")
    def alguna_area(self):
        if not self.area_construida_m2 and not self.area_lote_m2:
            raise ValueError("Indica el área construida o el área del lote")
        return self


class EstadoIn(BaseModel):
    estado: str


class UsuarioIn(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    email: str = Field(max_length=255)
    telefono: str = Field("", max_length=30)
    clave: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def email_valido(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", v):
            raise ValueError("Correo no válido")
        return v


# ---------- utilidades ----------

def obtener(db: Session, prop_id: int) -> Propiedad:
    prop = db.scalars(
        select(Propiedad)
        .options(selectinload(Propiedad.fotos))
        .where(Propiedad.id == prop_id)
    ).first()
    if not prop:
        raise HTTPException(404, "Propiedad no encontrada")
    return prop


def validar_tipo(db: Session, tipo_id: int) -> None:
    if not db.get(TipoPropiedad, tipo_id):
        raise HTTPException(400, "Tipo de propiedad no válido")


def guardar_foto(prop_id: int, archivo: UploadFile) -> str | None:
    """Corrige la rotación, reduce a 1600 px y guarda como JPEG."""
    try:
        img = Image.open(archivo.file)
        img = ImageOps.exif_transpose(img).convert("RGB")
    except Exception:
        return None
    img.thumbnail((1600, 1600))
    carpeta = UPLOADS / str(prop_id)
    carpeta.mkdir(exist_ok=True)
    nombre = f"{uuid.uuid4().hex}.jpg"
    img.save(carpeta / nombre, "JPEG", quality=85)
    return f"{prop_id}/{nombre}"


def hash_clave(clave: str) -> str:
    sal = secrets.token_bytes(16)
    h = hashlib.scrypt(clave.encode(), salt=sal, n=2**14, r=8, p=1)
    return f"scrypt${sal.hex()}${h.hex()}"


def pesos(v: int) -> str:
    return "$" + f"{v:,}".replace(",", ".")


def texto_anuncio(p: Propiedad) -> str:
    """Texto listo para copiar y pegar en cualquier portal."""
    lineas = [p.titulo, "", f"Tipo: {p.tipo.nombre}", f"Precio: {pesos(p.precio)}"]
    if p.administracion:
        lineas.append(f"Administración: {pesos(p.administracion)} al mes")
    if p.area_construida_m2:
        lineas.append(f"Área construida: {p.area_construida_m2:g} m²")
    if p.area_lote_m2:
        lineas.append(f"Área del lote: {p.area_lote_m2:g} m²")
    if p.habitaciones or p.banos or p.parqueaderos:
        lineas.append(
            f"Habitaciones: {p.habitaciones} | Baños: {p.banos} | Parqueaderos: {p.parqueaderos}"
        )
    if p.pisos > 1:
        lineas.append(f"Pisos: {p.pisos}")
    if p.piso is not None:
        lineas.append(f"Piso: {p.piso}")
    if p.anio_construccion is not None:
        edad = date.today().year - p.anio_construccion
        if edad > 0:
            detalle = f" ({edad} años)"
        elif edad == 0:
            detalle = " (nueva)"
        else:
            detalle = " (sobre planos)"
        lineas.append(f"Año de construcción: {p.anio_construccion}{detalle}")
    if p.estrato:
        lineas.append(f"Estrato: {p.estrato}")
    ubicacion = ", ".join(x for x in (p.direccion, p.barrio, p.ciudad) if x)
    lineas.append(f"Ubicación: {ubicacion}")
    if p.descripcion:
        lineas += ["", p.descripcion]
    return "\n".join(lineas)


def salida(p: Propiedad, con_anuncio: bool = False) -> dict:
    datos = {c: getattr(p, c) for c in CAMPOS}
    datos["tipo"] = p.tipo.nombre
    datos["antiguedad_anios"] = (
        max(0, date.today().year - p.anio_construccion) if p.anio_construccion else None
    )
    datos["fotos"] = [{"id": f.id, "url": f"/uploads/{f.archivo}"} for f in p.fotos]
    if con_anuncio:
        datos["anuncio"] = texto_anuncio(p)
    return datos


# ---------- API ----------

@app.get("/api/tipos")
def listar_tipos(db: Session = Depends(get_db)):
    tipos = db.scalars(select(TipoPropiedad).order_by(TipoPropiedad.nombre))
    return [{"id": t.id, "nombre": t.nombre} for t in tipos]


@app.get("/api/propiedades")
def listar(estado: str = "", tipo_id: int | None = None, db: Session = Depends(get_db)):
    consulta = select(Propiedad).options(selectinload(Propiedad.fotos))
    if estado in ESTADOS:
        consulta = consulta.where(Propiedad.estado == estado)
    if tipo_id:
        consulta = consulta.where(Propiedad.tipo_id == tipo_id)
    return [salida(p) for p in db.scalars(consulta.order_by(Propiedad.id.desc()))]


@app.post("/api/propiedades", status_code=201)
def crear(datos: PropiedadIn, db: Session = Depends(get_db)):
    validar_tipo(db, datos.tipo_id)
    prop = Propiedad(**datos.model_dump())
    db.add(prop)
    db.commit()
    return salida(obtener(db, prop.id), con_anuncio=True)


@app.get("/api/propiedades/{prop_id}")
def detalle(prop_id: int, db: Session = Depends(get_db)):
    return salida(obtener(db, prop_id), con_anuncio=True)


@app.put("/api/propiedades/{prop_id}")
def actualizar(prop_id: int, datos: PropiedadIn, db: Session = Depends(get_db)):
    validar_tipo(db, datos.tipo_id)
    prop = obtener(db, prop_id)
    for campo, valor in datos.model_dump().items():
        setattr(prop, campo, valor)
    db.commit()
    return salida(obtener(db, prop_id), con_anuncio=True)


@app.patch("/api/propiedades/{prop_id}/estado")
def cambiar_estado(prop_id: int, datos: EstadoIn, db: Session = Depends(get_db)):
    if datos.estado not in ESTADOS:
        raise HTTPException(400, "Estado no válido")
    prop = obtener(db, prop_id)
    prop.estado = datos.estado
    db.commit()
    return salida(prop, con_anuncio=True)


@app.delete("/api/propiedades/{prop_id}", status_code=204)
def eliminar(prop_id: int, db: Session = Depends(get_db)):
    prop = obtener(db, prop_id)
    db.delete(prop)
    db.commit()
    shutil.rmtree(UPLOADS / str(prop_id), ignore_errors=True)
    return Response(status_code=204)


@app.post("/api/propiedades/{prop_id}/fotos")
def subir_fotos(
    prop_id: int,
    fotos: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    prop = obtener(db, prop_id)
    for archivo in fotos:
        ruta = guardar_foto(prop.id, archivo)
        if ruta:
            db.add(Foto(propiedad_id=prop.id, archivo=ruta))
    db.commit()
    db.refresh(prop, attribute_names=["fotos"])  # recarga la lista de fotos
    return salida(prop, con_anuncio=True)


@app.delete("/api/fotos/{foto_id}", status_code=204)
def borrar_foto(foto_id: int, db: Session = Depends(get_db)):
    foto = db.get(Foto, foto_id)
    if not foto:
        raise HTTPException(404, "Foto no encontrada")
    (UPLOADS / foto.archivo).unlink(missing_ok=True)
    db.delete(foto)
    db.commit()
    return Response(status_code=204)


@app.post("/api/usuarios", status_code=201)
def registrar(datos: UsuarioIn, db: Session = Depends(get_db)):
    if db.scalars(select(Usuario).where(Usuario.email == datos.email)).first():
        raise HTTPException(409, "Ya existe una cuenta con ese correo")
    usuario = Usuario(
        nombre=datos.nombre.strip(),
        email=datos.email,
        telefono=datos.telefono.strip(),
        clave_hash=hash_clave(datos.clave),
    )
    db.add(usuario)
    db.commit()
    return {"id": usuario.id, "nombre": usuario.nombre, "email": usuario.email}


# ---------- archivos estáticos ----------

app.mount("/uploads", StaticFiles(directory=UPLOADS), name="uploads")

# En producción, FastAPI sirve también el frontend compilado (frontend/dist).
if DIST.exists():
    app.mount("/", StaticFiles(directory=DIST, html=True), name="frontend")
