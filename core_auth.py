# core_auth.py
import hashlib
import random
import string

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
    Simulación de envío de correo. Aquí conectarás tu servicio SMTP o Supabase Edge Function.
    Para pruebas locales, imprimirá el código en la consola de Streamlit.
    """
    print(f"--- ENVIANDO CORREO A {email} ---")
    print(f"Asunto: {asunto}")
    print(f"Código Seguro: {codigo}")
    print("---------------------------------")