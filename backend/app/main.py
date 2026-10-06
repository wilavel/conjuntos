import base64
import calendar
import hashlib
import hmac
import os
import random
import re
import secrets
import shutil
import time
import unicodedata
import uuid
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path

from fastapi import Depends, FastAPI, File, Header, HTTPException, Response, UploadFile
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageOps
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import inspect, select, text
from sqlalchemy.orm import Session, selectinload

from .db import SessionLocal, engine, get_db  # carga .env (antes que correo)
from . import correo
from .models import (
    Apartamento, Base, DisponibilidadVisita, Foto, FotoZona, Noticia, Parqueadero,
    PersonaApartamento, Postulacion, Propiedad, Sorteo, TipoPropiedad, Usuario, Visita,
    ZonaComun,
)

BASE_DIR = Path(__file__).parent
UPLOADS = BASE_DIR.parent / "uploads"
UPLOADS.mkdir(exist_ok=True)
DIST = BASE_DIR.parent.parent / "frontend" / "dist"
FOTO_EDIFICIO = BASE_DIR.parent.parent / "frontend" / "src" / "assets" / "edificio-trend.webp"

# Correos de los super admin, separados por coma. Pueden todo, incluido nombrar administradores.
# (ADMIN_EMAILS se acepta por compatibilidad con la configuración anterior.)
SUPERADMIN_EMAILS = {
    e.strip().lower()
    for e in (os.getenv("SUPERADMIN_EMAILS") or os.getenv("ADMIN_EMAILS") or "").split(",")
    if e.strip()
}
# Clave para firmar los tokens de sesión. Sin SECRET_KEY se genera una al arrancar
# y las sesiones se cierran cada vez que se reinicia el backend.
SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_hex(32)
DURACION_SESION = 12 * 3600  # segundos
DURACION_INVITACION = 7 * 24 * 3600  # el enlace para crear la contraseña dura 7 días
# Dirección pública de la página, para los enlaces de los correos
SITIO_URL = (os.getenv("SITIO_URL") or "http://localhost:5174").rstrip("/")

# Datos del edificio: todos los avisos son apartamentos de este mismo edificio en Bogotá.
EDIFICIO = {
    "nombre": "Trend Apartamentos",
    "ciudad": os.getenv("EDIFICIO_CIUDAD", "Bogotá"),
    "barrio": os.getenv("EDIFICIO_BARRIO", ""),
    "direccion": os.getenv("EDIFICIO_DIRECCION", "") or "Edificio Trend Apartamentos",
    "estrato": int(os.getenv("EDIFICIO_ESTRATO") or 0) or None,
    "anio_construccion": int(os.getenv("EDIFICIO_ANIO") or 0) or None,
}

ESTADOS = ["borrador", "publicado", "vendido"]
NEGOCIOS = ["venta", "arriendo"]
ROLES = ["propietario", "arrendatario"]
# Perfiles de usuario: superadmin y admin son de staff; propietario y arrendatario salen de
# los apartamentos (por identificación, solo registros activos); residente = sin verificar.
PERFILES = ["superadmin", "admin", "propietario", "arrendatario", "residente"]

ZONAS_INICIALES = [
    {
        "slug": "gimnasio", "nombre": "Gimnasio", "icono": "gimnasio",
        "resumen": "Equipos de cardio y fuerza para entrenar sin salir del conjunto.",
        "descripcion": (
            "Un espacio dotado con máquinas de cardio, zona de pesas y área funcional para que "
            "entrenes a tu ritmo sin salir de casa.\n\n"
            "Usa ropa y calzado deportivo, lleva tu toalla y deja los equipos limpios y en su "
            "lugar después de usarlos. Los menores de 14 años deben ingresar acompañados."
        ),
        "horario": "Lunes a domingo, 5:00 a. m. a 10:00 p. m.",
    },
    {
        "slug": "terrazas", "nombre": "Terrazas", "icono": "terrazas",
        "resumen": "Terrazas sociales al aire libre con zona BBQ y mobiliario para compartir.",
        "descripcion": (
            "Terrazas con vista a la ciudad, zona de BBQ, mesas y mobiliario exterior para "
            "reuniones con familia y amigos.\n\n"
            "El uso de la zona BBQ se reserva con anticipación desde la zona privada. Al terminar, "
            "deja el área limpia y respeta los horarios de silencio."
        ),
        "horario": "Domingo a jueves hasta las 10:00 p. m.; viernes y sábado hasta las 11:00 p. m.",
    },
    {
        "slug": "coworking", "nombre": "Coworking", "icono": "coworking",
        "resumen": "Puestos de trabajo con wifi y ambiente tranquilo para estudiar o trabajar.",
        "descripcion": (
            "Un espacio de trabajo compartido con puestos cómodos, wifi, tomas eléctricas e "
            "iluminación natural, ideal para trabajar o estudiar sin salir del edificio.\n\n"
            "Mantén un volumen de voz moderado y usa audífonos para llamadas y videollamadas."
        ),
        "horario": "Lunes a sábado, 6:00 a. m. a 10:00 p. m.",
    },
    {
        "slug": "lavanderia", "nombre": "Lavandería", "icono": "lavanderia",
        "resumen": "Lavadoras y secadoras comunales de uso programado.",
        "descripcion": (
            "Lavadoras y secadoras de uso comunal para el cuidado de tu ropa.\n\n"
            "Programa tu turno, retira la ropa al terminar el ciclo y deja los equipos limpios "
            "para el siguiente residente."
        ),
        "horario": "Lunes a domingo, 6:00 a. m. a 9:00 p. m.",
    },
    {
        "slug": "parqueaderos", "nombre": "Parqueaderos", "icono": "parqueaderos",
        "resumen": "Parqueaderos privados para residentes y espacios para visitantes.",
        "descripcion": (
            "Parqueaderos privados para residentes y cupos para visitantes, con control de "
            "acceso vehicular.\n\n"
            "Usa únicamente el cupo asignado, respeta la velocidad máxima dentro del sótano y "
            "registra a tus visitantes en portería."
        ),
        "horario": "24 horas",
    },
]
TIPOS_INICIALES = [
    "Apartamento", "Casa", "Apartaestudio", "Local comercial",
    "Oficina", "Bodega", "Lote", "Finca",
]

CAMPOS = [
    "id", "tipo_id", "apartamento_id", "usuario_id", "titulo", "negocio", "amoblado", "precio", "administracion",
    "area_construida_m2", "area_lote_m2", "habitaciones", "banos", "parqueaderos",
    "pisos", "piso", "anio_construccion", "estrato",
    "ciudad", "barrio", "direccion", "descripcion", "video_youtube", "estado",
]
MAX_FOTOS = 10  # fotos por aviso
ZONA_HORARIA = ZoneInfo("America/Bogota")
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
DIAS_AGENDA = 14  # se pueden agendar visitas en los próximos 14 días
DURACIONES_VISITA = [15, 20, 30, 45, 60, 90]
ESTADOS_VISITA = ["pendiente", "confirmada", "cancelada"]
TIPOS_PARQUEADERO = ["carro", "moto"]
USOS_PARQUEADERO = ["residente", "visitante"]
MAX_MB_FOTO = 15  # tamaño máximo de cada archivo (luego se reduce a 1600 px)

Base.metadata.create_all(engine)  # más adelante puedes pasar a Alembic


COLUMNAS_NUEVAS = [
    ("propiedades", "negocio", "VARCHAR(20) NOT NULL DEFAULT 'venta'"),
    ("usuarios", "identificacion", "VARCHAR(30) NOT NULL DEFAULT ''"),
    ("usuarios", "rol", "VARCHAR(20) NOT NULL DEFAULT ''"),
    ("usuarios", "verificado", "BOOLEAN NOT NULL DEFAULT FALSE"),
    ("propiedades", "apartamento_id", "INTEGER"),
    ("propiedades", "usuario_id", "INTEGER"),
    ("propiedades", "video_youtube", "VARCHAR(20) NOT NULL DEFAULT ''"),
    ("propiedades", "amoblado", "BOOLEAN NOT NULL DEFAULT FALSE"),
    ("fotos", "principal", "BOOLEAN NOT NULL DEFAULT FALSE"),
    ("propiedades", "telefonos", "VARCHAR(255) NOT NULL DEFAULT ''"),
    ("propiedades", "duracion_visita", "INTEGER NOT NULL DEFAULT 30"),
    ("apartamentos_conjunto", "habitaciones", "INTEGER NOT NULL DEFAULT 0"),
    ("apartamentos_conjunto", "banos", "INTEGER NOT NULL DEFAULT 0"),
    ("apartamentos_conjunto", "parqueaderos", "INTEGER NOT NULL DEFAULT 0"),
    ("apartamentos_conjunto", "coeficiente", "FLOAT"),
    ("parqueaderos", "asignado_desde", "DATE"),
    ("parqueaderos", "asignado_hasta", "DATE"),
    ("apartamentos_conjunto", "deudor", "BOOLEAN NOT NULL DEFAULT FALSE"),
    ("postulaciones", "excluido", "BOOLEAN NOT NULL DEFAULT FALSE"),
]


def asegurar_columnas() -> None:
    """Agrega columnas nuevas a tablas ya creadas (sin necesidad de Alembic)."""
    inspector = inspect(engine)
    tablas = set(inspector.get_table_names())
    for tabla, columna, tipo in COLUMNAS_NUEVAS:
        if tabla not in tablas:
            continue
        if columna not in {c["name"] for c in inspector.get_columns(tabla)}:
            with engine.begin() as conn:
                conn.execute(text(f"ALTER TABLE {tabla} ADD COLUMN {columna} {tipo}"))


asegurar_columnas()

# Carga los tipos iniciales si aún no existen (puedes agregar más desde DBeaver).
with SessionLocal() as s:
    existentes = {n for (n,) in s.execute(select(TipoPropiedad.nombre))}
    for nombre in TIPOS_INICIALES:
        if nombre not in existentes:
            s.add(TipoPropiedad(nombre=nombre))
    s.commit()

# Identificaciones guardadas antes de normalizarlas ('1.020.304' -> '1020304').
with SessionLocal() as s:
    for p in s.scalars(select(PersonaApartamento)):
        limpia = re.sub(r"[^0-9A-Za-z]", "", p.identificacion).upper()
        if limpia != p.identificacion:
            p.identificacion = limpia
    s.commit()

# Carga las zonas comunes iniciales si aún no hay ninguna (se editan desde la administración).
with SessionLocal() as s:
    if not s.scalars(select(ZonaComun.id).limit(1)).first():
        for orden, zona in enumerate(ZONAS_INICIALES):
            s.add(ZonaComun(orden=orden, **zona))
        s.commit()

app = FastAPI(title="Anuncios de propiedades")


# ---------- esquemas ----------

class FranjaIn(BaseModel):
    """Disponibilidad semanal: ej. lunes (0) de 09:00 a 12:00."""

    dia: int = Field(ge=0, le=6)
    inicio: str
    fin: str

    @field_validator("inicio", "fin")
    @classmethod
    def hora_valida(cls, v: str) -> str:
        if not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", v or ""):
            raise ValueError("La hora debe tener el formato HH:MM")
        return v


def minutos(hora: str) -> int:
    h, m = hora.split(":")
    return int(h) * 60 + int(m)


def telefono_valido(v: str) -> str:
    v = re.sub(r"\s+", " ", (v or "").strip())
    if not re.fullmatch(r"\+?[\d ()-]+", v) or len(re.sub(r"\D", "", v)) < 7:
        raise ValueError(f"El teléfono «{v}» no es válido")
    return v


