# view_caja_visor.py
import pandas as pd
import streamlit as st


def preparar_columnas_monto(df: pd.DataFrame) -> pd.DataFrame:
  """Normaliza las columnas numéricas/monto en el DataFrame para evitar errores de tipo."""
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
  """Renderiza la vista analítica del Visor con filtros avanzados y acumulados/sumatorias dinámicas en tiempo real."""
  st.header("📊 Visor Analítico y Acumulados")

  if df_movimientos is None or df_movimientos.empty:
    st.info("No hay movimientos registrados para mostrar.")
    return

  df_temp = preparar_columnas_monto(df_movimientos)
  df_temp["fecha_dt"] = pd.to_datetime(df_temp["fecha"], errors="coerce")

  # --- 1. SELECCIÓN/MUESTRA DE PERÍODO ---
  # Si run_app ya le pasó el mes y el año pre-filtrados
  if mes_sel_nombre and anho_sel:
    st.subheader(f"🗓️ Período Evaluado: {mes_sel_nombre} {anho_sel}")
    df_mes = df_temp.copy()
  else:
    st.subheader("🗓️ Selección de Período")
    col_anho, col_mes = st.columns(2)

    anhos_disponibles = sorted(
        df_temp["fecha_dt"].dt.year.dropna().unique().astype(int), reverse=True
    )
    if not anhos_disponibles:
      st.warning("No se encontraron fechas válidas en los registros.")
      return

    with col_anho:
      anho_sel = st.selectbox(
          "Seleccione el Año", anhos_disponibles, key="visor_anho"
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
      mes_num = st.selectbox(
          "Seleccione el Mes",
          range(1, 13),
          format_func=lambda x: meses_nombres[x - 1],
          key="visor_mes",
      )

    mascara_periodo = (df_temp["fecha_dt"].dt.year == int(anho_sel)) & (
        df_temp["fecha_dt"].dt.month == int(mes_num)
    )
    df_mes = df_temp[mascara_periodo].copy()

  if df_mes.empty:
    st.info("No existen movimientos en el período seleccionado.")
    return

  # --- 2. FILTROS DINÁMICOS POR TIPO Y CATEGORÍA ---
  st.markdown("---")
  st.subheader("🔍 Filtros de Segmentación")
  col_f1, col_f2 = st.columns(2)

  tipos_unicos = (
      sorted(
          [
              str(x)
              for x in df_mes["tipo"].dropna().unique()
              if str(x).strip() != ""
          ]
      )
      if "tipo" in df_mes.columns
      else []
  )
  opciones_tipo = ["Todos los Tipos"] + tipos_unicos

  with col_f1:
    tipo_sel = st.selectbox(
        "Filtrar por Tipo de Cuenta", opciones_tipo, key="visor_tipo"
    )

  cat_col = (
      "categoria"
      if "categoria" in df_mes.columns
      else ("concepto" if "concepto" in df_mes.columns else None)
  )
  cats_unicas = (
      sorted(
          [
              str(x)
              for x in df_mes[cat_col].dropna().unique()
              if str(x).strip() != ""
          ]
      )
      if cat_col
      else []
  )
  opciones_cat = ["Todas las Categorías"] + cats_unicas

  with col_f2:
    cat_sel = st.selectbox(
        "Filtrar por Categoría / Concepto", opciones_cat, key="visor_cat"
    )

  # Aplicar filtros
  df_filtrado = df_mes.copy()
  if tipo_sel != "Todos los Tipos" and "tipo" in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado["tipo"] == tipo_sel]

  if cat_sel != "Todas las Categorías" and cat_col:
    df_filtrado = df_filtrado[df_filtrado[cat_col] == cat_sel]

  # --- 3. ACUMULADOS PARCIALES Y MÉTRICAS CLAVE ---
  st.markdown("---")
  st.subheader("💰 Acumulados Parciales")

  if df_filtrado.empty:
    st.warning("No hay registros que coincidan con la combinación de filtros.")
    return

  total_monto = (
      float(df_filtrado["monto"].sum()) if "monto" in df_filtrado.columns else 0.0
  )
  cant_registros = len(df_filtrado)
  promedio_monto = (
      (total_monto / cant_registros) if cant_registros > 0 else 0.0
  )

  m1, m2, m3 = st.columns(3)
  m1.metric("Sumatoria Total (Filtro)", f"${total_monto:,.2f}")
  m2.metric("Nº de Registros", f"{cant_registros}")
  m3.metric("Promedio por Asiento", f"${promedio_monto:,.2f}")

  # --- 4. DESGLOSE ANALÍTICO (TABLAS DE ACUMULADOS) ---
  st.markdown("#### 📊 Resumen por Agrupación")
  tab_tipo, tab_cat = st.tabs(
      ["Acumulado por Tipo", "Acumulado por Categoría"]
  )

  with tab_tipo:
    if "tipo" in df_filtrado.columns and "monto" in df_filtrado.columns:
      resumen_tipo = (
          df_filtrado.groupby("tipo")["monto"]
          .agg(["sum", "count", "mean"])
          .reset_index()
      )
      resumen_tipo.columns = [
          "Tipo de Cuenta",
          "Monto Total ($)",
          "Cantidad",
          "Promedio ($)",
      ]
      resumen_tipo["% del Total"] = (
          (resumen_tipo["Monto Total ($)"] / total_monto * 100)
          if total_monto != 0
          else 0.0
      )

      st.dataframe(
          resumen_tipo.style.format({
              "Monto Total ($)": "${:,.2f}",
              "Promedio ($)": "${:,.2f}",
              "% del Total": "{:.1f}%",
          }),
          use_container_width=True,
          hide_index=True,
      )
    else:
      st.info("Columna 'tipo' no disponible para desglose.")

  with tab_cat:
    if cat_col and "monto" in df_filtrado.columns:
      resumen_cat = (
          df_filtrado.groupby(cat_col)["monto"]
          .agg(["sum", "count", "mean"])
          .reset_index()
      )
      resumen_cat.columns = [
          "Categoría / Concepto",
          "Monto Total ($)",
          "Cantidad",
          "Promedio ($)",
      ]
      resumen_cat["% del Total"] = (
          (resumen_cat["Monto Total ($)"] / total_monto * 100)
          if total_monto != 0
          else 0.0
      )

      st.dataframe(
          resumen_cat.style.format({
              "Monto Total ($)": "${:,.2f}",
              "Promedio ($)": "${:,.2f}",
              "% del Total": "{:.1f}%",
          }),
          use_container_width=True,
          hide_index=True,
      )
    else:
      st.info("Columna de categoría/concepto no disponible para desglose.")

  # --- 5. DETALLE DE MOVIMIENTOS FILTRADOS ---
  with st.expander("📋 Ver Listado Completo de Registros Filtrados"):
    columnas_mostrar = [
        c
        for c in ["id", "fecha", "concepto", "categoria", "tipo", "monto"]
        if c in df_filtrado.columns
    ]
    st.dataframe(
        df_filtrado[columnas_mostrar]
        .sort_values(by=["fecha", "id"])
        .style.format({"monto": "${:,.2f}"}),
        use_container_width=True,
        hide_index=True,
    )


# Aliases de compatibilidad
render_view_caja_visor = render_visor
render_caja_visor = render_visor
