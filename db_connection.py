# db_connection.py
import pandas as pd
import streamlit as st
from supabase import create_client

# Conexión utilizando los Secrets de Streamlit
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def obtener_movimientos_locales():
  """Consulta los movimientos directamente desde Supabase en lugar del archivo CSV."""
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

      # Asegurar tipos de datos correctos
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
    st.error(f"❌ Error al conectar con Supabase: {e}")
    return pd.DataFrame()


def actualizar_movimiento_db(id_reg, cambios_dict):
  """Actualiza un registro existente directamente en la tabla de Supabase."""
  try:
    supabase.table("movimientos").update(cambios_dict).eq(
        "id", id_reg
    ).execute()
  except Exception as e:
    st.error(f"❌ Error al actualizar el registro {id_reg} en Supabase: {e}")


def actualizar_consolidado_mes_db(lista_ids, estado_consolidado, usuario):
  """Actualiza el estado de consolidación para una lista de registros en Supabase."""
  if not lista_ids:
    return
  try:
    supabase.table("movimientos").update({
        "consolidado": estado_consolidado,
        "modificado_por": usuario,
    }).in_("id", lista_ids).execute()
  except Exception as e:
    st.error(f"❌ Error al consolidar los registros en Supabase: {e}")