def id_youtube(texto: str) -> str | None:
    """Saca el id del video de enlaces como youtube.com/watch?v=ID, youtu.be/ID o /shorts/ID."""
    if re.fullmatch(r"[\w-]{11}", texto):
        return texto
    m = re.match(
        r"(?:https?://)?(?:www\.|m\.)?(?:youtube\.com/(?:watch\?(?:.*&)?v=|shorts/|embed/|live/)|youtu\.be/)([\w-]{11})",
        texto,
    )
    return m.group(1) if m else None


class PropiedadIn(BaseModel):
    """Datos del aviso. Las características (área, piso, habitaciones, baños, parqueaderos)
    son del apartamento; la ubicación, del edificio (EDIFICIO)."""

    apartamento_id: int
    tipo_id: int | None = None  # vacío = Apartamento
    titulo: str = Field(min_length=1, max_length=200)
    negocio: str = "venta"  # venta | arriendo
    amoblado: bool = False  # se arrienda amoblado
    precio: int = Field(ge=0)
    administracion: int | None = Field(None, ge=0)
    anio_construccion: int | None = Field(None, ge=1800, le=date.today().year + 5)
    estrato: int | None = Field(None, ge=1, le=6)
    ciudad: str = Field("", max_length=100)
    barrio: str = Field("", max_length=100)
    direccion: str = Field("", max_length=255)
    descripcion: str = ""
    video_youtube: str = ""  # enlace de YouTube (se guarda solo el id del video)
    telefonos: list[str] = Field(default_factory=list, max_length=5)  # a dónde llamar (mínimo uno)
    duracion_visita: int = 30
    disponibilidad: list[FranjaIn] = Field(default_factory=list, max_length=21)

    @field_validator("telefonos")
    @classmethod
    def telefonos_validos(cls, v: list[str]) -> list[str]:
        v = [telefono_valido(t) for t in v if t and t.strip()]
        if not v:
            raise ValueError("Agrega al menos un teléfono de contacto")
        return v

    @field_validator("duracion_visita")
    @classmethod
    def duracion_valida(cls, v: int) -> int:
        if v not in DURACIONES_VISITA:
            raise ValueError("Duración de visita no válida")
        return v

    @field_validator("disponibilidad")
    @classmethod
    def franjas_validas(cls, v: list[FranjaIn]) -> list[FranjaIn]:
        for f in v:
            if minutos(f.fin) <= minutos(f.inicio):
                raise ValueError(f"El {DIAS[f.dia]}: la hora final debe ser mayor que la inicial")
        return v

    @field_validator("video_youtube")
    @classmethod
    def video_valido(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            return ""
        video = id_youtube(v)
        if not video:
            raise ValueError("El enlace del video debe ser de YouTube (youtube.com o youtu.be)")
        return video

    @field_validator("negocio")
    @classmethod
    def negocio_valido(cls, v: str) -> str:
        v = (v or "venta").strip().lower()
        if v not in NEGOCIOS:
            raise ValueError("El negocio debe ser 'venta' o 'arriendo'")
        return v


class NoticiaIn(BaseModel):
    titulo: str = Field(min_length=1, max_length=200)
    resumen: str = Field("", max_length=300)
    contenido: str = ""
    publicada: bool = False


def normalizar_identificacion(v: str) -> str:
    """'1.020.304-050 ' -> '1020304050': así coinciden la cuenta y el registro del apartamento."""
    return re.sub(r"[^0-9A-Za-z]", "", v or "").upper()


class PersonaIn(BaseModel):
    nombre: str = Field(min_length=1, max_length=150)
    identificacion: str = Field(min_length=1, max_length=30)
    telefono: str = Field("", max_length=30)
    email: str = Field(max_length=255)  # con él se crea su cuenta y se le envía el acceso
    activo: bool = True

    @field_validator("nombre", "telefono")
    @classmethod
    def sin_espacios(cls, v: str) -> str:
        return v.strip()

    @field_validator("email")
    @classmethod
    def email_valido(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", v):
            raise ValueError("Correo no válido")
        return v

    @field_validator("identificacion")
    @classmethod
    def identificacion_valida(cls, v: str) -> str:
        v = normalizar_identificacion(v)
        if not v:
            raise ValueError("La identificación no es válida")
        return v


class PersonaNuevaIn(PersonaIn):
    rol: str

    @field_validator("rol")
    @classmethod
    def rol_valido(cls, v: str) -> str:
        if v not in ROLES:
            raise ValueError("El rol debe ser 'propietario' o 'arrendatario'")
        return v


class ApartamentoIn(BaseModel):
    torre: str = Field("", max_length=20)  # una sola torre: el formulario no lo envía
    numero: str = Field(min_length=1, max_length=20)
    piso: int | None = Field(None, ge=0)
    area_m2: float | None = Field(None, gt=0)
    habitaciones: int = Field(0, ge=0)
    banos: int = Field(0, ge=0)
    # (los parqueaderos se calculan con los que tenga asignados)
    coeficiente: float | None = Field(None, gt=0, le=100)  # porcentaje de copropiedad
    deudor: bool = False  # en mora: no participa en sorteos

    @field_validator("torre", "numero")
    @classmethod
    def sin_espacios(cls, v: str) -> str:
        return v.strip()


class ApartamentoNuevoIn(ApartamentoIn):
    propietarios: list[PersonaIn] = Field(min_length=1)  # todo apartamento nace con propietario


class ActivacionIn(BaseModel):
    token: str
    clave: str = Field(min_length=8, max_length=128)


class ClaveIn(BaseModel):
    clave: str = Field(min_length=8, max_length=128)


class CambioClaveIn(BaseModel):
    actual: str
    nueva: str = Field(min_length=8, max_length=128)


class VerificacionIn(BaseModel):
    verificado: bool


class PerfilIn(BaseModel):
    telefono: str = Field("", max_length=30)
    identificacion: str = Field(min_length=1, max_length=30)

    @field_validator("identificacion")
    @classmethod
    def identificacion_valida(cls, v: str) -> str:
        v = normalizar_identificacion(v)
        if not v:
            raise ValueError("La identificación no es válida")
        return v


class RolIn(BaseModel):
    rol: str  # "admin" o "" (quitar)

    @field_validator("rol")
    @classmethod
    def rol_valido(cls, v: str) -> str:
        if v not in ("admin", ""):
            raise ValueError("El rol debe ser 'admin' o vacío")
        return v


class ZonaIn(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    icono: str = Field("", max_length=30)
    resumen: str = Field("", max_length=300)
    descripcion: str = ""
    horario: str = Field("", max_length=200)
    orden: int = 0


class VisitaIn(BaseModel):
    fecha: date
    hora: str
    nombre: str = Field(min_length=2, max_length=100)
    telefono: str = Field(max_length=30)
    email: str = Field("", max_length=255)
    mensaje: str = Field("", max_length=1000)

    @field_validator("telefono")
    @classmethod
    def tel(cls, v: str) -> str:
        return telefono_valido(v)

    @field_validator("email")
    @classmethod
    def email_opcional(cls, v: str) -> str:
        v = (v or "").strip().lower()
        if v and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", v):
            raise ValueError("Correo no válido")
        return v


class ParqueaderoIn(BaseModel):
    numero: str = Field(min_length=1, max_length=20)
    tipo: str = "carro"
    uso: str = "residente"
    ubicacion: str = Field("", max_length=60)
    observaciones: str = Field("", max_length=255)
    apartamento_id: int | None = None
    asignado_hasta: date | None = None  # vacío = sin vencimiento

    @field_validator("numero", "ubicacion", "observaciones")
    @classmethod
    def sin_espacios(cls, v: str) -> str:
        return v.strip()

    @field_validator("tipo")
    @classmethod
    def tipo_valido(cls, v: str) -> str:
        if v not in TIPOS_PARQUEADERO:
            raise ValueError("El tipo debe ser carro o moto")
        return v

    @field_validator("uso")
    @classmethod
    def uso_valido(cls, v: str) -> str:
        if v not in USOS_PARQUEADERO:
            raise ValueError("El uso debe ser residente o visitante")
        return v


class LoteParqueaderosIn(BaseModel):
    """Crea varios de una vez: prefijo "P-" del 1 al 40 -> P-1 ... P-40."""

    prefijo: str = Field("", max_length=10)
    desde: int = Field(ge=0)
    hasta: int = Field(ge=0)
    tipo: str = "carro"
    uso: str = "residente"
    ubicacion: str = Field("", max_length=60)

    @field_validator("tipo")
    @classmethod
    def tipo_valido(cls, v: str) -> str:
        if v not in TIPOS_PARQUEADERO:
            raise ValueError("El tipo debe ser carro o moto")
        return v

    @field_validator("uso")
    @classmethod
    def uso_valido(cls, v: str) -> str:
        if v not in USOS_PARQUEADERO:
            raise ValueError("El uso debe ser residente o visitante")
        return v


class SorteoIn(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    tipo: str = "carro"
    meses: int = Field(ge=1, le=60)
    inicio: date
    cierre: date
    parqueadero_ids: list[int] | None = None  # vacío = todos los de residentes de ese tipo

    @field_validator("tipo")
    @classmethod
    def tipo_valido(cls, v: str) -> str:
        if v not in TIPOS_PARQUEADERO:
            raise ValueError("El tipo debe ser carro o moto")
        return v


class PostulacionIn(BaseModel):
    apartamento_id: int


class EstadoVisitaIn(BaseModel):
    estado: str

    @field_validator("estado")
    @classmethod
    def estado_valido(cls, v: str) -> str:
        if v not in ESTADOS_VISITA:
            raise ValueError("Estado de visita no válido")
        return v


class EstadoIn(BaseModel):
    estado: str


class SesionIn(BaseModel):
    email: str
    clave: str


class UsuarioIn(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    email: str = Field(max_length=255)
    telefono: str = Field("", max_length=30)
    identificacion: str = Field(min_length=1, max_length=30)
    clave: str = Field(min_length=8, max_length=128)

    @field_validator("identificacion")
    @classmethod
    def identificacion_valida(cls, v: str) -> str:
        v = normalizar_identificacion(v)
        if not v:
            raise ValueError("La identificación no es válida")
        return v

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
        .options(selectinload(Propiedad.fotos), selectinload(Propiedad.disponibilidad))
        .where(Propiedad.id == prop_id)
    ).first()
    if not prop:
        raise HTTPException(404, "Propiedad no encontrada")
    return prop


def validar_tipo(db: Session, tipo_id: int) -> None:
    if not db.get(TipoPropiedad, tipo_id):
        raise HTTPException(400, "Tipo de propiedad no válido")


def apartamentos_propios(usuario: Usuario | None, db: Session) -> set[int]:
    """Apartamentos donde la cuenta (verificada) figura como propietario activo."""
    if not usuario:
        return set()
    return {a["id"] for a in perfil(usuario, db)["apartamentos"] if a["rol"] == "propietario"}


def puede_editar(prop: Propiedad, usuario: Usuario | None, db: Session) -> bool:
    if not usuario:
        return False
    return es_admin(usuario) or prop.apartamento_id in apartamentos_propios(usuario, db)


def requiere_editor(prop: Propiedad, usuario: Usuario | None, db: Session) -> None:
    if not usuario:
        raise HTTPException(401, "Inicia sesión para continuar")
    if not puede_editar(prop, usuario, db):
        raise HTTPException(403, "Solo puedes administrar los avisos de tus apartamentos")


CARACTERISTICAS = {  # campo del aviso: campo del apartamento
    "area_construida_m2": "area_m2",
    "piso": "piso",
    "habitaciones": "habitaciones",
    "banos": "banos",
    "parqueaderos": "parqueaderos",
}


def guardar_disponibilidad(prop: Propiedad, datos: PropiedadIn) -> None:
    prop.disponibilidad = [
        DisponibilidadVisita(dia=f.dia, inicio=f.inicio, fin=f.fin) for f in datos.disponibilidad
    ]


def copiar_caracteristicas(prop: Propiedad, apto: Apartamento) -> None:
    """El aviso muestra las características del apartamento (no se editan en el aviso)."""
    for campo, del_apto in CARACTERISTICAS.items():
        setattr(prop, campo, getattr(apto, del_apto))
    prop.area_lote_m2 = None
    prop.pisos = 1


def completar_aviso(datos: PropiedadIn, usuario: Usuario, db: Session) -> tuple[dict, Apartamento]:
    """Valida permisos y completa el aviso con los datos del edificio."""
    valores = datos.model_dump(exclude={"disponibilidad"})
    valores["telefonos"] = ", ".join(datos.telefonos)
    # El propietario solo publica sus propios apartamentos
    if not es_admin(usuario) and datos.apartamento_id not in apartamentos_propios(usuario, db):
        raise HTTPException(403, "Elige uno de tus apartamentos")
    if valores["negocio"] != "arriendo":
        valores["amoblado"] = False  # en venta no aplica
    # Todos son apartamentos del edificio: ubicación, estrato y año salen de EDIFICIO
    valores.update(tipo_id=None, ciudad="", barrio="", direccion="", estrato=None, anio_construccion=None)
    apto = db.get(Apartamento, datos.apartamento_id)
    if not apto:
        raise HTTPException(400, "Apartamento no válido")

    if not valores["tipo_id"]:
        apartamento = db.scalars(
            select(TipoPropiedad).where(TipoPropiedad.nombre == "Apartamento")
        ).first()
        valores["tipo_id"] = apartamento.id
    validar_tipo(db, valores["tipo_id"])
    for campo in ("ciudad", "barrio", "direccion"):
        valores[campo] = valores[campo].strip() or EDIFICIO[campo]
    for campo in ("estrato", "anio_construccion"):
        if valores[campo] is None:
            valores[campo] = EDIFICIO[campo]
    return valores, apto


def guardar_foto(subcarpeta: str, archivo) -> str | None:
    """Corrige la rotación, reduce a 1600 px y guarda como JPEG en uploads/<subcarpeta>/."""
    try:
        img = Image.open(archivo)
        img = ImageOps.exif_transpose(img).convert("RGB")
    except Exception:
        return None
    img.thumbnail((1600, 1600))
    carpeta = UPLOADS / subcarpeta
    carpeta.mkdir(parents=True, exist_ok=True)
    nombre = f"{uuid.uuid4().hex}.jpg"
    img.save(carpeta / nombre, "JPEG", quality=85)
    return f"{subcarpeta}/{nombre}"


def hash_clave(clave: str) -> str:
    sal = secrets.token_bytes(16)
    h = hashlib.scrypt(clave.encode(), salt=sal, n=2**14, r=8, p=1)
    return f"scrypt${sal.hex()}${h.hex()}"


def verificar_clave(clave: str, guardado: str) -> bool:
    """Compara la contraseña con el hash scrypt almacenado."""
    try:
        _, sal, esperado = guardado.split("$")
        calculado = hashlib.scrypt(
            clave.encode(), salt=bytes.fromhex(sal), n=2**14, r=8, p=1
        )
        return secrets.compare_digest(calculado.hex(), esperado)
    except (ValueError, AttributeError):
        return False


def rol_staff(usuario: Usuario) -> str:
    if usuario.email in SUPERADMIN_EMAILS:
        return "superadmin"
    return "admin" if usuario.rol == "admin" else ""


def es_admin(usuario: Usuario) -> bool:
    return rol_staff(usuario) in ("superadmin", "admin")


def perfil(usuario: Usuario, db: Session, para_admin: bool = False) -> dict:
    """Perfil efectivo y apartamentos donde la persona figura activa (por identificación).

    Propietario o arrendatario solo si la administración verificó la cuenta; antes de eso
    es "residente". Con para_admin se incluyen las coincidencias para poder verificarla.
    """
    registros = []
    if usuario.identificacion:
        registros = db.scalars(
            select(PersonaApartamento)
            .options(selectinload(PersonaApartamento.apartamento))
            .where(
                PersonaApartamento.identificacion == usuario.identificacion,
                PersonaApartamento.activo.is_(True),
            )
        ).all()
    vinculados = registros if usuario.verificado else []
    roles = {r.rol for r in vinculados}
    rol = rol_staff(usuario) or (
        "propietario" if "propietario" in roles
        else "arrendatario" if "arrendatario" in roles
        else "residente"
    )
    def aptos(lista):
        return [
            {
                "id": r.apartamento.id,
                "torre": r.apartamento.torre,
                "numero": r.apartamento.numero,
                "piso": r.apartamento.piso,
                "area_m2": r.apartamento.area_m2,
                "habitaciones": r.apartamento.habitaciones,
                "banos": r.apartamento.banos,
                "parqueaderos": r.apartamento.parqueaderos,
                "rol": r.rol,
            }
            for r in lista
        ]

    datos = {
        "id": usuario.id,
        "nombre": usuario.nombre,
        "email": usuario.email,
        "telefono": usuario.telefono,
        "identificacion": usuario.identificacion,
        "rol": rol,
        "rol_staff": rol_staff(usuario),
        "es_admin": rol in ("superadmin", "admin"),
        "verificado": usuario.verificado,
        "apartamentos": aptos(vinculados),
    }
    if para_admin:
        datos["coincidencias"] = aptos(registros)
        datos["creado"] = usuario.creado
    return datos


def firmar(datos: str) -> str:
    return hmac.new(SECRET_KEY.encode(), datos.encode(), hashlib.sha256).hexdigest()


def crear_token(usuario: Usuario) -> str:
    """Token firmado con HMAC: base64(id:expira).firma"""
    datos = f"{usuario.id}:{int(time.time()) + DURACION_SESION}"
    return base64.urlsafe_b64encode(datos.encode()).decode() + "." + firmar(datos)


def token_invitacion(usuario: Usuario) -> str:
    """Enlace de un solo uso para crear la contraseña: deja de servir al cambiarla."""
    datos = f"{usuario.id}:{int(time.time()) + DURACION_INVITACION}:{usuario.clave_hash[-12:]}"
    return base64.urlsafe_b64encode(datos.encode()).decode() + "." + firmar("invitacion|" + datos)


def usuario_de_invitacion(token: str, db: Session) -> Usuario | None:
    try:
        cuerpo, firma = token.split(".")
        datos = base64.urlsafe_b64decode(cuerpo.encode()).decode()
        usuario_id, expira, huella = datos.split(":")
        usuario_id, expira = int(usuario_id), int(expira)
    except ValueError:
        return None
    if not hmac.compare_digest(firma, firmar("invitacion|" + datos)) or expira < time.time():
        return None
    usuario = db.get(Usuario, usuario_id)
    if not usuario or usuario.clave_hash[-12:] != huella:
        return None  # ya se usó (la contraseña cambió)
    return usuario


def enviar_invitacion(usuario: Usuario, nueva: bool) -> dict:
    """Envía el correo con el enlace para crear la contraseña.

    Si no hay SMTP configurado devuelve el enlace para que la administración lo comparta."""
    enlace = f"{SITIO_URL}/#/activar/{token_invitacion(usuario)}"
    asunto = "Tu acceso a Trend Apartamentos" if nueva else "Enlace para crear tu contraseña · Trend Apartamentos"
    texto = (
        f"Hola, {usuario.nombre}:\n\n"
        "La administración de Trend Apartamentos creó tu cuenta en la página del conjunto, donde "
        "encontrarás la zona privada de propietarios y residentes.\n\n"
        f"Tu usuario es este correo: {usuario.email}\n"
        f"Crea tu contraseña aquí (el enlace vence en 7 días):\n{enlace}\n\n"
        "Si no esperabas este mensaje, puedes ignorarlo.\n\n"
        "Administración · Alianza Grupo Inmobiliario S.A.S."
    )
    html = f"""<div style="font-family:Arial,sans-serif;color:#16233c;max-width:520px">
<h2 style="font-family:Georgia,serif;font-weight:400">Hola, {usuario.nombre}</h2>
<p>La administración de <strong>Trend Apartamentos</strong> creó tu cuenta en la página del conjunto,
donde encontrarás la zona privada de propietarios y residentes.</p>
<p>Tu usuario es este correo: <strong>{usuario.email}</strong></p>
<p><a href="{enlace}" style="display:inline-block;background:#ffc629;color:#14335f;padding:12px 20px;
text-decoration:none;font-weight:bold;letter-spacing:.08em">CREAR MI CONTRASEÑA</a></p>
<p style="color:#6b7486;font-size:13px">El enlace vence en 7 días. Si no esperabas este mensaje, puedes ignorarlo.</p>
<p style="color:#6b7486;font-size:13px">Administración · Alianza Grupo Inmobiliario S.A.S.</p></div>"""
    enviado = correo.enviar(usuario.email, asunto, texto, html)
    resultado = {"email": usuario.email, "nombre": usuario.nombre, "nueva": nueva, "enviado": enviado}
    if not enviado:
        resultado["enlace"] = enlace  # para compartirlo a mano
    return resultado


def cuenta_para_persona(persona: PersonaApartamento, db: Session) -> tuple[Usuario, bool]:
    """Busca la cuenta del correo de la persona o la crea (verificada y sin contraseña aún)."""
    usuario = db.scalars(select(Usuario).where(Usuario.email == persona.email)).first()
    if usuario:
        if not usuario.identificacion:
            usuario.identificacion = persona.identificacion
        return usuario, False
    usuario = Usuario(
        nombre=persona.nombre,
        email=persona.email,
        telefono=persona.telefono,
        identificacion=persona.identificacion,
        clave_hash=hash_clave(secrets.token_urlsafe(32)),  # nadie la conoce: se crea con el enlace
        verificado=True,
    )
    db.add(usuario)
    db.flush()
    return usuario, True


def invitar_personas(personas: list[PersonaApartamento], db: Session) -> list[dict]:
    """Crea las cuentas que falten y envía el acceso solo a las nuevas."""
    cuentas = [cuenta_para_persona(p, db) for p in personas if p.email]
    db.commit()
    return [enviar_invitacion(u, nueva) for u, nueva in cuentas if nueva]


def usuario_del_token(token: str, db: Session) -> Usuario | None:
    try:
        cuerpo, firma = token.split(".")
        datos = base64.urlsafe_b64decode(cuerpo.encode()).decode()
        usuario_id, expira = (int(x) for x in datos.split(":"))
    except ValueError:
        return None
    if not hmac.compare_digest(firma, firmar(datos)) or expira < time.time():
        return None
    return db.get(Usuario, usuario_id)


def usuario_actual(
    authorization: str = Header(""), db: Session = Depends(get_db)
) -> Usuario | None:
    """Usuario de la cabecera 'Authorization: Bearer <token>', o None si no hay sesión válida."""
    if not authorization.startswith("Bearer "):
        return None
    return usuario_del_token(authorization.removeprefix("Bearer "), db)


def requiere_admin(usuario: Usuario | None = Depends(usuario_actual)) -> Usuario:
    if not usuario:
        raise HTTPException(401, "Inicia sesión para continuar")
    if not es_admin(usuario):
        raise HTTPException(403, "Solo la administración puede hacer esto")
    return usuario


def requiere_superadmin(usuario: Usuario | None = Depends(usuario_actual)) -> Usuario:
    if not usuario:
        raise HTTPException(401, "Inicia sesión para continuar")
    if rol_staff(usuario) != "superadmin":
        raise HTTPException(403, "Solo el super admin puede hacer esto")
    return usuario


def requiere_sesion(usuario: Usuario | None = Depends(usuario_actual)) -> Usuario:
    if not usuario:
        raise HTTPException(401, "Inicia sesión para continuar")
    return usuario


def pesos(v: int) -> str:
    return "$" + f"{v:,}".replace(",", ".")


def texto_anuncio(p: Propiedad) -> str:
    """Texto listo para copiar y pegar en cualquier portal."""
    lineas = [
        p.titulo,
        "",
        f"Tipo: {p.tipo.nombre}",
        f"Negocio: {'Arriendo' if p.negocio == 'arriendo' else 'Venta'}"
        + (" (amoblado)" if p.negocio == "arriendo" and p.amoblado else ""),
        f"Precio: {pesos(p.precio)}",
    ]
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
    if p.telefonos:
        lineas.append(f"Teléfonos: {p.telefonos}")
    if p.video_youtube:
        lineas.append(f"Video: https://youtu.be/{p.video_youtube}")
    if p.descripcion:
        lineas += ["", p.descripcion]
    return "\n".join(lineas)


def salida(p: Propiedad, con_anuncio: bool = False, privado: bool = False) -> dict:
    """privado=True incluye el apartamento y quién creó el aviso (no se muestra al público)."""
    datos = {c: getattr(p, c) for c in CAMPOS}
    datos["tipo"] = p.tipo.nombre
    datos["apartamento"] = (
        {"id": p.apartamento.id, "torre": p.apartamento.torre, "numero": p.apartamento.numero}
        if p.apartamento else None
    )
    datos["telefonos"] = [t.strip() for t in (p.telefonos or "").split(",") if t.strip()]
    datos["duracion_visita"] = p.duracion_visita
    datos["disponibilidad"] = [{"dia": d.dia, "inicio": d.inicio, "fin": d.fin} for d in p.disponibilidad]
    if not privado:
        datos.update(apartamento_id=None, usuario_id=None, apartamento=None)
    datos["antiguedad_anios"] = (
        max(0, date.today().year - p.anio_construccion) if p.anio_construccion else None
    )
    # La foto principal va primero (es la portada); si no hay marcada, la más antigua
    fotos = sorted(p.fotos, key=lambda f: (not f.principal, f.id))
    datos["fotos"] = [
        {"id": f.id, "url": f"/uploads/{f.archivo}", "principal": i == 0} for i, f in enumerate(fotos)
    ]
    if con_anuncio:
        datos["anuncio"] = texto_anuncio(p)
    return datos


def obtener_noticia(db: Session, noticia_id: int) -> Noticia:
    noticia = db.get(Noticia, noticia_id)
    if not noticia:
        raise HTTPException(404, "Noticia no encontrada")
    return noticia


def salida_noticia(n: Noticia) -> dict:
    return {
        "id": n.id,
        "titulo": n.titulo,
        "resumen": n.resumen,
        "contenido": n.contenido,
        "imagen": f"/uploads/{n.imagen}" if n.imagen else None,
        "publicada": n.publicada,
        "creado": n.creado,
    }


NOTICIA_CENSO = {
    "titulo": "Censo y actualización de información",
    "resumen": (
        "Estimados propietarios: les pedimos diligenciar el formulario del censo para mantener "
        "actualizada la información de la copropiedad."
    ),
    "contenido": (
        "Estimados propietarios: esperamos que estén teniendo un hermoso día.\n\n"
        "Les solicitamos muy amablemente su colaboración con el diligenciamiento del formulario. "
        "Su participación es muy importante para mantener nuestra información actualizada y "
        "continuar fortaleciendo la gestión de la copropiedad.\n\n"
        "Importante: el formulario estará habilitado únicamente hasta el miércoles 30 de "
        "septiembre de 2026 a las 5:00 p. m.\n\n"
        "Para diligenciarlo, crea tu cuenta desde el botón «Registrarse» de esta página.\n\n"
        "Agradecemos mucho su tiempo y colaboración.\n\n"
        "Administración\nAlianza Grupo Inmobiliario S.A.S."
    ),
    "publicada": True,
}


def cargar_noticia_inicial() -> None:
    """Si el blog está vacío, crea el comunicado del censo con la foto del edificio."""
    with SessionLocal() as s:
        if s.scalars(select(Noticia.id).limit(1)).first():
            return
        noticia = Noticia(**NOTICIA_CENSO)
        s.add(noticia)
        s.commit()
        if FOTO_EDIFICIO.exists():
            with FOTO_EDIFICIO.open("rb") as foto:
                noticia.imagen = guardar_foto(f"noticias/{noticia.id}", foto)
            s.commit()


cargar_noticia_inicial()


def obtener_apartamento(db: Session, apto_id: int) -> Apartamento:
    apto = db.scalars(
        select(Apartamento)
        .options(selectinload(Apartamento.personas))
        .where(Apartamento.id == apto_id)
    ).first()
    if not apto:
        raise HTTPException(404, "Apartamento no encontrado")
    return apto


def orden_texto(texto: str) -> tuple:
    """Orden natural: 201, 502, 1001 / P-2, P-10 (no 1001, 201 como texto)."""
    partes = re.findall(r"\d+|\D+", texto)
    return tuple((0, int(p), "") if p.isdigit() else (1, 0, p.lower()) for p in partes)


def orden_numero(apto: Apartamento) -> tuple:
    return orden_texto(apto.numero)


def salida_parqueadero(p: Parqueadero, con_apto: bool = True) -> dict:
    datos = {
        "id": p.id,
        "numero": p.numero,
        "tipo": p.tipo,
        "uso": p.uso,
        "ubicacion": p.ubicacion,
        "observaciones": p.observaciones,
        "apartamento_id": p.apartamento_id,
        "asignado_desde": p.asignado_desde.isoformat() if p.asignado_desde else None,
        "asignado_hasta": p.asignado_hasta.isoformat() if p.asignado_hasta else None,
    }
    if con_apto:
        datos["apartamento"] = (
            {"id": p.apartamento.id, "torre": p.apartamento.torre, "numero": p.apartamento.numero}
            if p.apartamento else None
        )
    return datos


def sumar_meses(fecha: date, meses: int) -> date:
    """15 ene + 6 meses = 15 jul (si el día no existe, el último del mes)."""
    m = fecha.month - 1 + meses
    anio, mes = fecha.year + m // 12, m % 12 + 1
    return date(anio, mes, min(fecha.day, calendar.monthrange(anio, mes)[1]))


def liberar_vencidos(db: Session) -> None:
    """Las asignaciones cuyo periodo terminó dejan el parqueadero libre."""
    hoy = ahora_bogota().date()
    vencidos = db.scalars(
        select(Parqueadero).where(
            Parqueadero.apartamento_id.is_not(None), Parqueadero.asignado_hasta < hoy
        )
    ).all()
    if not vencidos:
        return
    aptos = {p.apartamento_id for p in vencidos}
    for p in vencidos:
        p.apartamento_id, p.asignado_desde, p.asignado_hasta = None, None, None
    for apto_id in aptos:
        recalcular_parqueaderos(apto_id, db)
    db.commit()


def recalcular_parqueaderos(apto_id: int | None, db: Session) -> None:
    """El apartamento (y sus avisos) muestran cuántos parqueaderos de carro tiene asignados."""
    if not apto_id:
        return
    apto = db.get(Apartamento, apto_id)
    if not apto:
        return
    db.flush()
    apto.parqueaderos = len(db.scalars(
        select(Parqueadero.id).where(Parqueadero.apartamento_id == apto_id, Parqueadero.tipo == "carro")
    ).all())
    for prop in db.scalars(select(Propiedad).where(Propiedad.apartamento_id == apto_id)):
        prop.parqueaderos = apto.parqueaderos


def validar_numero_libre(db: Session, datos: ApartamentoIn, excepto: int | None = None) -> None:
    consulta = select(Apartamento.id).where(
        Apartamento.torre == datos.torre, Apartamento.numero == datos.numero
    )
    if excepto:
        consulta = consulta.where(Apartamento.id != excepto)
    if db.scalars(consulta).first():
        raise HTTPException(409, "Ya existe un apartamento con ese número")


def validar_identificacion(apto: Apartamento, rol: str, identificacion: str, excepto: int | None = None) -> None:
    """Una misma persona no puede figurar dos veces activa con el mismo rol en un apartamento."""
    for p in apto.personas:
        if p.id != excepto and p.activo and p.rol == rol and p.identificacion == identificacion:
            raise HTTPException(409, f"Ya hay un {rol} activo con esa identificación")


def validar_propietario_activo(apto: Apartamento) -> None:
    if not any(p.activo and p.rol == "propietario" for p in apto.personas):
        raise HTTPException(
            400, "El apartamento debe tener al menos un propietario activo. Agrega el nuevo primero."
        )


def salida_persona(p: PersonaApartamento) -> dict:
    return {
        "id": p.id,
        "rol": p.rol,
        "nombre": p.nombre,
        "identificacion": p.identificacion,
        "telefono": p.telefono,
        "email": p.email,
        "activo": p.activo,
        "creado": p.creado,
    }


def salida_apartamento(a: Apartamento, db: Session | None = None) -> dict:
    personas = [salida_persona(p) for p in a.personas]
    parqueaderos = (
        sorted(
            db.scalars(select(Parqueadero).where(Parqueadero.apartamento_id == a.id)),
            key=lambda p: orden_texto(p.numero),
        )
        if db
        else []
    )
    return {
        "id": a.id,
        "torre": a.torre,
        "numero": a.numero,
        "piso": a.piso,
        "area_m2": a.area_m2,
        "habitaciones": a.habitaciones,
        "banos": a.banos,
        "parqueaderos": a.parqueaderos,
        "coeficiente": a.coeficiente,
        "deudor": a.deudor,
        "parqueaderos_asignados": [salida_parqueadero(p, con_apto=False) for p in parqueaderos],
        "propietarios": [p for p in personas if p["rol"] == "propietario"],
        "arrendatarios": [p for p in personas if p["rol"] == "arrendatario"],
    }


def salida_zona(z: ZonaComun) -> dict:
    return {
        "id": z.id,
        "slug": z.slug,
        "nombre": z.nombre,
        "icono": z.icono,
        "resumen": z.resumen,
        "descripcion": z.descripcion,
        "horario": z.horario,
        "orden": z.orden,
        "fotos": [{"id": f.id, "url": f"/uploads/{f.archivo}"} for f in z.fotos],
    }


def slug_libre(db: Session, nombre: str, excepto: int | None = None) -> str:
    """'Salón comunal' -> 'salon-comunal' (agrega -2, -3... si ya existe)."""
    base = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode().lower()
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-") or "zona"
    slug, n = base, 2
    while True:
        consulta = select(ZonaComun.id).where(ZonaComun.slug == slug)
        if excepto:
            consulta = consulta.where(ZonaComun.id != excepto)
        if not db.scalars(consulta).first():
            return slug
        slug, n = f"{base}-{n}", n + 1


def obtener_zona(db: Session, zona_id: int) -> ZonaComun:
    zona = db.scalars(
        select(ZonaComun).options(selectinload(ZonaComun.fotos)).where(ZonaComun.id == zona_id)
    ).first()
    if not zona:
        raise HTTPException(404, "Zona no encontrada")
    return zona


# ---------- API ----------

@app.get("/api/tipos")
def listar_tipos(db: Session = Depends(get_db)):
    tipos = db.scalars(select(TipoPropiedad).order_by(TipoPropiedad.nombre))
    return [{"id": t.id, "nombre": t.nombre} for t in tipos]


@app.get("/api/edificio")
def datos_edificio():
    """Valores por defecto de los avisos (todos son del mismo edificio)."""
    return EDIFICIO


@app.get("/api/propiedades")
def listar(
    estado: str = "",
    tipo_id: int | None = None,
    negocio: str = "",
    mias: bool = False,
    apartamento_id: int | None = None,
    db: Session = Depends(get_db),
    usuario: Usuario | None = Depends(usuario_actual),
):
    consulta = select(Propiedad).options(
        selectinload(Propiedad.fotos), selectinload(Propiedad.disponibilidad)
    )
    privado = bool(usuario) and (mias or es_admin(usuario))
    if mias:
        # Avisos de los apartamentos del propietario (en cualquier estado)
        if not usuario:
            raise HTTPException(401, "Inicia sesión para continuar")
        consulta = consulta.where(Propiedad.apartamento_id.in_(apartamentos_propios(usuario, db)))
    elif estado != "publicado" or apartamento_id:
        # Sin sesión de administración solo se ven las propiedades publicadas.
        requiere_admin(usuario)
    if apartamento_id:
        consulta = consulta.where(Propiedad.apartamento_id == apartamento_id)
    if estado in ESTADOS:
        consulta = consulta.where(Propiedad.estado == estado)
    if tipo_id:
        consulta = consulta.where(Propiedad.tipo_id == tipo_id)
    if negocio in NEGOCIOS:
        consulta = consulta.where(Propiedad.negocio == negocio)
    return [salida(p, privado=privado) for p in db.scalars(consulta.order_by(Propiedad.id.desc()))]


@app.post("/api/propiedades", status_code=201)
def crear(
    datos: PropiedadIn,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_sesion),
):
    valores, apto = completar_aviso(datos, usuario, db)
    prop = Propiedad(**valores, usuario_id=usuario.id)
    copiar_caracteristicas(prop, apto)
    guardar_disponibilidad(prop, datos)
    db.add(prop)
    db.commit()
    return {**salida(obtener(db, prop.id), con_anuncio=True, privado=True), "puede_editar": True}


@app.get("/api/propiedades/{prop_id}")
def detalle(
    prop_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario | None = Depends(usuario_actual),
):
    prop = obtener(db, prop_id)
    if prop.estado != "publicado":
        requiere_editor(prop, usuario, db)
    editor = puede_editar(prop, usuario, db)
    return {**salida(prop, con_anuncio=True, privado=editor), "puede_editar": editor}


@app.put("/api/propiedades/{prop_id}")
def actualizar(
    prop_id: int, datos: PropiedadIn,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_sesion),
):
    prop = obtener(db, prop_id)
    requiere_editor(prop, usuario, db)
    valores, apto = completar_aviso(datos, usuario, db)
    for campo, valor in valores.items():
        setattr(prop, campo, valor)
    copiar_caracteristicas(prop, apto)
    guardar_disponibilidad(prop, datos)
    db.commit()
    return {**salida(obtener(db, prop_id), con_anuncio=True, privado=True), "puede_editar": True}


@app.patch("/api/propiedades/{prop_id}/estado")
def cambiar_estado(
    prop_id: int, datos: EstadoIn,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_sesion),
):
    if datos.estado not in ESTADOS:
        raise HTTPException(400, "Estado no válido")
    prop = obtener(db, prop_id)
    requiere_editor(prop, usuario, db)
    prop.estado = datos.estado
    db.commit()
    return {**salida(prop, con_anuncio=True, privado=True), "puede_editar": True}


@app.delete("/api/propiedades/{prop_id}", status_code=204)
def eliminar(
    prop_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_sesion),
):
    prop = obtener(db, prop_id)
    requiere_editor(prop, usuario, db)
    db.delete(prop)
    db.commit()
    shutil.rmtree(UPLOADS / str(prop_id), ignore_errors=True)
    return Response(status_code=204)


