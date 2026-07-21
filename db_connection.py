# db_connection.py
import pandas as pd
import streamlit as st
from supabase import create_client

SUPABASE_URL = "https://nkesjmkdyueehfdomesy.supabase.co"
SUPABASE_KEY = "sb_publishable_s9sytr-JOPZBYPSZ4mD_4A_tdkLVIOp"

try:
  supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
  supabase = None


def obtener_movimientos_locales():
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

    return pd.DataFrame(todos_los_datos)

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
    return (
        False,
        "No se pudo completar el registro en la base de datos (respuesta"
        " vacía).",
    )
  except Exception as e:
    return False, f"Error de Supabase: {str(e)}"


def actualizar_movimiento_db(
    id_registro: int, cambios: dict
) -> tuple[bool, str]:
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
      return (
          True,
          f"¡Asiento ID {id_registro} actualizado correctamente en la base de"
          " datos!",
      )
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