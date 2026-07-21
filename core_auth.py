# core_auth.py
import hashlib
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st

ROLES_PERMITIDOS = ["operador", "administrador", "contador", "gerente", "soporte"]

def calcular_hash_256(password: str) -> str:
    """Encripta la contraseña usando SHA-256."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def generar_codigo_temporal(longitud=6) -> str:
    """Genera un código alfanumérico para verificación o recuperación."""
    caracteres = string.ascii_uppercase + string.digits
    return ''.join(random.choice(caracteres) for _ in range(longitud))

def enviar_correo_simulado(email: str, asunto: str, codigo: str):
    """
    Envía correos reales mediante SMTP de Gmail utilizando credenciales seguras de st.secrets.
    Si las credenciales no están configuradas, realiza un respaldo impreso en consola.
    """
    remitente = "alvarogallegosz@gmail.com"
    
    # Obtener la contraseña de aplicación de forma segura desde los secretos de Streamlit
    try:
        password_smtp = st.secrets["GMAIL_PASSWORD"]
    except Exception:
        password_smtp = None

    if not password_smtp:
        # Fallback de respaldo para desarrollo local si el secreto no está definido
        print(f"--- [MODO SIMULACIÓN - FALTAN CREDENCIALES] ---")
        print(f"ENVIANDO CORREO A {email}")
        print(f"Asunto: {asunto}")
        print(f"Código Seguro: {codigo}")
        print("-----------------------------------------------")
        return

    # Configuración del servidor SMTP de Gmail
    servidor_smtp = "smtp.gmail.com"
    puerto = 587

    mensaje = MIMEMultipart()
    mensaje["From"] = remitente
    mensaje["To"] = email
    mensaje["Subject"] = asunto

    cuerpo = f"""
    Hola,

    Has solicitado un código de verificación o recuperación para el sistema de la Estructura Administrativa.

    Tu código de seguridad es: {codigo}

    Este código es estrictamente temporal. Si no solicitaste esta acción, puedes ignorar este mensaje.
    """
    mensaje.attach(MIMEText(cuerpo, "plain"))

    try:
        with smtplib.SMTP(servidor_smtp, puerto) as server:
            server.starttls()
            server.login(remitente, password_smtp)
            server.sendmail(remitente, email, mensaje.as_string())
        print(f"Correo enviado exitosamente a {email} desde {remitente}")
    except Exception as e:
        print(f"Error crítico al enviar el correo SMTP: {e}")
        raise e