@app.post("/api/propiedades/{prop_id}/fotos")
def subir_fotos(
    prop_id: int,
    fotos: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_sesion),
):
    prop = obtener(db, prop_id)
    requiere_editor(prop, usuario, db)
    disponibles = MAX_FOTOS - len(prop.fotos)
    if len(fotos) > disponibles:
        raise HTTPException(
            400,
            f"Cada aviso admite máximo {MAX_FOTOS} fotos; "
            + (f"puedes subir {disponibles} más." if disponibles else "ya está completo."),
        )
    for archivo in fotos:
        if archivo.size and archivo.size > MAX_MB_FOTO * 1024 * 1024:
            raise HTTPException(400, f"La foto «{archivo.filename}» pesa más de {MAX_MB_FOTO} MB")
    for archivo in fotos:
        ruta = guardar_foto(str(prop.id), archivo.file)
        if ruta:
            db.add(Foto(propiedad_id=prop.id, archivo=ruta))
    db.commit()
    db.refresh(prop, attribute_names=["fotos"])  # recarga la lista de fotos
    return {**salida(prop, con_anuncio=True, privado=True), "puede_editar": True}


@app.patch("/api/fotos/{foto_id}/principal")
def marcar_principal(
    foto_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_sesion),
):
    """Elige la foto de portada del aviso (la que se ve en las tarjetas)."""
    foto = db.get(Foto, foto_id)
    if not foto:
        raise HTTPException(404, "Foto no encontrada")
    prop = obtener(db, foto.propiedad_id)
    requiere_editor(prop, usuario, db)
    for f in prop.fotos:
        f.principal = f.id == foto.id
    db.commit()
    return {**salida(prop, con_anuncio=True, privado=True), "puede_editar": True}


