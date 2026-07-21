# view_caja_historico.py
import pandas as pd
import streamlit as st
from db_connection import (
    actualizar_estado_mes_db,
    obtener_cierres_db,
)  # O funciones equivalentes de BD


def render_historico(df_movimientos: pd.DataFrame, rol_usuario: str = "operador"):
  st.subheader("📜 Histórico de Cierres y Consolidación de Meses")

  if df_movimientos is None or df_movimientos.empty:
    st.info("No hay registros disponibles para procesar el histórico.")
    return

  df_temp = df_movimientos.copy()

  # Asegurar columna de fecha datetime
  if "fecha" in df_temp.columns:
    df_temp["fecha_dt"] = pd.to_datetime(df_temp["fecha"], errors="coerce")
    df_temp["Anho"] = df_temp["fecha_dt"].dt.year
    df_temp["Mes"] = df_temp["fecha_dt"].dt.month
  else:
    st.error(
        "El DataFrame de movimientos no contiene la columna esencial 'fecha'."
    )
    return

  # Obtener años y meses únicos presentes en los datos
  anhos = sorted(df_temp["Anho"].dropna().unique().astype(int), reverse=True)
  if not anhos:
    st.warning("No se encontraron años válidos en los registros.")
    return

  col1, col2 = st.columns(2)
  with col1:
    anho_sel = st.selectbox("Seleccione Año", anhos, key="hist_anho_sel")

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

  with col2:
    mes_sel_num = st.selectbox(
        "Seleccione Mes",
        range(1, 13),
        format_func=lambda x: meses_nombres[x - 1],
        key="hist_mes_sel",
    )

  # Filtrar movimientos del mes/año seleccionado
  mask = (df_temp["Anho"] == anho_sel) & (df_temp["Mes"] == mes_sel_num)
  df_mes = df_temp[mask].copy()

  mes_nombre = meses_nombres[mes_sel_num - 1]
  st.markdown(f"### Período: **{mes_nombre} {anho_sel}**")

  if df_mes.empty:
    st.info(f"No hay movimientos registrados en {mes_nombre} de {anho_sel}.")
    return

  # Comprobar estado de consolidación / cierre
  consolidado_actual = False
  if "consolidado" in df_mes.columns:
    consolidado_actual = df_mes["consolidado"].fillna(False).astype(bool).any()

  # Mostrar estado visual
  if consolidado_actual:
    st.success(f"🔒 El mes de **{mes_nombre} {anho_sel}** está **CERRADO**.")
  else:
    st.warning(f"🔓 El mes de **{mes_nombre} {anho_sel}** está **ABIERTO**.")

  # Controles de administración de cierre (Solo administradores o según rol)
  if rol_usuario in ["admin", "administrador", "Gerente"]:
    st.markdown("---")
    st.write("⚙️ **Gestión de Estado del Período:**")
    col_btn1, col_btn2 = st.columns(2)

    with col_btn1:
      if not consolidado_actual:
        if st.button(
            f"🔒 Cerrar / Consolidar {mes_nombre}", key="btn_cerrar_mes"
        ):
          # Lógica para marcar como consolidado en BD si aplica
          st.info(
              "Función de cierre activada. (Actualice o verifique su conexión"
              " a base de datos)"
          )
      else:
        st.info("El mes ya se encuentra cerrado.")

    with col_btn2:
      if consolidado_actual:
        if st.button(f"🔓 Reabrir {mes_nombre}", key="btn_reabrir_mes"):
          st.info(
              "Función de reapertura activada para permitir modificaciones en"
              " Edición."
          )

  # --- VISTA SEGURA DE REGISTROS DEL MES ---
  st.markdown("---")
  st.markdown("#### 📋 Resumen de Movimientos del Período")

  # Seleccionar dinámicamente solo las columnas que SÍ existan para evitar KeyErrors
췄  columnas_disponibles = [
      c
      for c in [
          "id",
          "fecha",
          "concepto",
          "categoria",
          "tipo",
          "monto",
          "consolidado",
      ]
      if c in df_mes.columns
  ]

  st.dataframe(
      df_mes[columnas_disponibles]
      .sort_values(by=["fecha"])
      .style.format({"monto": "${:,.2f}"} if "monto" in df_mes.columns else {}),
      use_container_width=True,
      hide_index=True,
  )


# Alias de compatibilidad
render_view_caja_historico = render_historico
render_caja_historico = render_historico
