from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Integer, String, Text, func
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

    titulo: Mapped[str] = mapped_column(String(200))
    precio: Mapped[int] = mapped_column(BigInteger)
    administracion: Mapped[int | None] = mapped_column(BigInteger, nullable=True)  # cuota mensual

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
    estado: Mapped[str] = mapped_column(String(20), default="borrador")
    creado: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    tipo: Mapped[TipoPropiedad] = relationship(back_populates="propiedades", lazy="joined")
    fotos: Mapped[list["Foto"]] = relationship(
        back_populates="propiedad",
        cascade="all, delete-orphan",
        order_by="Foto.id",
    )


class Foto(Base):
    __tablename__ = "fotos"

    id: Mapped[int] = mapped_column(primary_key=True)
    propiedad_id: Mapped[int] = mapped_column(ForeignKey("propiedades.id"))
    archivo: Mapped[str] = mapped_column(String(255))  # ruta relativa dentro de uploads/

    propiedad: Mapped[Propiedad] = relationship(back_populates="fotos")


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    telefono: Mapped[str] = mapped_column(String(30), default="")
    clave_hash: Mapped[str] = mapped_column(String(255))  # scrypt$sal$hash, nunca la clave en texto
    creado: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