@app.delete("/api/fotos/{foto_id}", status_code=204)
def borrar_foto(
    foto_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_sesion),
):
    foto = db.get(Foto, foto_id)
    if not foto:
        raise HTTPException(404, "Foto no encontrada")
    requiere_editor(foto.propiedad, usuario, db)
    (UPLOADS / foto.archivo).unlink(missing_ok=True)
    db.delete(foto)
    db.commit()
    return Response(status_code=204)


# ---------- parqueaderos (solo administración) ----------

def validar_parqueadero(datos: ParqueaderoIn, db: Session, excepto: int | None = None) -> None:
    consulta = select(Parqueadero.id).where(Parqueadero.numero == datos.numero)
    if excepto:
        consulta = consulta.where(Parqueadero.id != excepto)
    if db.scalars(consulta).first():
        raise HTTPException(409, f"Ya existe el parqueadero {datos.numero}")
    if datos.apartamento_id:
        if datos.uso != "residente":
            raise HTTPException(400, "Los parqueaderos de visitantes no se asignan a un apartamento")
        if not db.get(Apartamento, datos.apartamento_id):
            raise HTTPException(400, "Apartamento no válido")


@app.get("/api/parqueaderos")
def listar_parqueaderos(
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_admin),
):
    liberar_vencidos(db)
    return [
        salida_parqueadero(p)
        for p in sorted(db.scalars(select(Parqueadero)), key=lambda p: orden_texto(p.numero))
    ]


