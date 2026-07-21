# db_connection.py
import calendar
import os
import pandas as pd
import streamlit as st
from supabase import create_client, Client

# ==========================================
# CONEXIÓN SEGURA A SUPABASE CON CACHE
# ==========================================

@st.cache_resource
def init_supabase() -> Client | None:
    """
    Inicializa y almacena en caché el cliente de Supabase.
    Busca credenciales primero en st.secrets (Streamlit Cloud/local secrets) 
    y luego en variables de entorno.
    """
    url = st.secrets.get("SUPABASE_URL", os.getenv("SUPABASE_URL"))
    key = st.secrets.get("SUPABASE_KEY", os.getenv("SUPABASE_KEY"))
    
    if not url or not key:
        st.error("⚠️ No se encontraron las credenciales 'SUPABASE_URL' o 'SUPABASE_KEY' en st.secrets.")
        return None

    try:
        return create_client(url, key)
    except Exception as e:
        st.error(f"Error al conectar con Supabase: {e}")
        return None

supabase = init_supabase()


# ==========================================
# 1. LECTURA Y MANEJO DE MOVIMIENTOS
# ==========================================

def obtener_movimientos_locales() -> pd.DataFrame:
    """Consulta todos los movimientos desde Supabase paginando de 1000 en 1000."""
    if not supabase:
        return pd.DataFrame()

    try:
        todos_los_datos = []
        tamanio_bloque = 1000
        inicio = 0

        while True:
            response = (
                supabase.table("movimientos")
                .select("*")
                .order("fecha", desc=False)
                .order("id", desc=False)
                .range(inicio, inicio + tamanio_bloque - 1)
                .execute()
            )
            data = response.data
            if not data:
                break

            todos_los_datos.extend(data)

            if len(data) < tamanio_bloque:
                break

            inicio += tamanio_bloque

        df = pd.DataFrame(todos_los_datos)

        # Conversión explícita de 'fecha' a tipo date
        if not df.empty and "fecha" in df.columns:
            df["fecha"] = pd.to_datetime(df["fecha"]).dt.date

        return df

    except Exception as e:
        st.error(f"Error al consultar Supabase: {e}")
        return pd.DataFrame()


def insertar_movimiento_db(nuevo_registro: dict) -> tuple[bool, str]:
    """Inserta un nuevo registro en Supabase y retorna (Éxito, Mensaje)."""
    if not supabase:
        return False, "No hay conexión activa con Supabase."

    try:
        respuesta = supabase.table("movimientos").insert(nuevo_registro).execute()
        if respuesta.data:
            id_generado = respuesta.data[0].get("id", "N/A")
            return True, f"¡Transacción registrada con éxito! (ID Asiento: {id_generado})"
        return False, "No se pudo completar el registro en la base de datos (respuesta vacía)."
    except Exception as e:
        return False, f"Error de Supabase: {str(e)}"


def actualizar_movimiento_db(id_registro: int, cambios: dict) -> tuple[bool, str]:
    """Actualiza un registro existente en Supabase."""
    if not supabase:
        return False, "No hay conexión activa con Supabase."

    try:
        respuesta = (
            supabase.table("movimientos")
            .update(cambios)
            .eq("id", id_registro)
            .execute()
        )
        if respuesta.data:
            return True, f"¡Asiento ID {id_registro} actualizado correctamente en la base de datos!"
        return False, f"No se encontró el registro ID {id_registro} para actualizar."
    except Exception as e:
        return False, f"Error al actualizar el asiento ID {id_registro}: {str(e)}"


def eliminar_movimiento_db(id_registro: int) -> tuple[bool, str]:
    """Elimina un registro en Supabase por ID."""
    if not supabase:
        return False, "No hay conexión activa con Supabase."

    try:
        respuesta = (
            supabase.table("movimientos")
            .delete()
            .eq("id", id_registro)
            .execute()
        )
        if respuesta.data:
            return True, f"¡Asiento ID {id_registro} eliminado con éxito!"
        return False, f"No se pudo eliminar el asiento ID {id_registro}."
    except Exception as e:
        return False, f"Error al eliminar asiento ID {id_registro}: {str(e)}"


# ==========================================
# 2. CONSOLIDACIÓN DE MESES E HISTÓRICO
# ==========================================

def actualizar_consolidado_mes_db(anho, mes, estado=True, **kwargs) -> tuple[bool, str]:
    """Actualiza el estado de consolidación (bloqueo) de todos los movimientos de un mes/año."""
    if not supabase:
        return False, "No hay conexión activa con Supabase."

    try:
        num_dias = calendar.monthrange(int(anho), int(mes))[1]
        fecha_inicio = f"{int(anho):04d}-{int(mes):02d}-01"
        fecha_fin = f"{int(anho):04d}-{int(mes):02d}-{num_dias:02d}"

        respuesta = (
            supabase.table("movimientos")
            .update({"consolidado": bool(estado)})
            .gte("fecha", fecha_inicio)
            .lte("fecha", fecha_fin)
            .execute()
        )

        return True, f"Consolidación actualizada correctamente para el periodo {mes}/{anho}."
    except Exception as e:
        return False, f"Error al actualizar consolidación: {str(e)}"


def obtener_historico_cierres() -> pd.DataFrame:
    """Consulta el histórico de cierres mensuales."""
    if not supabase:
        return pd.DataFrame()

    try:
        for tabla in ["cierres", "historico_cierres"]:
            try:
                response = supabase.table(tabla).select("*").execute()
                if response.data:
                    return pd.DataFrame(response.data)
            except Exception:
                continue
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def guardar_cierre_db(datos_cierre: dict) -> tuple[bool, str]:
    """Guarda un cierre mensual consolidado."""
    if not supabase:
        return False, "No hay conexión activa con Supabase."

    try:
        respuesta = supabase.table("cierres").insert(datos_cierre).execute()
        if respuesta.data:
            return True, "¡Cierre mensual guardado con éxito!"
        return False, "No se pudo registrar el cierre mensual."
    except Exception as e:
        return False, f"Error al guardar el cierre: {str(e)}"