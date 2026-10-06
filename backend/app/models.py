from datetime import date, datetime

from sqlalchemy import (
    BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TipoPropiedad(Base):
    """Catálogo: Apartamento, Casa, Lote, Local comercial..."""

    __tablename__ = "tipos_propiedad"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(50), unique=True)

    propiedades: Mapped[list["Propiedad"]] = relationship(back_populates="tipo")


class Propiedad(Base):
    __tablename__ = "propiedades"

    id: Mapped[int] = mapped_column(primary_key=True)
    tipo_id: Mapped[int] = mapped_column(ForeignKey("tipos_propiedad.id"))
    # Apartamento del conjunto al que corresponde el aviso y cuenta que lo creó
    apartamento_id: Mapped[int | None] = mapped_column(
        ForeignKey("apartamentos_conjunto.id", ondelete="SET NULL"), nullable=True
    )
    usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )

    titulo: Mapped[str] = mapped_column(String(200))
    negocio: Mapped[str] = mapped_column(String(20), default="venta")  # venta | arriendo
    amoblado: Mapped[bool] = mapped_column(Boolean, default=False)  # solo aplica a arriendos
    precio: Mapped[int] = mapped_column(BigInteger)
    administracion: Mapped[int | None] = mapped_column(BigInteger, nullable=True)  # cuota mensual

    # Copia de las características del apartamento (se actualizan solas al guardar el apartamento)
    area_construida_m2: Mapped[float | None] = mapped_column(Float, nullable=True)
    area_lote_m2: Mapped[float | None] = mapped_column(Float, nullable=True)
    habitaciones: Mapped[int] = mapped_column(Integer, default=0)
    banos: Mapped[int] = mapped_column(Integer, default=0)
    parqueaderos: Mapped[int] = mapped_column(Integer, default=0)
    pisos: Mapped[int] = mapped_column(Integer, default=1)  # cantidad de pisos de la propiedad
    piso: Mapped[int | None] = mapped_column(Integer, nullable=True)  # piso en el que queda (apartamentos)
    anio_construccion: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estrato: Mapped[int | None] = mapped_column(Integer, nullable=True)

    ciudad: Mapped[str] = mapped_column(String(100))
    barrio: Mapped[str] = mapped_column(String(100), default="")
    direccion: Mapped[str] = mapped_column(String(255))
    descripcion: Mapped[str] = mapped_column(Text, default="")
    video_youtube: Mapped[str] = mapped_column(String(20), default="")  # id del video, ej. "dQw4w9WgXcQ"
    telefonos: Mapped[str] = mapped_column(String(255), default="")  # teléfonos de contacto, separados por coma
    duracion_visita: Mapped[int] = mapped_column(Integer, default=30)  # minutos de cada visita
    estado: Mapped[str] = mapped_column(String(20), default="borrador")
    creado: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    tipo: Mapped[TipoPropiedad] = relationship(back_populates="propiedades", lazy="joined")
    apartamento: Mapped["Apartamento | None"] = relationship(lazy="joined")
    fotos: Mapped[list["Foto"]] = relationship(
        back_populates="propiedad",
        cascade="all, delete-orphan",
        order_by="Foto.id",
    )
    disponibilidad: Mapped[list["DisponibilidadVisita"]] = relationship(
        cascade="all, delete-orphan",
        order_by="[DisponibilidadVisita.dia, DisponibilidadVisita.inicio]",
    )
    visitas: Mapped[list["Visita"]] = relationship(
        back_populates="propiedad",
        cascade="all, delete-orphan",
        order_by="[Visita.fecha, Visita.hora]",
    )