@app.post("/api/parqueaderos", status_code=201)
def crear_parqueadero(
    datos: ParqueaderoIn,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_admin),
):
    validar_parqueadero(datos, db)
    parq = Parqueadero(**datos.model_dump())
    if parq.apartamento_id:
        parq.asignado_desde = ahora_bogota().date()
    db.add(parq)
    recalcular_parqueaderos(parq.apartamento_id, db)
    db.commit()
    return salida_parqueadero(parq)


@app.post("/api/parqueaderos/lote", status_code=201)
def crear_parqueaderos_lote(
    datos: LoteParqueaderosIn,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_admin),
):
    """Crea una serie (P-1 ... P-40); omite los números que ya existen."""
    if datos.hasta < datos.desde:
        raise HTTPException(400, "El número final debe ser mayor o igual al inicial")
    if datos.hasta - datos.desde >= 500:
        raise HTTPException(400, "Máximo 500 parqueaderos por lote")
    prefijo = datos.prefijo.strip()
    existentes = set(db.scalars(select(Parqueadero.numero)))
    creados, omitidos = [], []
    for n in range(datos.desde, datos.hasta + 1):
        numero = f"{prefijo}{n}"
        if numero in existentes:
            omitidos.append(numero)
            continue
        parq = Parqueadero(numero=numero, tipo=datos.tipo, uso=datos.uso, ubicacion=datos.ubicacion.strip())
        db.add(parq)
        creados.append(parq)
    db.commit()
    return {"creados": len(creados), "omitidos": omitidos}


@app.put("/api/parqueaderos/{parq_id}")
def actualizar_parqueadero(
    parq_id: int,
    datos: ParqueaderoIn,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_admin),
):
    parq = db.get(Parqueadero, parq_id)
    if not parq:
        raise HTTPException(404, "Parqueadero no encontrado")
    validar_parqueadero(datos, db, excepto=parq_id)
    antes = parq.apartamento_id
    for campo, valor in datos.model_dump().items():
        setattr(parq, campo, valor)
    if not parq.apartamento_id:
        parq.asignado_desde = parq.asignado_hasta = None
    elif parq.apartamento_id != antes:
        parq.asignado_desde = ahora_bogota().date()
    recalcular_parqueaderos(antes, db)
    if parq.apartamento_id != antes:
        recalcular_parqueaderos(parq.apartamento_id, db)
    db.commit()
    db.refresh(parq)
    return salida_parqueadero(parq)


@app.delete("/api/parqueaderos/{parq_id}", status_code=204)
def eliminar_parqueadero(
    parq_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_admin),
):
    parq = db.get(Parqueadero, parq_id)
    if not parq:
        raise HTTPException(404, "Parqueadero no encontrado")
    apto_id = parq.apartamento_id
    db.delete(parq)
    recalcular_parqueaderos(apto_id, db)
    db.commit()
    return Response(status_code=204)


# ---------- sorteos de parqueaderos ----------

def obtener_sorteo(db: Session, sorteo_id: int) -> Sorteo:
    sorteo = db.scalars(
        select(Sorteo)
        .options(selectinload(Sorteo.parqueaderos), selectinload(Sorteo.postulaciones))
        .where(Sorteo.id == sorteo_id)
    ).first()
    if not sorteo:
        raise HTTPException(404, "Sorteo no encontrado")
    return sorteo


def salida_postulacion(p: Postulacion) -> dict:
    return {
        "id": p.id,
        "apartamento": {
            "id": p.apartamento.id, "torre": p.apartamento.torre, "numero": p.apartamento.numero,
            "deudor": p.apartamento.deudor,
        },
        "posicion": p.posicion,
        "excluido": p.excluido,
        "parqueadero": p.parqueadero.numero if p.parqueadero else None,
        "creado": p.creado,
    }


