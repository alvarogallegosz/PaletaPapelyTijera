# view_caja_visor.py
import pandas as pd
import streamlit as st

CUENTAS = ["Bs", "$Ch", "$Ze", "$AhCh", "$AhZe"]


def calcular_saldos_dinamicos(df: pd.DataFrame) -> dict:
  """Calcula los saldos dinámicos acumulados por cuenta sumando IN- y restando EG-."""
  saldos = {c: 0.0 for c in CUENTAS}
  if (
      df is None
      or df.empty
      or "tipo" not in df.columns
      or "monto" not in df.columns
  ):
    return saldos

  df_calc = df.copy()
  df_calc["monto"] = pd.to_numeric(df_calc["monto"], errors="coerce").fillna(
      0.0
  )

  for c in CUENTAS:
    ing = df_calc[df_calc["tipo"] == f"IN-{c}"]["monto"].sum()
    eg = df_calc[df_calc["tipo"] == f"EG-{c}"]["monto"].sum()
    saldos[c] = ing - eg

  return saldos


def render_visor(
    df_mes: pd.DataFrame = None,
    mes_sel_nombre: str = "",
    anho_sel=None,
    saldos_fin=None,
    **kwargs,
):
  """Visor de caja ajustado exactamente a la llamada de run_app.py:

  render_visor(df_mes, mes_sel_nombre, anho_sel, saldos_fin)
  """
  titulo_periodo = (
      f" – {mes_sel_nombre} {anho_sel}" if mes_sel_nombre and anho_sel else ""
  )
  st.subheader(f"👁️ Visor General de Caja{titulo_periodo}")

  if df_mes is None:
    df_mes = st.session_state.get("df_movimientos", pd.DataFrame())

  # --- 1. DESPLIEGUE DE SALDOS DINÁMICOS ---
  # Si run_app.py ya le pasa los saldos calculados (saldos_fin), los usa directamente
  if saldos_fin is not None and len(saldos_fin) > 0:
    if isinstance(saldos_fin, pd.Series):
      saldos_dict = saldos_fin.to_dict()
    elif isinstance(saldos_fin, dict):
      saldos_dict = saldos_fin
    else:
      saldos_dict = calcular_saldos_dinamicos(df_mes)
  else:
    saldos_dict = calcular_saldos_dinamicos(df_mes)

  st.markdown("### 💳 Saldos Dinámicos Acumulados")
  cols = st.columns(5)
  for idx, cuenta in enumerate(CUENTAS):
    simbolo = "Bs" if cuenta == "Bs" else "$"
    val = saldos_dict.get(cuenta, 0.0)
    cols[idx].metric(label=f"Saldo {cuenta}", value=f"{simbolo} {val:,.2f}")

  st.markdown("---")

  if df_mes is None or df_mes.empty:
    st.info("No hay movimientos registrados para el período seleccionado.")
    return

  # --- 2. FILTROS LOCALES Y TABLA ---
  col_f1, col_f2 = st.columns(2)
  with col_f1:
    cuenta_sel = st.selectbox(
        "Filtrar por Cuenta", ["Todas"] + CUENTAS, key="visor_cuenta_sel"
    )
  with col_f2:
    tipo_sel = st.selectbox(
        "Filtrar por Flujo",
        ["Todos", "Ingresos (IN)", "Egresos (EG)"],
        key="visor_tipo_sel",
    )

  df_filtered = df_mes.copy()

  if cuenta_sel != "Todas":
    df_filtered = df_filtered[
        df_filtered["tipo"].str.contains(cuenta_sel, na=False)
    ]

  if tipo_sel == "Ingresos (IN)":
    df_filtered = df_filtered[
        df_filtered["tipo"].str.startswith("IN-", na=False)
    ]
  elif tipo_sel == "Egresos (EG)":
    df_filtered = df_filtered[
        df_filtered["tipo"].str.startswith("EG-", na=False)
    ]

  # Cálculo opcional de saldo corrido
  if "monto" in df_filtered.columns and "tipo" in df_filtered.columns:
    df_filtered["monto_neto"] = df_filtered.apply(
        lambda r: (
            r["monto"]
            if str(r.get("tipo", "")).startswith("IN-")
            else -r["monto"]
        ),
        axis=1,
    )
    df_filtered["saldo_corrido"] = df_filtered["monto_neto"].cumsum()

  st.dataframe(df_filtered, use_container_width=True, hide_index=True)


# Aliases de compatibilidad por si se importa con otro nombre
render_caja_visor = render_visor
render_view_caja_visor = render_visor
