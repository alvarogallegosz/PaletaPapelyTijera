# view_caja_edicion.py
import pandas as pd
import streamlit as st
from db_connection import actualizar_movimiento_db, eliminar_movimiento_db


def render_edicion(
    df_movimientos: pd.DataFrame,
    rol_usuario: str = "operador",
    es_consolidado: bool = False,
):
  """Renderiza la vista de edición/eliminación de movimientos respetando el estado de consolidación y rol de usuario."""
  st.header("✏️ Edición y Eliminación de Movimientos")

  if df_movimientos.empty:
    st.info("No hay movimientos registrados en la base de datos.")
    return

  # --- 1. SELECCIÓN DE PERÍODO (AÑO Y MES) ---
  col_anho, col_mes = st.columns(2)

  df_temp = df_movimientos.copy()
  df_temp["fecha_dt"] = pd.to_datetime(df_temp["fecha"], errors="coerce")
  anhos_disponibles = sorted(
      df_temp["fecha_dt"].dt.year.dropna().unique().astype(int), reverse=True
  )

  if not anhos_disponibles:
    st.warning("No se encontraron fechas válidas en los registros.")
    return

  with col_anho:
    anho_sel = st.selectbox(
        "Seleccione el Año", anhos_disponibles, key="edicion_anho"
    )

  meses_nombres = [
      "Enero",
      "Febrero",
      "Marzo",
      "Abril",
      "Mayo",
      "Junio",
      "Julio",
      "Agosto",
      "Septiembre",
      "Octubre",
      "Noviembre",
      "Diciembre",
  ]

  with col_mes:
    mes_sel = st.selectbox(
        "Seleccione el Mes",
        range(1, 13),
        format_func=lambda x: meses_nombres[x - 1],
        key="edicion_mes",
    )

  # --- 2. FILTRADO DE MOVIMIENTOS ---
  mascara = (df_temp["fecha_dt"].dt.year == int(anho_sel)) & (
      df_temp["fecha_dt"].dt.month == int(mes_sel)
  )
  df_mes = df_temp[mascara].sort_values(by=["fecha", "id"]).copy()

  if df_mes.empty:
    st.info(
        f"No existen movimientos registrados en **{meses_nombres[mes_sel-1]} de"
        f" {anho_sel}**."
    )
    return

  # --- 3. VERIFICACIÓN DE MES CERRADO / CONSOLIDADO ---
  # Se verifica tanto el parámetro directo como la columna en el DataFrame
  mes_cerrado = es_consolidado
  if not mes_cerrado and "consolidado" in df_mes.columns:
    mes_cerrado = df_mes["consolidado"].fillna(False).astype(bool).any()

  if mes_cerrado:
    st.warning(
        f"🔒 **MES CERRADO / CONSOLIDADO ({meses_nombres[mes_sel-1].upper()}"
        f" {anho_sel})**\n\n"
        "No hay modificaciones posibles en este período.\n\n"
        "💡 *Si necesita modificar o borrar un registro, debe reabrir el mes"
        " previamente en la pestaña **Histórico**.*"
    )
    return

  # --- 4. VISTA DE EDICIÓN (SOLO SI EL MES ESTÁ ABIERTO) ---
  st.success(
      f"🔓 **Mes Abierto:** Mostrando {len(df_mes)} registro(s) disponible(s)"
      " para modificación."
  )
  st.markdown("---")

  for _, row in df_mes.iterrows():
    asiento_id = row.get("id")
    fecha_str = str(row.get("fecha", ""))
    concepto = str(row.get("concepto", ""))
    tipo = str(row.get("tipo", ""))
    monto = float(row.get("monto", 0.0))

    with st.expander(
        f"📌 Asiento #{asiento_id} | {fecha_str} | {tipo} | ${monto:,.2f}"
    ):
      col_info, col_acciones = st.columns([3, 1])

      with col_info:
        st.write(f"**Concepto:** {concepto}")
        st.write(f"**Tipo de Cuenta:** {tipo}")

      with col_acciones:
        if st.button(
            f"🗑️ Eliminar #{asiento_id}", key=f"btn_del_{asiento_id}"
        ):
          exito, msg = eliminar_movimiento_db(asiento_id)
          if exito:
            st.success(msg)
            st.rerun()
          else:
            st.error(msg)


# Alias de compatibilidad
render_view_caja_edicion = render_edicion
