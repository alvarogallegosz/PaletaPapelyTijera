# view_caja_historico.py
import pandas as pd
import streamlit as st

# Cuentas oficiales y sus 10 tipos exactos
CUENTAS = ["Bs", "$Ch", "$Ze", "$AhCh", "$AhZe"]
TIPOS_EXACTOS = [
    "IN-Bs",
    "EG-Bs",
    "IN-$Ch",
    "EG-$Ch",
    "IN-$Ze",
    "EG-$Ze",
    "IN-$AhCh",
    "EG-$AhCh",
    "IN-$AhZe",
    "EG-$AhZe",
]


def calcular_saldos_dinamicos(df: pd.DataFrame) -> pd.Series:
  """Calcula el saldo dinámico por cuenta considerando los prefijos IN- (suma) y EG- (resta)."""
  saldos = {cuenta: 0.0 for cuenta in CUENTAS}
  if (
      df is None
      or df.empty
      or "tipo" not in df.columns
      or "monto" not in df.columns
  ):
    return pd.Series(saldos)

  df_calc = df.copy()
  df_calc["monto"] = pd.to_numeric(df_calc["monto"], errors="coerce").fillna(
      0.0
  )

  for cuenta in CUENTAS:
    in_val = df_calc[df_calc["tipo"] == f"IN-{cuenta}"]["monto"].sum()
    eg_val = df_calc[df_calc["tipo"] == f"EG-{cuenta}"]["monto"].sum()
    saldos[cuenta] = in_val - eg_val

  return pd.Series(saldos)


def render_historico(df_movimientos: pd.DataFrame, rol_usuario: str = "operador"):
  st.subheader("📜 Histórico de Cierres y Visor de Caja")

  if df_movimientos is None or df_movimientos.empty:
    st.info("No hay registros disponibles para procesar.")
    return

  df_temp = df_movimientos.copy()

  # Conversión y preparación de fechas
  if "fecha" in df_temp.columns:
    df_temp["fecha_dt"] = pd.to_datetime(df_temp["fecha"], errors="coerce")
    df_temp["Anho"] = df_temp["fecha_dt"].dt.year
    df_temp["Mes"] = df_temp["fecha_dt"].dt.month
  else:
    st.error("El conjunto de datos no contiene la columna 'fecha'.")
    return

  # Filtros de selección
  anhos = sorted(df_temp["Anho"].dropna().unique().astype(int), reverse=True)
  if not anhos:
    st.warning("No se encontraron registros con fechas válidas.")
    return

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

  col_a, col_m, col_c = st.columns(3)
  with col_a:
    anho_sel = st.selectbox("Año", anhos, key="hist_anho_sel")
  with col_m:
    mes_sel_num = st.selectbox(
        "Mes",
        range(1, 13),
        format_func=lambda x: meses_nombres[x - 1],
        key="hist_mes_sel",
    )
  with col_c:
    cuenta_filtro = st.selectbox(
        "Cuenta / Caja", ["Todas"] + CUENTAS, key="hist_cuenta_sel"
    )

  # --- SALDOS DINÁMICOS ACUMULADOS HASTA EL PERÍODO SELECCIONADO ---
  mask_hasta_periodo = (df_temp["Anho"] < anho_sel) | (
      (df_temp["Anho"] == anho_sel) & (df_temp["Mes"] <= mes_sel_num)
  )
  df_acumulado = df_temp[mask_hasta_periodo]
  saldos_acumulados = calcular_saldos_dinamicos(df_acumulado)

  st.markdown("### 💰 Saldos Dinámicos Acumulados")
  cols_metrics = st.columns(5)
  for idx, cuenta in enumerate(CUENTAS):
    simbolo = "Bs" if cuenta == "Bs" else "$"
    val = saldos_acumulados.get(cuenta, 0.0)
    cols_metrics[idx].metric(
        label=f"Saldo {cuenta}", value=f"{simbolo} {val:,.2f}"
    )

  st.markdown("---")

  # --- FILTRADO DE MOVIMIENTOS DEL MES ---
  mask_mes = (df_temp["Anho"] == anho_sel) & (df_temp["Mes"] == mes_sel_num)
  df_mes = df_temp[mask_mes].copy()

  if cuenta_filtro != "Todas":
    tipos_permitidos = [f"IN-{cuenta_filtro}", f"EG-{cuenta_filtro}"]
    df_mes = df_mes[df_mes["tipo"].isin(tipos_permitidos)]

  mes_nombre = meses_nombres[mes_sel_num - 1]
  st.markdown(f"### Detalle del Período: **{mes_nombre} {anho_sel}**")

  if df_mes.empty:
    st.info(
        f"No hay movimientos registrados para el filtro seleccionado en"
        f" {mes_nombre} {anho_sel}."
    )
    return

  # Control del estado de consolidación
  consolidado_actual = False
  if "consolidado" in df_mes.columns:
    consolidado_actual = df_mes["consolidado"].fillna(False).astype(bool).any()

  if consolidado_actual:
    st.success(
        f"🔒 El mes de **{mes_nombre} {anho_sel}** se encuentra **CERRADO**."
    )
  else:
    st.warning(
        f"🔓 El mes de **{mes_nombre} {anho_sel}** se encuentra **ABIERTO**."
    )

  if rol_usuario in ["admin", "administrador", "Gerente"]:
    col_b1, col_b2 = st.columns(2)
    with col_b1:
      if not consolidado_actual and st.button(
          f"🔒 Cerrar / Consolidar {mes_nombre}", key="btn_cerrar"
      ):
        st.info("Acción de consolidación activada.")
    with col_b2:
      if consolidado_actual and st.button(
          f"🔓 Reabrir {mes_nombre}", key="btn_reabrir"
      ):
        st.info("Acción de re-apertura activada.")

  # --- SALDO CORRIDO Y TABLA DE DATOS ---
  if "monto" in df_mes.columns and "tipo" in df_mes.columns:
    df_mes["monto_neto"] = df_mes.apply(
        lambda r: (
            r["monto"]
            if str(r.get("tipo", "")).startswith("IN-")
            else -r["monto"]
        ),
        axis=1,
    )
    df_mes["saldo_corrido"] = df_mes["monto_neto"].cumsum()

  columnas_deseadas = [
      "id",
      "fecha",
      "concepto",
      "categoria",
      "tipo",
      "monto",
      "saldo_corrido",
      "consolidado",
  ]
  columnas_visibles = [c for c in columnas_deseadas if c in df_mes.columns]

  st.dataframe(
      df_mes[columnas_visibles]
      .sort_values(by=["fecha"])
      .style.format({
          "monto": "{:,.2f}",
          "saldo_corrido": "{:,.2f}",
      }),
      use_container_width=True,
      hide_index=True,
  )


# Aliases de compatibilidad de importación
render_view_caja_historico = render_historico
render_caja_historico = render_historico