def salida_sorteo(s: Sorteo, detalle: bool = False) -> dict:
    datos = {
        "id": s.id,
        "nombre": s.nombre,
        "tipo": s.tipo,
        "meses": s.meses,
        "inicio": s.inicio.isoformat(),
        "fin": sumar_meses(s.inicio, s.meses).isoformat(),
        "cierre": s.cierre.isoformat(),
        "estado": s.estado,
        "abierto": s.estado == "abierto" and s.cierre >= ahora_bogota().date(),
        "semilla": s.semilla,
        "realizado_en": s.realizado_en,
        "num_parqueaderos": len(s.parqueaderos),
        "num_postulaciones": len(s.postulaciones),
    }
    if detalle:
        datos["parqueaderos"] = [
            salida_parqueadero(p) for p in sorted(s.parqueaderos, key=lambda p: orden_texto(p.numero))
        ]
        postulaciones = sorted(s.postulaciones, key=lambda p: (p.posicion or 10**6, orden_numero(p.apartamento)))
        datos["postulaciones"] = [salida_postulacion(p) for p in postulaciones]
    return datos


def elegir_parqueaderos(datos: SorteoIn, db: Session) -> list[Parqueadero]:
    consulta = select(Parqueadero).where(Parqueadero.uso == "residente", Parqueadero.tipo == datos.tipo)
    if datos.parqueadero_ids is not None:
        consulta = consulta.where(Parqueadero.id.in_(datos.parqueadero_ids))
    parqueaderos = db.scalars(consulta).all()
    if not parqueaderos:
        raise HTTPException(400, f"No hay parqueaderos de residentes para {datos.tipo}s en este sorteo")
    return parqueaderos


@app.get("/api/sorteos")
def listar_sorteos(db: Session = Depends(get_db), _: Usuario = Depends(requiere_admin)):
    sorteos = db.scalars(
        select(Sorteo).options(selectinload(Sorteo.parqueaderos), selectinload(Sorteo.postulaciones))
        .order_by(Sorteo.id.desc())
    )
    return [salida_sorteo(s) for s in sorteos]


@app.post("/api/sorteos", status_code=201)
def crear_sorteo(datos: SorteoIn, db: Session = Depends(get_db), _: Usuario = Depends(requiere_admin)):
    sorteo = Sorteo(**datos.model_dump(exclude={"parqueadero_ids"}))
    sorteo.parqueaderos = elegir_parqueaderos(datos, db)
    db.add(sorteo)
    db.commit()
    return salida_sorteo(obtener_sorteo(db, sorteo.id), detalle=True)


@app.get("/api/sorteos/{sorteo_id}")
def ver_sorteo(sorteo_id: int, db: Session = Depends(get_db), _: Usuario = Depends(requiere_admin)):
    return salida_sorteo(obtener_sorteo(db, sorteo_id), detalle=True)


@app.put("/api/sorteos/{sorteo_id}")
def actualizar_sorteo(
    sorteo_id: int, datos: SorteoIn, db: Session = Depends(get_db), _: Usuario = Depends(requiere_admin)
):
    sorteo = obtener_sorteo(db, sorteo_id)
    if sorteo.estado == "realizado":
        raise HTTPException(400, "El sorteo ya se realizó")
    for campo, valor in datos.model_dump(exclude={"parqueadero_ids"}).items():
        setattr(sorteo, campo, valor)
    sorteo.parqueaderos = elegir_parqueaderos(datos, db)
    db.commit()
    return salida_sorteo(obtener_sorteo(db, sorteo_id), detalle=True)


@app.delete("/api/sorteos/{sorteo_id}", status_code=204)
def eliminar_sorteo(sorteo_id: int, db: Session = Depends(get_db), _: Usuario = Depends(requiere_admin)):
    sorteo = obtener_sorteo(db, sorteo_id)
    if sorteo.estado == "realizado":
        raise HTTPException(400, "Un sorteo realizado no se elimina: es el respaldo de las asignaciones")
    db.delete(sorteo)
    db.commit()
    return Response(status_code=204)


@app.post("/api/sorteos/{sorteo_id}/postulaciones", status_code=201)
def inscribir_apartamento(
    sorteo_id: int, datos: PostulacionIn, db: Session = Depends(get_db), admin: Usuario = Depends(requiere_admin)
):
    """La administración inscribe un apartamento (aunque ya haya pasado la fecha de cierre)."""
    sorteo = obtener_sorteo(db, sorteo_id)
    return postular(sorteo, datos.apartamento_id, admin, db, validar_cierre=False)


@app.post("/api/sorteos/{sorteo_id}/postular", status_code=201)
def postular_mi_apartamento(
    sorteo_id: int, datos: PostulacionIn, db: Session = Depends(get_db), usuario: Usuario = Depends(requiere_sesion)
):
    """Propietario o arrendatario activo postula su apartamento antes del cierre."""
    if datos.apartamento_id not in {a["id"] for a in perfil(usuario, db)["apartamentos"]}:
        raise HTTPException(403, "Solo puedes postular tu propio apartamento")
    return postular(obtener_sorteo(db, sorteo_id), datos.apartamento_id, usuario, db, validar_cierre=True)


def postular(sorteo: Sorteo, apto_id: int, usuario: Usuario, db: Session, validar_cierre: bool) -> dict:
    if sorteo.estado != "abierto":
        raise HTTPException(400, "El sorteo ya se realizó")
    if validar_cierre and sorteo.cierre < ahora_bogota().date():
        raise HTTPException(400, "Las postulaciones de este sorteo ya cerraron")
    apto = db.get(Apartamento, apto_id)
    if not apto:
        raise HTTPException(400, "Apartamento no válido")
    if apto.deudor:
        raise HTTPException(
            400, f"El Apto {apto.numero} tiene saldo pendiente con la administración: solo participan los que están al día"
        )
    if any(p.apartamento_id == apto_id for p in sorteo.postulaciones):
        raise HTTPException(409, "Ese apartamento ya está inscrito en este sorteo")
    post = Postulacion(sorteo_id=sorteo.id, apartamento_id=apto_id, usuario_id=usuario.id)
    db.add(post)
    db.commit()
    return salida_postulacion(db.get(Postulacion, post.id))


@app.delete("/api/postulaciones/{post_id}", status_code=204)
def retirar_postulacion(post_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(requiere_sesion)):
    post = db.get(Postulacion, post_id)
    if not post:
        raise HTTPException(404, "Postulación no encontrada")
    if not es_admin(usuario) and post.apartamento_id not in {a["id"] for a in perfil(usuario, db)["apartamentos"]}:
        raise HTTPException(403, "Solo puedes retirar la postulación de tu apartamento")
    if post.sorteo.estado != "abierto":
        raise HTTPException(400, "El sorteo ya se realizó")
    db.delete(post)
    db.commit()
    return Response(status_code=204)


@app.post("/api/sorteos/{sorteo_id}/realizar")
def realizar_sorteo(sorteo_id: int, db: Session = Depends(get_db), _: Usuario = Depends(requiere_admin)):
    """Ordena al azar a los postulantes: los primeros reciben un parqueadero por los meses del
    sorteo; los demás quedan en lista de espera en el orden en que salieron."""
    liberar_vencidos(db)
    sorteo = obtener_sorteo(db, sorteo_id)
    if sorteo.estado != "abierto":
        raise HTTPException(400, "El sorteo ya se realizó")
    if not sorteo.postulaciones:
        raise HTTPException(400, "No hay apartamentos postulados")
    # Solo participan los que están al día: quien quedó en mora después de postularse sale
    for post in sorteo.postulaciones:
        post.excluido = post.apartamento.deudor
    participantes = [p for p in sorteo.postulaciones if not p.excluido]
    if not participantes:
        raise HTTPException(400, "Todos los postulados están en mora; no hay quién participe")
    sorteo.semilla = secrets.token_hex(8)
    orden = sorted(participantes, key=lambda p: p.id)
    random.Random(sorteo.semilla).shuffle(orden)  # reproducible con la semilla guardada
    cupos = sorted(sorteo.parqueaderos, key=lambda p: orden_texto(p.numero))
    fin = sumar_meses(sorteo.inicio, sorteo.meses)
    afectados = set()
    for i, post in enumerate(orden):
        post.posicion = i + 1
        if i < len(cupos):
            parq = cupos[i]
            afectados.update({parq.apartamento_id, post.apartamento_id})
            parq.apartamento_id = post.apartamento_id
            parq.asignado_desde, parq.asignado_hasta = sorteo.inicio, fin
            post.parqueadero_id = parq.id
    sorteo.estado = "realizado"
    sorteo.realizado_en = ahora_bogota()
    for apto_id in afectados:
        recalcular_parqueaderos(apto_id, db)
    db.commit()
    db.expire_all()  # recarga el parqueadero de cada postulación antes de avisar
    sorteo = obtener_sorteo(db, sorteo_id)
    avisar_resultados(sorteo, db)
    return salida_sorteo(obtener_sorteo(db, sorteo_id), detalle=True)


def avisar_resultados(sorteo: Sorteo, db: Session) -> None:
    fin = sumar_meses(sorteo.inicio, sorteo.meses)
    for post in sorteo.postulaciones:
        # A los propietarios y arrendatarios activos del apartamento (aunque lo haya inscrito la administración)
        destinos = {(p.email, p.nombre) for p in post.apartamento.personas if p.activo and p.email}
        if post.excluido:
            texto = (
                f"El Apto {post.apartamento.numero} no participó en el sorteo porque tenía saldo "
                "pendiente con la administración."
            )
        elif post.parqueadero:
            texto = (
                f"Al Apto {post.apartamento.numero} le correspondió el parqueadero {post.parqueadero.numero} "
                f"del {sorteo.inicio:%d/%m/%Y} al {fin:%d/%m/%Y}."
            )
        else:
            texto = f"El Apto {post.apartamento.numero} quedó en la lista de espera, en la posición {post.posicion}."
        for email, nombre in destinos:
            correo.enviar(
                email,
                f"Resultado del sorteo · {sorteo.nombre}",
                f"Hola, {nombre}:\n\n{texto}\n\nAdministración · Trend Apartamentos",
            )


@app.get("/api/mis-sorteos")
def mis_sorteos(db: Session = Depends(get_db), usuario: Usuario = Depends(requiere_sesion)):
    """Sorteos abiertos y realizados con la postulación de los apartamentos del usuario."""
    mis_aptos = {a["id"]: a for a in perfil(usuario, db)["apartamentos"]}
    if not mis_aptos:
        return []
    resultado = []
    for s in db.scalars(
        select(Sorteo).options(selectinload(Sorteo.parqueaderos), selectinload(Sorteo.postulaciones))
        .order_by(Sorteo.id.desc())
    ):
        mias = {p.apartamento_id: p for p in s.postulaciones if p.apartamento_id in mis_aptos}
        if s.estado == "realizado" and not mias:
            continue  # solo los realizados en los que participó
        resultado.append({
            **salida_sorteo(s),
            "apartamentos": [
                {
                    "id": apto_id,
                    "numero": a["numero"],
                    "torre": a["torre"],
                    "deudor": bool(db.get(Apartamento, apto_id).deudor),
                    "postulacion": salida_postulacion(mias[apto_id]) if apto_id in mias else None,
                }
                for apto_id, a in mis_aptos.items()
            ],
        })
    return resultado


# ---------- visitas ----------

def ahora_bogota() -> datetime:
    return datetime.now(ZONA_HORARIA).replace(tzinfo=None)


