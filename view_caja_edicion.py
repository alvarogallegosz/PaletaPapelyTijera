# view_caja_edicion.py
import datetime
import pandas as pd
import streamlit as st

from db_connection import actualizar_movimiento_db, obtener_movimientos_locales


def render_edicion(df_completo, rol_actual, es_consolidado):
  st.markdown("### 🛠️ Modificaciones Generales de Auditoría")

  if df_completo.empty:
    st.info("No hay registros editables en la base de datos.")
    return

  # --- FILTROS INTERNOS DE AUDITORÍA ---
  df = df_completo.copy()
  df["fecha_dt"] = pd.to_datetime(df["fecha"])

  col_anio, col_mes, col_buscar = st.columns([1, 1, 2])

  # Selector de Año
  anios = sorted(df["fecha_dt"].dt.year.unique(), reverse=True)
  with col_anio:
    anio_sel = st.selectbox("Año a editar:", options=anios, index=0)

  # Selector de Mes
  meses_nombres = [
      "Todo el año",
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
    mes_sel = st.selectbox("Mes:", options=meses_nombres, index=0)

  # Buscador de texto (Detalle, ID o Categoría)
  with col_buscar:
    busqueda = st.text_input(
        "🔍 Buscador rápido:", placeholder="Ej: 147, Zelle, Imprenta..."
    )

  # Aplicar filtrado
  df_filtrado = df[df["fecha_dt"].dt.year == anio_sel].copy()

  if mes_sel != "Todo el año":
    num_mes = meses_nombres.index(mes_sel)
    df_filtrado = df_filtrado[df_filtrado["fecha_dt"].dt.month == num_mes]

  if busqueda:
    b_lower = busqueda.strip().lower()
    df_filtrado = df_filtrado[
        df_filtrado["id"].astype(str).str.contains(b_lower)
        | df_filtrado["detalle"].astype(str).str.lower().str.contains(b_lower)
        | df_filtrado["categoria"]
        .astype(str)
        .str.lower()
        .str.contains(b_lower)
    ]

  if df_filtrado.empty:
    st.warning("No se encontraron registros con los filtros seleccionados.")
    return

  es_consolidado_puro = bool(es_consolidado)
  if es_consolidado_puro:
    st.warning(
        "🔒 **EDICIÓN SUSPENDIDA:** Los registros están blindados por"
        " consolidación administrativa."
    )
    return

  st.caption(
      f"💡 Editando {len(df_filtrado)} registros. Haz doble clic sobre cualquier"
      " celda para modificar (Estilo Excel) y presiona guardar al finalizar."
  )

  # --- EDITOR INTERACTIVO ---
  df_editado = st.data_editor(
      df_filtrado,
      column_order=[
          "id",  # Agregado ID visible para control
          "fecha",
          "categoria",
          "detalle",
          "tipo",
          "monto",
          "tasa",
          "comentarios",
      ],
      column_config={
          "id": st.column_config.NumberColumn("ID", width=60, disabled=True),
          "fecha": st.column_config.DateColumn(
              "Fecha", width=100, format="DD/MM/YYYY"
          ),
          "categoria": st.column_config.TextColumn("Categoría", width=160),
          "detalle": st.column_config.TextColumn("Descripción", width=340),
          "tipo": st.column_config.SelectboxColumn(
              "Tipo Cuenta",
              width=120,
              options=[
                  "IN-Bs",
                  "EG-Bs",
                  "IN-$Ze",
                  "EG-$Ze",
                  "IN-$Ch",
                  "EG-$Ch",
                  "IN-$AhZe",
                  "EG-$AhZe",
                  "IN-$AhCh",
                  "EG-$AhCh",
              ],
          ),
          "monto": st.column_config.NumberColumn(
              "Monto Base", width=130, min_value=0.0, format="%.2f"
          ),
          "tasa": st.column_config.NumberColumn(
              "Tasa Monitor", width=110, min_value=0.0, format="%.2f"
          ),
          "comentarios": st.column_config.TextColumn("Comentario", width=340),
      },
      disabled=es_consolidado_puro,
      hide_index=True,
      use_container_width=False,
      height=500,
      key="editor_excel_caja",
  )

  # --- GUARDAR CAMBIOS ---
  if not es_consolidado_puro:
    if st.button("💾 Aplicar Cambios Consolidados en Base de Datos"):
      for _, row_editada in df_editado.iterrows():
        id_reg = int(row_editada["id"])

        # Manejo flexible de la fecha si regresa como string o date de Streamlit
        fecha_str = (
            row_editada["fecha"].strftime("%Y-%m-%d")
            if isinstance(row_editada["fecha"], (datetime.date, pd.Timestamp))
            else str(row_editada["fecha"])
        )

        cambios = {
            "fecha": fecha_str,
            "categoria": str(row_editada["categoria"]).strip().upper(),
            "detalle": str(row_editada["detalle"]).strip(),
            "tipo": row_editada["tipo"],
            "monto": float(row_editada["monto"]),
            "tasa": (
                float(row_editada["tasa"])
                if pd.notnull(row_editada["tasa"])
                else 1.0
            ),
            "comentarios": str(row_editada["comentarios"]).strip(),
            "modificado_por": rol_actual,
        }
        actualizar_movimiento_db(id_reg, cambios)

      obtener_movimientos_locales()
      st.success("🎉 ¡Todos los cambios han sido actualizados en Supabase!")
      st.rerun()