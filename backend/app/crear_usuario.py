"""Crea una cuenta (o le cambia la contraseña) desde la terminal.

Sirve para la primera cuenta de super admin, ya que en la página solo la
administración puede crear cuentas:

    python -m app.crear_usuario

El correo debe estar también en SUPERADMIN_EMAILS (.env) para tener ese perfil.
"""
from getpass import getpass

from sqlalchemy import select

from .db import SessionLocal
from .main import SUPERADMIN_EMAILS, hash_clave, normalizar_identificacion
from .models import Usuario


def pedir(texto: str, obligatorio: bool = True) -> str:
    while True:
        valor = input(texto).strip()
        if valor or not obligatorio:
            return valor
        print("  Este dato es obligatorio.")


def pedir_clave() -> str:
    while True:
        clave = getpass("Contraseña (mínimo 8 caracteres): ")
        if len(clave) < 8:
            print("  Muy corta.")
        elif clave != getpass("Repite la contraseña: "):
            print("  No coinciden.")
        else:
            return clave


def main() -> None:
    email = pedir("Correo: ").lower()
    with SessionLocal() as s:
        usuario = s.scalars(select(Usuario).where(Usuario.email == email)).first()
        if usuario:
            print(f"Ya existe la cuenta de {usuario.nombre}; se le asignará una contraseña nueva.")
            usuario.clave_hash = hash_clave(pedir_clave())
        else:
            usuario = Usuario(
                email=email,
                nombre=pedir("Nombre: "),
                identificacion=normalizar_identificacion(pedir("Identificación: ")),
                telefono=pedir("Teléfono (opcional): ", obligatorio=False),
                clave_hash=hash_clave(pedir_clave()),
                verificado=True,
            )
            s.add(usuario)
        s.commit()
    print("Listo.")
    if email in SUPERADMIN_EMAILS:
        print("Este correo es super admin: entra por la zona privada y verás el botón Administrar.")
    else:
        print(
            "Ojo: este correo NO está en SUPERADMIN_EMAILS. Para que sea super admin, agrégalo "
            "en backend/.env y reinicia el backend."
        )


if __name__ == "__main__":
    main()
