# view_presupuestos_historico.py
import datetime
import pandas as pd
import streamlit as st
from db_connection import (
    actualizar_estado_presupuesto_db,
    eliminar_presupuesto_db,
    guardar_presupuesto_db,
    obtener_presupuestos_db,
)


def render_tarjeta_presupuesto(p: dict, rol_actual: str = "administrador"):
  """Renderiza la tarjeta expandible para un presupuesto individual."""
  id_p = p.get("id")
  nombre = p.get("nombre", "Sin nombre")
  cliente = p.get("cliente", "N/A")
  tipo = p.get("tipo_presupuesto", "General")
  estado = p.get("estado", "Borrador")
  monto = p.get("monto_total", 0.0)
  es_plantilla = p.get("es_plantilla", False)

  # Distintivo visual según el estado
  badge_color = {
      "Borrador": "⚪",
      "Enviado": "🔵",
      "Aprobado": "🟢",
      "Rechazado": "🔴",
  }.get(estado, "⚪")

  titulo_tarjeta = (
      f"#{id_p} | {badge_color} {nombre} — {cliente} (${monto:,.2f})"
  )

  with st.expander(titulo_tarjeta, expanded=False):
    col_info1, col_info2, col_info3 = st.columns([2, 2, 2])

    with col_info1:
      st.markdown(f"**Cliente / Razón Social:** {cliente}")
      st.markdown(f"**Lugar del Evento:** {p.get('lugar_evento') or 'N/A'}")
      st.markdown(f"**Fecha del Evento:** {p.get('fecha_evento') or 'N/A'}")

    with col_info2:
      st.markdown(f"**Tipo de Presupuesto:** `{tipo}`")
      st.markdown(f"**Monto Total:** `${monto:,.2f}`")
      st.markdown(f"**Fecha Emisión:** {p.get('fecha_emision') or 'N/A'}")

    with col_info3:
      # Cambio rápido de Estado
      opciones_estado = ["Borrador", "Enviado", "Aprobado", "Rechazado"]
      idx_actual = (
          opciones_estado.index(estado) if estado in opciones_estado else 0
      )

      nuevo_estado = st.selectbox(
          "Estado del Presupuesto:",
          opciones_estado,
          index=idx_actual,
          key=f"select_estado_{id_p}",
      )

      if nuevo_estado != estado:
        exito, msg = actualizar_estado_presupuesto_db(id_p, nuevo_estado)
        if exito:
          st.toast(f"✅ Presupuesto #{id_p} -> {nuevo_estado}")
          st.rerun()
        else:
          st.error(msg)

    st.divider()

    # Fila de Acciones
    b_col1, b_col2, b_col3, b_col4 = st.columns(4)

    # 1. Cargar en Editor
    with b_col1:
      if st.button(
          "✏️ Cargar en Editor", key=f"btn_edit_{id_p}", use_container_width=True
      ):
        st.session_state["presupuesto_id_activo"] = id_p
        st.success(
            f"Presupuesto #{id_p} cargado. Puedes pasar a la pestaña de"
            " Maquetación."
        )
        st.rerun()

    # 2. Clonar / Replicar
    with b_col2:
      if st.button(
          "📋 Clonar / Replicar",
          key=f"btn_clonar_{id_p}",
          use_container_width=True,
      ):
        payload_clon = {
            "nombre": f"COPIA - {nombre}",
            "cliente": f"{cliente} (Copia)",
            "fecha_evento": p.get("fecha_evento"),
            "lugar_evento": p.get("lugar_evento"),
            "tipo_presupuesto": tipo,
            "monto_total": monto,
            "estado": "Borrador",
            "es_plantilla": False,
            "secciones": p.get("secciones", []),
        }
        exito, msg = guardar_presupuesto_db(payload_clon)
        if exito:
          st.success("¡Presupuesto clonado con éxito!")
          st.rerun()
        else:
          st.error(msg)

    # 3. Marcar / Desmarcar como Plantilla
    with b_col3:
      txt_plantilla = (
          "⭐ Quitar de Plantillas"
          if es_plantilla
          else "⭐ Guardar como Plantilla"
      )
      if st.button(
          txt_plantilla, key=f"btn_plantilla_{id_p}", use_container_width=True
      ):
        exito, msg = guardar_presupuesto_db(
            {"es_plantilla": not es_plantilla}, id_presupuesto=id_p
        )
        if exito:
          st.toast(
              "Plantilla removida" if es_plantilla else "Guardado como plantilla"
          )
          st.rerun()
        else:
          st.error(msg)

    # 4. Eliminar
    with b_col4:
      if st.button(
          "🗑️ Eliminar", key=f"btn_del_{id_p}", use_container_width=True
      ):
        exito, msg = eliminar_presupuesto_db(id_p)
        if exito:
          st.warning(msg)
          st.rerun()
        else:
          st.error(msg)