class Foto(Base):
    __tablename__ = "fotos"

    id: Mapped[int] = mapped_column(primary_key=True)
    propiedad_id: Mapped[int] = mapped_column(ForeignKey("propiedades.id"))
    archivo: Mapped[str] = mapped_column(String(255))  # ruta relativa dentro de uploads/
    principal: Mapped[bool] = mapped_column(Boolean, default=False)  # portada del aviso

    propiedad: Mapped[Propiedad] = relationship(back_populates="fotos")


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    telefono: Mapped[str] = mapped_column(String(30), default="")
    clave_hash: Mapped[str] = mapped_column(String(255))  # scrypt$sal$hash, nunca la clave en texto
    # Con esta identificación se reconoce como propietario o arrendatario de un apartamento.
    identificacion: Mapped[str] = mapped_column(String(30), default="")
    # Perfil de staff asignado por el super admin: "admin" o vacío. El super admin se define en .env.
    rol: Mapped[str] = mapped_column(String(20), default="")
    # La administración confirma que la cuenta es de quien dice ser antes de darle perfil de residente.
    verificado: Mapped[bool] = mapped_column(Boolean, default=False)
    creado: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Noticia(Base):
    """Entradas del blog de noticias del conjunto."""

    __tablename__ = "noticias"

    id: Mapped[int] = mapped_column(primary_key=True)
    titulo: Mapped[str] = mapped_column(String(200))
    resumen: Mapped[str] = mapped_column(String(300), default="")
    contenido: Mapped[str] = mapped_column(Text, default="")
    imagen: Mapped[str | None] = mapped_column(String(255), nullable=True)  # ruta dentro de uploads/
    publicada: Mapped[bool] = mapped_column(Boolean, default=False)
    creado: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Apartamento(Base):
    """Unidad del conjunto. Tiene uno o más propietarios y puede tener arrendatarios."""

    __tablename__ = "apartamentos_conjunto"
    __table_args__ = (UniqueConstraint("torre", "numero"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    torre: Mapped[str] = mapped_column(String(20), default="")  # el edificio tiene una sola torre: queda vacío
    numero: Mapped[str] = mapped_column(String(20))  # ej. "502"
    piso: Mapped[int | None] = mapped_column(Integer, nullable=True)
    area_m2: Mapped[float | None] = mapped_column(Float, nullable=True)
    habitaciones: Mapped[int] = mapped_column(Integer, default=0)
    banos: Mapped[int] = mapped_column(Integer, default=0)
    parqueaderos: Mapped[int] = mapped_column(Integer, default=0)
    # Coeficiente de copropiedad en porcentaje (ej. 0.8523); entre todos suman 100
    coeficiente: Mapped[float | None] = mapped_column(Float, nullable=True)
    # En mora con la administración: no puede participar en sorteos
    deudor: Mapped[bool] = mapped_column(Boolean, default=False)
    creado: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    personas: Mapped[list["PersonaApartamento"]] = relationship(
        back_populates="apartamento",
        cascade="all, delete-orphan",
        order_by="PersonaApartamento.id",
    )


class PersonaApartamento(Base):
    """Propietario o arrendatario de un apartamento. Se inactiva cuando deja de serlo."""

    __tablename__ = "personas_apartamento"

    id: Mapped[int] = mapped_column(primary_key=True)
    apartamento_id: Mapped[int] = mapped_column(ForeignKey("apartamentos_conjunto.id"))
    rol: Mapped[str] = mapped_column(String(20))  # propietario | arrendatario
    nombre: Mapped[str] = mapped_column(String(150))
    identificacion: Mapped[str] = mapped_column(String(30))  # cédula, NIT, pasaporte...
    telefono: Mapped[str] = mapped_column(String(30), default="")
    email: Mapped[str] = mapped_column(String(255), default="")
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    creado: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    apartamento: Mapped[Apartamento] = relationship(back_populates="personas")


class ZonaComun(Base):
    """Zona común del conjunto (gimnasio, terrazas...) con su descripción y fotos."""

    __tablename__ = "zonas_comunes"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(60), unique=True)  # para la URL: /zonas/gimnasio
    nombre: Mapped[str] = mapped_column(String(100))
    icono: Mapped[str] = mapped_column(String(30), default="")  # clave de ícono del frontend
    resumen: Mapped[str] = mapped_column(String(300), default="")
    descripcion: Mapped[str] = mapped_column(Text, default="")
    horario: Mapped[str] = mapped_column(String(200), default="")
    orden: Mapped[int] = mapped_column(Integer, default=0)

    fotos: Mapped[list["FotoZona"]] = relationship(
        back_populates="zona",
        cascade="all, delete-orphan",
        order_by="FotoZona.id",
    )


class FotoZona(Base):
    __tablename__ = "fotos_zona"

    id: Mapped[int] = mapped_column(primary_key=True)
    zona_id: Mapped[int] = mapped_column(ForeignKey("zonas_comunes.id"))
    archivo: Mapped[str] = mapped_column(String(255))  # ruta relativa dentro de uploads/

    zona: Mapped[ZonaComun] = relationship(back_populates="fotos")


class DisponibilidadVisita(Base):
    """Franja semanal en la que se puede visitar el apartamento del aviso."""

    __tablename__ = "disponibilidad_visitas"

    id: Mapped[int] = mapped_column(primary_key=True)
    propiedad_id: Mapped[int] = mapped_column(ForeignKey("propiedades.id"))
    dia: Mapped[int] = mapped_column(Integer)  # 0 = lunes ... 6 = domingo
    inicio: Mapped[str] = mapped_column(String(5))  # "09:00"
    fin: Mapped[str] = mapped_column(String(5))  # "12:00"


class Visita(Base):
    """Visita agendada por una persona interesada en el aviso."""

    __tablename__ = "visitas"

    id: Mapped[int] = mapped_column(primary_key=True)
    propiedad_id: Mapped[int] = mapped_column(ForeignKey("propiedades.id"))
    fecha: Mapped[date] = mapped_column()
    hora: Mapped[str] = mapped_column(String(5))  # "10:30"
    nombre: Mapped[str] = mapped_column(String(100))
    telefono: Mapped[str] = mapped_column(String(30))
    email: Mapped[str] = mapped_column(String(255), default="")
    mensaje: Mapped[str] = mapped_column(Text, default="")
    estado: Mapped[str] = mapped_column(String(20), default="pendiente")  # pendiente | confirmada | cancelada
    creado: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    propiedad: Mapped[Propiedad] = relationship(back_populates="visitas")


class Parqueadero(Base):
    """Parqueadero del edificio: de carro o moto, para residentes o visitantes.

    Los de residentes se pueden asignar a un apartamento (uno puede tener varios)."""

    __tablename__ = "parqueaderos"

    id: Mapped[int] = mapped_column(primary_key=True)
    numero: Mapped[str] = mapped_column(String(20), unique=True)  # ej. "P-12", "M-03"
    tipo: Mapped[str] = mapped_column(String(10), default="carro")  # carro | moto
    uso: Mapped[str] = mapped_column(String(12), default="residente")  # residente | visitante
    ubicacion: Mapped[str] = mapped_column(String(60), default="")  # ej. "Sótano 1"
    observaciones: Mapped[str] = mapped_column(String(255), default="")
    apartamento_id: Mapped[int | None] = mapped_column(
        ForeignKey("apartamentos_conjunto.id", ondelete="SET NULL"), nullable=True
    )
    # Periodo de la asignación (por sorteo: X meses). Sin "hasta" = sin vencimiento.
    asignado_desde: Mapped[date | None] = mapped_column(nullable=True)
    asignado_hasta: Mapped[date | None] = mapped_column(nullable=True)

    apartamento: Mapped["Apartamento | None"] = relationship(lazy="joined")


class Sorteo(Base):
    """Sorteo de parqueaderos de residentes entre los apartamentos que se postulan."""

    __tablename__ = "sorteos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))
    tipo: Mapped[str] = mapped_column(String(10), default="carro")  # carro | moto
    meses: Mapped[int] = mapped_column(Integer, default=6)  # duración de la asignación
    inicio: Mapped[date] = mapped_column()  # desde cuándo rige la asignación
    cierre: Mapped[date] = mapped_column()  # último día para postularse
    estado: Mapped[str] = mapped_column(String(15), default="abierto")  # abierto | realizado
    semilla: Mapped[str] = mapped_column(String(32), default="")  # constancia del azar
    realizado_en: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    creado: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    parqueaderos: Mapped[list["Parqueadero"]] = relationship(secondary="sorteo_parqueaderos")
    postulaciones: Mapped[list["Postulacion"]] = relationship(
        back_populates="sorteo", cascade="all, delete-orphan", order_by="Postulacion.id"
    )


class SorteoParqueadero(Base):
    """Parqueaderos que entran en un sorteo."""

    __tablename__ = "sorteo_parqueaderos"

    sorteo_id: Mapped[int] = mapped_column(ForeignKey("sorteos.id", ondelete="CASCADE"), primary_key=True)
    parqueadero_id: Mapped[int] = mapped_column(ForeignKey("parqueaderos.id", ondelete="CASCADE"), primary_key=True)


class Postulacion(Base):
    """Un apartamento inscrito en un sorteo (máximo una vez por sorteo)."""

    __tablename__ = "postulaciones"
    __table_args__ = (UniqueConstraint("sorteo_id", "apartamento_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    sorteo_id: Mapped[int] = mapped_column(ForeignKey("sorteos.id"))
    apartamento_id: Mapped[int] = mapped_column(ForeignKey("apartamentos_conjunto.id", ondelete="CASCADE"))
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    posicion: Mapped[int | None] = mapped_column(Integer, nullable=True)  # orden que salió en el sorteo
    excluido: Mapped[bool] = mapped_column(Boolean, default=False)  # era deudor al momento del sorteo
    parqueadero_id: Mapped[int | None] = mapped_column(
        ForeignKey("parqueaderos.id", ondelete="SET NULL"), nullable=True
    )  # el que le correspondió (vacío = lista de espera)
    creado: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    sorteo: Mapped[Sorteo] = relationship(back_populates="postulaciones")
    apartamento: Mapped["Apartamento"] = relationship(lazy="joined")
    parqueadero: Mapped["Parqueadero | None"] = relationship(lazy="joined")
