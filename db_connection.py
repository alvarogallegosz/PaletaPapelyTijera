# db_connection.py
import pandas as pd
import streamlit as st
from supabase import create_client

# Carga segura de Secrets con captura de errores
try:
  SUPABASE_URL = st.secrets["SUPABASE_URL"]
  SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
  supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception:
  st.error(
      "⚠️ **Error de Credenciales:** No se encontraron `SUPABASE_URL` o"
      " `SUPABASE_KEY` en los Secrets de Streamlit."
  )
  supabase = None


def obtener_movimientos_locales():
  """Consulta los movimientos directamente desde Supabase en lugar del archivo CSV."""
  if not supabase:
    return pd.DataFrame()

  try:
    response = (
        supabase.table("movimientos")
        .select("*")
        .order("fecha", desc=False)
        .order("id", desc=False)
        .execute()
    )

    if response.data:
      df = pd.DataFrame(response.data)
      df["id"] = df["id"].astype(int)
      df["fecha"] = pd.to_datetime(df["fecha"]).dt.date
      df["monto"] = df["monto"].astype(float)
      df["tasa"] = df["tasa"].fillna(1.0).astype(float)
      df["activo"] = df["activo"].astype(bool)
      df["consolidado"] = df["consolidado"].astype(bool)
    else:
      df = pd.DataFrame(
          columns=[
              "id",
              "fecha",
              "categoria",
              "detalle",
              "tipo",
              "monto",
              "tasa",
              "comentarios",
              "activo",
              "consolidado",
          ]
      )

    st.session_state["df_movimientos"] = df
    return df

  except Exception as e:
    st.error(f"❌ Error al consultar la base de datos en Supabase: {e}")
    return pd.DataFrame()


def guardar_movimiento_local(nuevo_registro):
  """Guarda un nuevo registro en la tabla 'movimientos' de Supabase."""
  if not supabase:
    st.error("❌ No hay conexión con la base de datos Supabase.")
    return False

  try:
    # Si 'id' viene en el diccionario y Supabase lo genera automáticamente (Identity/Serial), lo removemos
    if "id" in nuevo_registro and (
        nuevo_registro["id"] is None or nuevo_registro["id"] == ""
    ):
      nuevo_registro.pop("id")

    supabase.table("movimientos").insert(nuevo_registro).execute()
    return True
  except Exception as e:
    st.error(f"❌ Error al guardar el movimiento en Supabase: {e}")
    return False


def actualizar_movimiento_db(id_reg, cambios_dict):
  """Actualiza un registro existente directamente en la tabla de Supabase."""
  if not supabase:
    return

  try:
    supabase.table("movimientos").update(cambios_dict).eq(
        "id", id_reg
    ).execute()
  except Exception as e:
    st.error(f"❌ Error al actualizar el registro {id_reg} en Supabase: {e}")


def actualizar_consolidado_mes_db(lista_ids, estado_consolidado, usuario):
  """Actualiza el estado de consolidación para una lista de registros en Supabase."""
  if not supabase or not lista_ids:
    return

  try:
    supabase.table("movimientos").update({
        "consolidado": estado_consolidado,
        "modificado_por": usuario,
    }).in_("id", lista_ids).execute()
  except Exception as e:
    st.error(f"❌ Error al consolidar los registros en Supabase: {e}")