def render_historico_presupuestos(rol_actual: str = "administrador"):
  """Función principal para renderizar la vista de Histórico y Plantillas."""
  st.subheader("📚 Histórico de Presupuestos y Plantillas Base")

  # Cargar datos desde Supabase
  lista_presupuestos = obtener_presupuestos_db()

  if not lista_presupuestos:
    st.info(
        "No hay presupuestos registrados aún en la base de datos. Crea uno"
        " nuevo en la pestaña de Creación y Carga."
    )
    return

  df_p = pd.DataFrame(lista_presupuestos)

  # ==========================================
  # 1. TARJETAS DE MÉTRICAS (KPIs)
  # ==========================================
  kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

  total_registros = len(df_p)
  monto_aprobado = (
      df_p[df_p["estado"] == "Aprobado"]["monto_total"].sum()
      if "estado" in df_p
      else 0.0
  )
  monto_enviado = (
      df_p[df_p["estado"] == "Enviado"]["monto_total"].sum()
      if "estado" in df_p
      else 0.0
  )
  total_plantillas = (
      df_p[df_p["es_plantilla"] == True].shape[0]
      if "es_plantilla" in df_p
      else 0
  )

  kpi_col1.metric("Total Presupuestos", total_registros)
  kpi_col2.metric("Monto Aprobado", f"${monto_aprobado:,.2f}")
  kpi_col3.metric("Monto en Cotización", f"${monto_enviado:,.2f}")
  kpi_col4.metric("Plantillas Base", total_plantillas)

  st.divider()

  # ==========================================
  # 2. SUB-PESTAÑAS DE NAVEGACIÓN
  # ==========================================
  tab_historico, tab_plantillas = st.tabs(
      ["📜 Histórico General", "⭐ Plantillas Base"]
  )

  # ------------------------------------------
  # TAB 1: HISTÓRICO GENERAL
  # ------------------------------------------
  with tab_historico:
    f_col1, f_col2, f_col3 = st.columns([3, 2, 2])

    with f_col1:
      busqueda = st.text_input(
          "🔍 Buscar por Cliente o Nombre:",
          key="filter_search",
          placeholder="Ej: María Pérez...",
      )

    with f_col2:
      tipos_disp = ["Todos"] + sorted(
          list(df_p["tipo_presupuesto"].dropna().unique())
      )
      filtro_tipo = st.selectbox(
          "Filtrar por Tipo:", tipos_disp, key="filter_tipo"
      )

    with f_col3:
      filtro_estado = st.selectbox(
          "Filtrar por Estado:",
          ["Todos", "Borrador", "Enviado", "Aprobado", "Rechazado"],
          key="filter_estado",
      )

    # Aplicar Filtros
    items_filtrados = lista_presupuestos

    if busqueda:
      b_lower = busqueda.lower()
      items_filtrados = [
          p
          for p in items_filtrados
          if b_lower in str(p.get("nombre", "")).lower()
          or b_lower in str(p.get("cliente", "")).lower()
      ]

    if filtro_tipo != "Todos":
      items_filtrados = [
          p
          for p in items_filtrados
          if p.get("tipo_presupuesto") == filtro_tipo
      ]

    if filtro_estado != "Todos":
      items_filtrados = [
          p for p in items_filtrados if p.get("estado") == filtro_estado
      ]

    st.caption(
        f"Mostrando {len(items_filtrados)} de {total_registros} registros."
    )

    for pres in items_filtrados:
      render_tarjeta_presupuesto(pres, rol_actual)

  # ------------------------------------------
  # TAB 2: PLANTILLAS BASE
  # ------------------------------------------
  with tab_plantillas:
    plantillas = [
        p for p in lista_presupuestos if p.get("es_plantilla") == True
    ]

    if not plantillas:
      st.info(
          "No tienes plantillas marcadas. Para guardar un presupuesto como"
          " plantilla, haz clic en el botón '⭐ Guardar como Plantilla' dentro"
          " del Histórico General."
      )
    else:
      st.markdown(
          "Utiliza estas plantillas preconfiguradas para generar un presupuesto"
          " en segundos haciendo clic en **📋 Clonar / Replicar**."
      )
      for pl in plantillas:
        render_tarjeta_presupuesto(pl, rol_actual)
