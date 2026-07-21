# view_caja_visor.py
import pandas as pd
import streamlit as st

# Cuentas oficiales
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
    df_movimientos: pd.DataFrame = None, rol_usuario: str = "operador"
):
  """Función principal del visor de caja con saldos dinámicos."""
  st.subheader("👁️ Visor General de Caja y Saldos")

  if df_movimientos is None:
    df_movimientos = st.session_state.get("df_movimientos", pd.DataFrame())

  if df_movimientos is None or df_movimientos.empty:
    st.info("No hay datos cargados para mostrar en el visor.")
    return

  # --- 1. SALDOS DINÁMICOS GLOBALES (Revisión de las 5 Cuentas) ---
  saldos = calcular_saldos_dinamicos(df_movimientos)

  st.markdown("### 💳 Saldos Dinámicos Actuales")
  cols = st.columns(5)
  for idx, cuenta in enumerate(CUENTAS):
    simbolo = "Bs" if cuenta == "Bs" else "$"
    val = saldos.get(cuenta, 0.0)
    cols[idx].metric(label=f"Saldo {cuenta}", value=f"{simbolo} {val:,.2f}")

  st.markdown("---")

  # --- 2. FILTROS DE VISUALIZACIÓN ---
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

  df_filtered = df_movimientos.copy()

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

  st.dataframe(df_filtered, use_container_width=True, hide_index=True)


# --- ALIASES DE SEGURIDAD PARA IMPORTACIÓN ---
render_caja_visor = render_visor
render_view_caja_visor = render_visor
