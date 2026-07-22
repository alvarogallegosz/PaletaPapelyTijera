# db_connection.py
import calendar
import pandas as pd
import streamlit as st
from supabase import create_client

SUPABASE_URL = "https://nkesjmkdyueehfdomesy.supabase.co"
SUPABASE_KEY = "sb_publishable_s9sytr-JOPZBYPSZ4mD_4A_tdkLVIOp"

try:
  supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
  supabase = None


# ==========================================
# 1. LECTURA Y MANEJO DE MOVIMIENTOS
# ==========================================


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

    df = pd.DataFrame(todos_los_datos)

    # Conversión explícita de 'fecha' a tipo date para evitar el TypeError
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


# ==========================================
# 2. CONSOLIDACIÓN DE MESES E HISTÓRICO
# ==========================================


def actualizar_consolidado_mes_db(anho, mes, estado=True, **kwargs):
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

    return (
        True,
        f"Consolidación actualizada correctamente para el periodo"
        f" {mes}/{anho}.",
    )
  except Exception as e:
    return False, f"Error al actualizar consolidación: {str(e)}"


def obtener_historico_cierres():
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
  except Exception as e:
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

# ==========================================
# 3. MANEJO DE PRESUPUESTOS EN SUPABASE
# ==========================================

def guardar_presupuesto_db(datos_presupuesto: dict, id_presupuesto: int = None) -> tuple[bool, str]:
    """Inserta o actualiza un presupuesto en Supabase."""
    if not supabase:
        return False, "No hay conexión activa con Supabase."

    try:
        if id_presupuesto:
            datos_presupuesto["updated_at"] = "now()"
            respuesta = supabase.table("presupuestos").update(datos_presupuesto).eq("id", id_presupuesto).execute()
            if respuesta.data:
                return True, f"¡Presupuesto #{id_presupuesto} actualizado con éxito!"
            return False, f"No se encontró el presupuesto #{id_presupuesto} para actualizar."
        else:
            respuesta = supabase.table("presupuestos").insert(datos_presupuesto).execute()
            if respuesta.data:
                nuevo_id = respuesta.data[0].get("id", "N/A")
                return True, f"¡Presupuesto guardado exitosamente con el ID #{nuevo_id}!"
            return False, "Respuesta vacía al insertar presupuesto."
    except Exception as e:
        return False, f"Error en Supabase: {str(e)}"


def obtener_presupuestos_db(incluir_inactivos: bool = False, tipo_filtro: str = None) -> pd.DataFrame:
    """Consulta los presupuestos guardados en la BD."""
    if not supabase:
        return pd.DataFrame()

    try:
        query = supabase.table("presupuestos").select("*")
        if not incluir_inactivos:
            query = query.eq("activo", True)
        if tipo_filtro and tipo_filtro != "Todos":
            query = query.eq("tipo_presupuesto", tipo_filtro)
            
        response = query.order("created_at", desc=True).execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as e:
        st.error(f"Error al consultar presupuestos: {e}")
        return pd.DataFrame()


def obtener_presupuesto_por_id_db(id_presupuesto: int) -> dict:
    """Recupera un presupuesto específico para su rehidratación."""
    if not supabase:
        return {}

    try:
        response = supabase.table("presupuestos").select("*").eq("id", id_presupuesto).execute()
        return response.data[0] if response.data else {}
    except Exception as e:
        st.error(f"Error al recuperar presupuesto #{id_presupuesto}: {e}")
        return {}


def cambiar_estado_presupuesto_db(id_presupuesto: int, nuevo_estado: str, usuario: str) -> tuple[bool, str]:
    """Cambia el estado del presupuesto ('Borrador', 'Aprobado', 'Rechazado')."""
    if not supabase:
        return False, "No hay conexión activa con Supabase."

    try:
        payload = {"estado": nuevo_estado, "modificado_por": usuario, "updated_at": "now()"}
        respuesta = supabase.table("presupuestos").update(payload).eq("id", id_presupuesto).execute()
        return (True, f"Presupuesto #{id_presupuesto} marcado como {nuevo_estado}.") if respuesta.data else (False, "Registro no encontrado.")
    except Exception as e:
        return False, f"Error al cambiar estado: {str(e)}"


def anular_presupuesto_db(id_presupuesto: int, usuario: str) -> tuple[bool, str]:
    """Aplica Soft Delete al presupuesto."""
    if not supabase:
        return False, "No hay conexión activa con Supabase."

    try:
        payload = {"activo": False, "modificado_por": usuario, "updated_at": "now()"}
        respuesta = supabase.table("presupuestos").update(payload).eq("id", id_presupuesto).execute()
        return (True, f"Presupuesto #{id_presupuesto} anulado con éxito.") if respuesta.data else (False, "Error al anular.")
    except Exception as e:
        return False, f"Error de anulación: {str(e)}"