def horas_libres(prop: Propiedad, db: Session) -> list[dict]:
    """Horas disponibles para visitar en los próximos días (sin las ya tomadas ni las pasadas)."""
    ahora = ahora_bogota()
    tomadas = {
        (v.fecha, v.hora)
        for v in db.scalars(
            select(Visita).where(
                Visita.propiedad_id == prop.id,
                Visita.estado != "cancelada",
                Visita.fecha >= ahora.date(),
            )
        )
    }
    dias = []
    for n in range(DIAS_AGENDA):
        fecha = ahora.date() + timedelta(days=n)
        horas = []
        for f in prop.disponibilidad:
            if f.dia != fecha.weekday():
                continue
            m = minutos(f.inicio)
            while m + prop.duracion_visita <= minutos(f.fin):
                hora = f"{m // 60:02d}:{m % 60:02d}"
                momento = datetime.combine(fecha, datetime.min.time()) + timedelta(minutes=m)
                # al menos 1 hora de anticipación
                if momento > ahora + timedelta(hours=1) and (fecha, hora) not in tomadas:
                    horas.append(hora)
                m += prop.duracion_visita
        if horas:
            dias.append({"fecha": fecha.isoformat(), "dia": DIAS[fecha.weekday()], "horas": sorted(set(horas))})
    return dias


def salida_visita(v: Visita) -> dict:
    return {
        "id": v.id,
        "fecha": v.fecha.isoformat(),
        "dia": DIAS[v.fecha.weekday()],
        "hora": v.hora,
        "nombre": v.nombre,
        "telefono": v.telefono,
        "email": v.email,
        "mensaje": v.mensaje,
        "estado": v.estado,
        "creado": v.creado,
    }


def fecha_texto(v: Visita) -> str:
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
             "septiembre", "octubre", "noviembre", "diciembre"]
    return f"{DIAS[v.fecha.weekday()]} {v.fecha.day} de {meses[v.fecha.month - 1]} a las {v.hora}"


def avisar_nueva_visita(prop: Propiedad, v: Visita, db: Session) -> None:
    """Correo a quien publicó el aviso y, si dejó correo, confirmación al visitante."""
    enlace = f"{SITIO_URL}/#/propiedades/{prop.id}"
    creador = db.get(Usuario, prop.usuario_id) if prop.usuario_id else None
    if creador:
        correo.enviar(
            creador.email,
            f"Nueva visita agendada · {prop.titulo}",
            f"Hola, {creador.nombre}:\n\n{v.nombre} agendó una visita para el {fecha_texto(v)}.\n"
            f"Teléfono: {v.telefono}\n" + (f"Correo: {v.email}\n" if v.email else "")
            + (f"Mensaje: {v.mensaje}\n" if v.mensaje else "")
            + f"\nConfírmala o cancélala en el aviso:\n{enlace}\n\nTrend Apartamentos",
        )
    if v.email:
        correo.enviar(
            v.email,
            f"Solicitud de visita · {prop.titulo}",
            f"Hola, {v.nombre}:\n\nRecibimos tu solicitud de visita para el {fecha_texto(v)} "
            f"al aviso «{prop.titulo}».\nTe contactaremos para confirmarla.\n\n"
            f"Teléfonos de contacto: {prop.telefonos}\n{enlace}\n\nTrend Apartamentos",
        )


@app.get("/api/propiedades/{prop_id}/horarios")
def horarios_visita(
    prop_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario | None = Depends(usuario_actual),
):
    prop = obtener(db, prop_id)
    if prop.estado != "publicado":
        requiere_editor(prop, usuario, db)
    return {"duracion": prop.duracion_visita, "dias": horas_libres(prop, db)}


@app.post("/api/propiedades/{prop_id}/visitas", status_code=201)
def agendar_visita(prop_id: int, datos: VisitaIn, db: Session = Depends(get_db)):
    """Cualquier persona que ve el aviso agenda una visita en una hora libre."""
    prop = obtener(db, prop_id)
    if prop.estado != "publicado":
        raise HTTPException(400, "Este aviso no está publicado")
    libres = {(d["fecha"], h) for d in horas_libres(prop, db) for h in d["horas"]}
    if (datos.fecha.isoformat(), datos.hora) not in libres:
        raise HTTPException(409, "Esa hora ya no está disponible. Elige otra.")
    pendientes = db.scalars(
        select(Visita).where(
            Visita.propiedad_id == prop.id,
            Visita.telefono == datos.telefono,
            Visita.estado == "pendiente",
            Visita.fecha >= ahora_bogota().date(),
        )
    ).all()
    if len(pendientes) >= 2:
        raise HTTPException(429, "Ya tienes visitas pendientes para este aviso")
    visita = Visita(propiedad_id=prop.id, **datos.model_dump())
    visita.nombre = visita.nombre.strip()
    db.add(visita)
    db.commit()
    avisar_nueva_visita(prop, visita, db)
    return salida_visita(visita)


@app.get("/api/propiedades/{prop_id}/visitas")
def listar_visitas(
    prop_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_sesion),
):
    """Visitas del aviso para quien lo publicó y la administración (próximas primero)."""
    prop = obtener(db, prop_id)
    requiere_editor(prop, usuario, db)
    hoy = ahora_bogota().date()
    visitas = db.scalars(select(Visita).where(Visita.propiedad_id == prop.id)).all()
    proximas = sorted((v for v in visitas if v.fecha >= hoy), key=lambda v: (v.fecha, v.hora))
    pasadas = sorted((v for v in visitas if v.fecha < hoy), key=lambda v: (v.fecha, v.hora), reverse=True)
    return [salida_visita(v) for v in proximas + pasadas]


@app.patch("/api/visitas/{visita_id}")
def cambiar_estado_visita(
    visita_id: int,
    datos: EstadoVisitaIn,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_sesion),
):
    visita = db.get(Visita, visita_id)
    if not visita:
        raise HTTPException(404, "Visita no encontrada")
    prop = obtener(db, visita.propiedad_id)
    requiere_editor(prop, usuario, db)
    if visita.estado == "cancelada" and datos.estado != "cancelada":
        raise HTTPException(400, "Esa visita ya fue cancelada; su hora pudo tomarla otra persona")
    anterior, visita.estado = visita.estado, datos.estado
    db.commit()
    if visita.email and anterior != datos.estado and datos.estado != "pendiente":
        texto = "confirmada" if datos.estado == "confirmada" else "cancelada"
        correo.enviar(
            visita.email,
            f"Visita {texto} · {prop.titulo}",
            f"Hola, {visita.nombre}:\n\nTu visita del {fecha_texto(visita)} fue {texto}.\n"
            f"Teléfonos de contacto: {prop.telefonos}\n\nTrend Apartamentos",
        )
    return salida_visita(visita)


# ---------- blog de noticias ----------

@app.get("/api/noticias")
def listar_noticias(
    todas: bool = False,
    limite: int | None = None,
    db: Session = Depends(get_db),
    usuario: Usuario | None = Depends(usuario_actual),
):
    """Por defecto solo las publicadas; con ?todas=true también los borradores (administración)."""
    if todas:
        requiere_admin(usuario)
    consulta = select(Noticia).order_by(Noticia.creado.desc(), Noticia.id.desc())
    if not todas:
        consulta = consulta.where(Noticia.publicada.is_(True))
    if limite:
        consulta = consulta.limit(limite)
    return [salida_noticia(n) for n in db.scalars(consulta)]


@app.post("/api/noticias", status_code=201)
def crear_noticia(
    datos: NoticiaIn,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_admin),
):
    noticia = Noticia(**datos.model_dump())
    db.add(noticia)
    db.commit()
    db.refresh(noticia)
    return salida_noticia(noticia)


@app.get("/api/noticias/{noticia_id}")
def ver_noticia(
    noticia_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario | None = Depends(usuario_actual),
):
    noticia = obtener_noticia(db, noticia_id)
    if not noticia.publicada:
        requiere_admin(usuario)
    return salida_noticia(noticia)


@app.put("/api/noticias/{noticia_id}")
def actualizar_noticia(
    noticia_id: int, datos: NoticiaIn,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_admin),
):
    noticia = obtener_noticia(db, noticia_id)
    for campo, valor in datos.model_dump().items():
        setattr(noticia, campo, valor)
    db.commit()
    return salida_noticia(noticia)


@app.delete("/api/noticias/{noticia_id}", status_code=204)
def eliminar_noticia(
    noticia_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_admin),
):
    noticia = obtener_noticia(db, noticia_id)
    db.delete(noticia)
    db.commit()
    shutil.rmtree(UPLOADS / "noticias" / str(noticia_id), ignore_errors=True)
    return Response(status_code=204)


@app.post("/api/noticias/{noticia_id}/imagen")
def subir_imagen_noticia(
    noticia_id: int,
    imagen: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_admin),
):
    """Sube la imagen de portada; reemplaza la anterior si existía."""
    noticia = obtener_noticia(db, noticia_id)
    ruta = guardar_foto(f"noticias/{noticia_id}", imagen.file)
    if not ruta:
        raise HTTPException(400, "El archivo no es una imagen válida")
    if noticia.imagen:
        (UPLOADS / noticia.imagen).unlink(missing_ok=True)
    noticia.imagen = ruta
    db.commit()
    return salida_noticia(noticia)


@app.delete("/api/noticias/{noticia_id}/imagen")
def borrar_imagen_noticia(
    noticia_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_admin),
):
    noticia = obtener_noticia(db, noticia_id)
    if noticia.imagen:
        (UPLOADS / noticia.imagen).unlink(missing_ok=True)
        noticia.imagen = None
        db.commit()
    return salida_noticia(noticia)


# ---------- apartamentos del conjunto (solo administración) ----------

@app.get("/api/apartamentos")
def listar_apartamentos(
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_admin),
):
    liberar_vencidos(db)
    consulta = select(Apartamento).options(selectinload(Apartamento.personas))
    return [salida_apartamento(a, db) for a in sorted(db.scalars(consulta), key=orden_numero)]


@app.post("/api/apartamentos", status_code=201)
def crear_apartamento(
    datos: ApartamentoNuevoIn,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_admin),
):
    validar_numero_libre(db, datos)
    ids = [p.identificacion for p in datos.propietarios]
    if len(ids) != len(set(ids)):
        raise HTTPException(409, "Hay propietarios repetidos con la misma identificación")
    apto = Apartamento(**datos.model_dump(exclude={"propietarios"}))
    apto.personas = [
        PersonaApartamento(rol="propietario", **p.model_dump()) for p in datos.propietarios
    ]
    validar_propietario_activo(apto)
    db.add(apto)
    db.commit()
    invitaciones = invitar_personas(apto.personas, db)
    return {**salida_apartamento(obtener_apartamento(db, apto.id), db), "invitaciones": invitaciones}


@app.get("/api/apartamentos/{apto_id}")
def ver_apartamento(
    apto_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_admin),
):
    return salida_apartamento(obtener_apartamento(db, apto_id), db)


@app.put("/api/apartamentos/{apto_id}")
def actualizar_apartamento(
    apto_id: int,
    datos: ApartamentoIn,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_admin),
):
    apto = obtener_apartamento(db, apto_id)
    validar_numero_libre(db, datos, excepto=apto_id)
    for campo, valor in datos.model_dump().items():
        setattr(apto, campo, valor)
    for prop in db.scalars(select(Propiedad).where(Propiedad.apartamento_id == apto_id)):
        copiar_caracteristicas(prop, apto)
    db.commit()
    return salida_apartamento(apto, db)


