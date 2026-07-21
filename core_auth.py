# core_auth.py
import hashlib
import secrets
import smtplib
import string
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import streamlit as st

# Roles permitidos en la aplicación
ROLES_PERMITIDOS = ["operador", "administrador", "contador", "gerente", "soporte"]


def calcular_hash_256(password: str) -> str:
    """Encripta la contraseña utilizando el algoritmo SHA-256."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def generar_codigo_temporal(longitud: int = 6) -> str:
    """
    Genera un código alfanumérico seguro para verificación o recuperación
    utilizando el módulo 'secrets' de Python.
    """
    caracteres = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(caracteres) for _ in range(longitud))


def enviar_correo_simulado(email: str, asunto: str, codigo: str) -> tuple[bool, str]:
    """
    Envía correos mediante el servidor SMTP de Gmail utilizando credenciales de st.secrets.
    Si las credenciales no están disponibles, ejecuta una simulación limpia en consola.
    
    Retorna:
        tuple[bool, str]: (Estado de éxito, Mensaje informativo)
    """
    # Intentar obtener credenciales de los secretos de Streamlit
    remitente = st.secrets.get("GMAIL_USER", "paletapapelytijera@gmail.com")
    password_smtp = st.secrets.get("GMAIL_PASSWORD")

    if not password_smtp:
        # Fallback de respaldo para desarrollo local si no hay contraseña configurada
        print("\n--- [MODO SIMULACIÓN - FALTAN CREDENCIALES] ---")
        print(f"DESTINATARIO: {email}")
        print(f"ASUNTO: {asunto}")
        print(f"CÓDIGO DE SEGURIDAD: {codigo}")
        print("-----------------------------------------------\n")
        return True, "Modo simulación: Código impreso en la consola del servidor."

    servidor_smtp = "smtp.gmail.com"
    puerto = 587

    mensaje = MIMEMultipart()
    mensaje["From"] = remitente
    mensaje["To"] = email
    mensaje["Subject"] = asunto

    cuerpo = f"""
Hola,

Has solicitado un código de verificación o recuperación para el sistema.

Tu código de seguridad es: {codigo}

Este código es estrictamente temporal y confidencial. Si no solicitaste esta acción, puedes ignorar este mensaje.
"""
    mensaje.attach(MIMEText(cuerpo, "plain"))

    try:
        with smtplib.SMTP(servidor_smtp, puerto) as server:
            server.starttls()
            server.login(remitente, password_smtp)
            server.sendmail(remitente, email, mensaje.as_string())
        
        return True, f"Correo enviado exitosamente a {email}."
    except Exception as e:
        msg_error = f"Error crítico al enviar el correo SMTP: {str(e)}"
        print(msg_error)
        return False, msg_error