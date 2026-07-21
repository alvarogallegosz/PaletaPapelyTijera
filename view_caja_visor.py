# view_caja_visor.py
import pandas as pd
import streamlit as st


def preparar_columnas_monto(df: pd.DataFrame) -> pd.DataFrame:
  """Normaliza las columnas numéricas/monto en el DataFrame."""
  if df.empty:
    return df
  df_out = df.copy()
  if "monto" in df_out.columns:
    df_out["monto"] = pd.to_numeric(df_out["monto"], errors="coerce").fillna(0.0)
  return df_out


def render_visor(
    df_movimientos: pd.DataFrame,
    mes_sel_nombre: str = "",
    anho_sel: int = None,
    saldos_fin: dict = None,
    **kwargs,
):
  st.subheader("📊 Visor de Acumulados por Cuenta")

  if df_movimientos is None or df_movimientos.empty:
    st.info("No hay movimientos registrados para mostrar.")
    return

  df_temp = preparar_columnas_monto(df_movimientos)

  # --- LISTA OFICIAL DE LAS 5 CUENTAS ---
  CUENTAS_OFICIALES = ["ING-$", "ING-Bs", "EG-$Ch", "EG-$Ob", "EG-Bs"]

  # Si en el DataFrame la columna se llama 'tipo' o 'cuenta', normalizamos
  col_cuenta = (
      "tipo"
      if "tipo" in df_temp.columns
      else ("cuenta" if "cuenta" in df_temp.columns else None)
  )
  col_cat = (
      "categoria"
      if "categoria" in df_temp.columns
      else ("concepto" if "concepto" in df_temp.columns else None)
  )

  # --- FILTROS DISCRETOS ---
  c1, c2 = st.columns(2)

  opciones_cuenta = ["Todas las Cuentas"] + CUENTAS_OFICIALES
  with c1:
    cuenta_sel = st.selectbox(
        "Filtrar por Cuenta", opciones_cuenta, key="visor_filtro_cuenta"
    )

  cats_unicas = (
      sorted(
          [
              str(x)
              for x in df_temp[col_cat].dropna().unique()
              if str(x).strip() != ""
          ]
      )
      if col_cat
      else []
  )
  opciones_cat = ["Todas las Categorías"] + cats_unicas
  with c2:
    cat_sel = st.selectbox(
        "Filtrar por Categoría", opciones_cat, key="visor_filtro_cat"
    )

  # --- APLICACIÓN DE FILTROS ---
  df_filtrado = df_temp.copy()

  if cuenta_sel != "Todas las Cuentas" and col_cuenta:
    df_filtrado = df_filtrado[df_filtrado[col_cuenta] == cuenta_sel]

  if cat_sel != "Todas las Categorías" and col_cat:
    df_filtrado = df_filtrado[df_filtrado[col_cat] == cat_sel]

  # --- CÁLCULO ALGEBRAICO DE LAS 5 CUENTAS ---
  # Garantizamos que las 5 cuentas siempre existan en el resultado
  totales_por_cuenta = {cta: 0.0 for cta in CUENTAS_OFICIALES}

  if not df_filtrado.empty and col_cuenta:
    # Agrupamos y sumamos algebraicamente los montos
    sumas = df_filtrado.groupby(col_cuenta)["monto"].sum().to_dict()
    for cta, monto in sumas.items():
      if cta in totales_por_cuenta:
        totales_por_cuenta[cta] = float(monto)

  # Convertimos a DataFrame horizontal/tabla financiera discreta
  df_resumen = pd.DataFrame([totales_por_cuenta])

  st.markdown("##### 💵 Acumulado Mensual del Período por Cuenta")

  # Formato de moneda por columna
  formatos = {cta: "${:,.2f}" for cta in CUENTAS_OFICIALES}

  st.dataframe(
      df_resumen.style.format(formatos),
      use_container_width=True,
      hide_index=True,
  )

  # --- LISTADO DETALLADO BAJO LA TABLA ---
  with st.expander("📋 Ver detalle de movimientos filtrados", expanded=False):
    cols_mostrar = [
        c
        for c in ["id", "fecha", col_cuenta, col_cat, "monto"]
        if c and c in df_filtrado.columns
    ]
    if not df_filtrado.empty:
      st.dataframe(
          df_filtrado[cols_mostrar]
          .sort_values(by=["fecha"])
          .style.format({"monto": "${:,.2f}"}),
          use_container_width=True,
          hide_index=True,
      )
    else:
      st.write("No hay registros para este filtro.")


# Aliases de compatibilidad
render_view_caja_visor = render_visor
render_caja_visor = render_visor