@app.delete("/api/apartamentos/{apto_id}", status_code=204)
def eliminar_apartamento(
    apto_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_admin),
):
    # Sus parqueaderos quedan libres
    for parq in db.scalars(select(Parqueadero).where(Parqueadero.apartamento_id == apto_id)):
        parq.apartamento_id = None
    db.delete(obtener_apartamento(db, apto_id))
    db.commit()
    return Response(status_code=204)


@app.post("/api/apartamentos/{apto_id}/personas", status_code=201)
def agregar_persona(
    apto_id: int,
    datos: PersonaNuevaIn,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_admin),
):
    """Agrega un propietario o un arrendatario al apartamento."""
    apto = obtener_apartamento(db, apto_id)
    if datos.activo:
        validar_identificacion(apto, datos.rol, datos.identificacion)
    persona = PersonaApartamento(**datos.model_dump())
    apto.personas.append(persona)
    db.commit()
    invitaciones = invitar_personas([persona], db)
    return {**salida_apartamento(obtener_apartamento(db, apto_id), db), "invitaciones": invitaciones}


@app.put("/api/personas/{persona_id}")
def actualizar_persona(
    persona_id: int,
    datos: PersonaIn,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_admin),
):
    """Edita los datos o el estado (activo / inactivo) de un propietario o arrendatario."""
    persona = db.get(PersonaApartamento, persona_id)
    if not persona:
        raise HTTPException(404, "Persona no encontrada")
    apto = obtener_apartamento(db, persona.apartamento_id)
    if datos.activo:
        validar_identificacion(apto, persona.rol, datos.identificacion, excepto=persona.id)
    for campo, valor in datos.model_dump().items():
        setattr(persona, campo, valor)
    validar_propietario_activo(apto)
    db.commit()
    return salida_apartamento(apto, db)


@app.delete("/api/personas/{persona_id}")
def eliminar_persona(
    persona_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_admin),
):
    """Borra un registro hecho por error. Para cambios en el tiempo, mejor inactivar."""
    persona = db.get(PersonaApartamento, persona_id)
    if not persona:
        raise HTTPException(404, "Persona no encontrada")
    apto = obtener_apartamento(db, persona.apartamento_id)
    apto.personas.remove(persona)
    validar_propietario_activo(apto)
    db.commit()
    return salida_apartamento(apto, db)


@app.post("/api/usuarios", status_code=201)
def registrar(
    datos: UsuarioIn,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_admin),
):
    """Solo la administración crea cuentas; nacen verificadas porque ella confirmó la identidad."""
    if db.scalars(select(Usuario).where(Usuario.email == datos.email)).first():
        raise HTTPException(409, "Ya existe una cuenta con ese correo")
    usuario = Usuario(
        nombre=datos.nombre.strip(),
        email=datos.email,
        telefono=datos.telefono.strip(),
        identificacion=datos.identificacion,
        clave_hash=hash_clave(datos.clave),
        verificado=True,
    )
    db.add(usuario)
    db.commit()
    return perfil(usuario, db, para_admin=True)


@app.patch("/api/usuarios/{usuario_id}/clave")
def restablecer_clave(
    usuario_id: int,
    datos: ClaveIn,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(requiere_admin),
):
    """Asigna una contraseña nueva (por ejemplo, si la persona la olvidó)."""
    usuario = db.get(Usuario, usuario_id)
    if not usuario:
        raise HTTPException(404, "Usuario no encontrado")
    # Un administrador no puede tomar el control de otra cuenta de administración
    if rol_staff(usuario) and rol_staff(admin) != "superadmin" and usuario.id != admin.id:
        raise HTTPException(403, "Solo el super admin cambia contraseñas de la administración")
    usuario.clave_hash = hash_clave(datos.clave)
    db.commit()
    return perfil(usuario, db, para_admin=True)


@app.put("/api/perfil/clave")
def cambiar_mi_clave(
    datos: CambioClaveIn,
    usuario: Usuario = Depends(requiere_sesion),
    db: Session = Depends(get_db),
):
    if not verificar_clave(datos.actual, usuario.clave_hash):
        raise HTTPException(400, "La contraseña actual no es correcta")
    usuario.clave_hash = hash_clave(datos.nueva)
    db.commit()
    return {"ok": True}


@app.post("/api/personas/{persona_id}/invitacion")
def invitar_persona(
    persona_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_admin),
):
    """Crea la cuenta si no existe y envía (o reenvía) el enlace para crear la contraseña."""
    persona = db.get(PersonaApartamento, persona_id)
    if not persona:
        raise HTTPException(404, "Persona no encontrada")
    if not persona.email:
        raise HTTPException(400, "Agrega primero el correo de la persona")
    usuario, nueva = cuenta_para_persona(persona, db)
    db.commit()
    return enviar_invitacion(usuario, nueva)


@app.post("/api/usuarios/{usuario_id}/invitacion")
def invitar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(requiere_admin),
):
    """Envía a una cuenta existente el enlace para crear una contraseña nueva."""
    usuario = db.get(Usuario, usuario_id)
    if not usuario:
        raise HTTPException(404, "Usuario no encontrado")
    if rol_staff(usuario) and rol_staff(admin) != "superadmin" and usuario.id != admin.id:
        raise HTTPException(403, "Solo el super admin gestiona accesos de la administración")
    return enviar_invitacion(usuario, nueva=False)


@app.post("/api/activar")
def activar_cuenta(datos: ActivacionIn, db: Session = Depends(get_db)):
    """La persona crea su contraseña con el enlace del correo y queda con sesión iniciada."""
    usuario = usuario_de_invitacion(datos.token, db)
    if not usuario:
        raise HTTPException(400, "El enlace no es válido, ya se usó o venció. Pide uno nuevo a la administración.")
    usuario.clave_hash = hash_clave(datos.clave)
    db.commit()
    return {**perfil(usuario, db), "token": crear_token(usuario)}


@app.post("/api/sesion")
def iniciar_sesion(datos: SesionIn, db: Session = Depends(get_db)):
    """Valida correo y contraseña para entrar a la zona privada de residentes."""
    email = datos.email.strip().lower()
    usuario = db.scalars(select(Usuario).where(Usuario.email == email)).first()
    if not usuario or not verificar_clave(datos.clave, usuario.clave_hash):
        raise HTTPException(401, "Correo o contraseña incorrectos")
    return {**perfil(usuario, db), "token": crear_token(usuario)}


@app.get("/api/perfil")
def mi_perfil(usuario: Usuario = Depends(requiere_sesion), db: Session = Depends(get_db)):
    """Perfil actual (cambia si la administración activa o inactiva a la persona)."""
    return perfil(usuario, db)


@app.put("/api/perfil")
def actualizar_perfil(
    datos: PerfilIn,
    usuario: Usuario = Depends(requiere_sesion),
    db: Session = Depends(get_db),
):
    """El usuario corrige su teléfono o identificación; si cambia la identificación,
    la cuenta vuelve a quedar pendiente de verificación."""
    if datos.identificacion != usuario.identificacion:
        usuario.identificacion = datos.identificacion
        usuario.verificado = False
    usuario.telefono = datos.telefono.strip()
    db.commit()
    return perfil(usuario, db)


@app.get("/api/usuarios")
def listar_usuarios(
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_admin),
):
    usuarios = db.scalars(select(Usuario).order_by(Usuario.verificado, Usuario.nombre))
    return [perfil(u, db, para_admin=True) for u in usuarios]


@app.patch("/api/usuarios/{usuario_id}/verificacion")
def verificar_usuario(
    usuario_id: int,
    datos: VerificacionIn,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_admin),
):
    """La administración confirma (o retira) que la cuenta pertenece a esa persona."""
    usuario = db.get(Usuario, usuario_id)
    if not usuario:
        raise HTTPException(404, "Usuario no encontrado")
    usuario.verificado = datos.verificado
    db.commit()
    return perfil(usuario, db, para_admin=True)


@app.patch("/api/usuarios/{usuario_id}/rol")
def cambiar_rol(
    usuario_id: int,
    datos: RolIn,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_superadmin),
):
    """Nombra o quita administradores. Los super admin se definen en .env."""
    usuario = db.get(Usuario, usuario_id)
    if not usuario:
        raise HTTPException(404, "Usuario no encontrado")
    if usuario.email in SUPERADMIN_EMAILS:
        raise HTTPException(400, "Los super admin se configuran en el archivo .env")
    usuario.rol = datos.rol
    db.commit()
    return perfil(usuario, db, para_admin=True)


# ---------- zonas comunes ----------

@app.get("/api/zonas")
def listar_zonas(db: Session = Depends(get_db)):
    consulta = (
        select(ZonaComun)
        .options(selectinload(ZonaComun.fotos))
        .order_by(ZonaComun.orden, ZonaComun.id)
    )
    return [salida_zona(z) for z in db.scalars(consulta)]


@app.get("/api/zonas/{slug}")
def ver_zona(slug: str, db: Session = Depends(get_db)):
    zona = db.scalars(
        select(ZonaComun).options(selectinload(ZonaComun.fotos)).where(ZonaComun.slug == slug)
    ).first()
    if not zona:
        raise HTTPException(404, "Zona no encontrada")
    return salida_zona(zona)


@app.post("/api/zonas", status_code=201)
def crear_zona(
    datos: ZonaIn,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_admin),
):
    zona = ZonaComun(slug=slug_libre(db, datos.nombre), **datos.model_dump())
    db.add(zona)
    db.commit()
    return salida_zona(obtener_zona(db, zona.id))


@app.put("/api/zonas/{zona_id}")
def actualizar_zona(
    zona_id: int,
    datos: ZonaIn,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_admin),
):
    zona = obtener_zona(db, zona_id)
    if datos.nombre != zona.nombre:
        zona.slug = slug_libre(db, datos.nombre, excepto=zona_id)
    for campo, valor in datos.model_dump().items():
        setattr(zona, campo, valor)
    db.commit()
    return salida_zona(zona)


@app.delete("/api/zonas/{zona_id}", status_code=204)
def eliminar_zona(
    zona_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_admin),
):
    db.delete(obtener_zona(db, zona_id))
    db.commit()
    shutil.rmtree(UPLOADS / "zonas" / str(zona_id), ignore_errors=True)
    return Response(status_code=204)


@app.post("/api/zonas/{zona_id}/fotos")
def subir_fotos_zona(
    zona_id: int,
    fotos: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_admin),
):
    zona = obtener_zona(db, zona_id)
    for archivo in fotos:
        ruta = guardar_foto(f"zonas/{zona_id}", archivo.file)
        if ruta:
            db.add(FotoZona(zona_id=zona.id, archivo=ruta))
    db.commit()
    db.refresh(zona, attribute_names=["fotos"])
    return salida_zona(zona)


@app.delete("/api/fotos-zona/{foto_id}", status_code=204)
def borrar_foto_zona(
    foto_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_admin),
):
    foto = db.get(FotoZona, foto_id)
    if not foto:
        raise HTTPException(404, "Foto no encontrada")
    (UPLOADS / foto.archivo).unlink(missing_ok=True)
    db.delete(foto)
    db.commit()
    return Response(status_code=204)


# ---------- archivos estáticos ----------

app.mount("/uploads", StaticFiles(directory=UPLOADS), name="uploads")

# En producción, FastAPI sirve también el frontend compilado (frontend/dist).
if DIST.exists():
    app.mount("/", StaticFiles(directory=DIST, html=True), name="frontend")
