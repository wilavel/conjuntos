"""Envío de correos por SMTP (configurable en .env).

Sin SMTP_HOST no se envía nada: el mensaje se escribe en el log y quien llama
decide qué hacer (por ejemplo, mostrar el enlace a la administración).
"""
import logging
import os
import smtplib
from email.message import EmailMessage

log = logging.getLogger("correo")

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT") or 587)
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "") or SMTP_USER


def configurado() -> bool:
    return bool(SMTP_HOST and SMTP_FROM)


def enviar(destino: str, asunto: str, texto: str, html: str | None = None) -> bool:
    """Devuelve True si el correo salió; False si no hay SMTP o falló el envío."""
    if not configurado():
        log.warning("SMTP sin configurar; no se envió el correo a %s (%s)", destino, asunto)
        return False
    msg = EmailMessage()
    msg["Subject"] = asunto
    msg["From"] = SMTP_FROM
    msg["To"] = destino
    msg.set_content(texto)
    if html:
        msg.add_alternative(html, subtype="html")
    try:
        if SMTP_PORT == 465:
            servidor = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=15)
        else:
            servidor = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15)
            servidor.starttls()
        with servidor:
            if SMTP_USER:
                servidor.login(SMTP_USER, SMTP_PASSWORD)
            servidor.send_message(msg)
        return True
    except (smtplib.SMTPException, OSError):
        log.exception("No se pudo enviar el correo a %s", destino)
        return False
