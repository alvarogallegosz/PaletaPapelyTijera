import datetime
import pandas as pd
import streamlit as st
from db_connection import (
    actualizar_estado_presupuesto_db,
    eliminar_presupuesto_db,
    guardar_presupuesto_db,
    obtener_presupuestos_db,
)
from view_presupuestos_creacion import (
    cargar_presupuesto_en_session_state,
    CLAUSULAS_POR_DEFECTO
)

# ===================================================
# 🎨 ESTILOS CSS UNIFICADOS Y COMPACTOS
# ===================================================
CSS_HISTORICO = """
<style>
    div[data-testid="stVerticalBlock"] {
        gap: 0.4rem !important;
    }
    .badge-estado {
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: bold;
        text-transform: uppercase;
        display: inline-block;
    }
    .badge-borrador { background-color: #e2e8f0; color: #475569; }
    .badge-enviado { background-color: #dbeafe; color: #1e40af; }
    .badge-aprobado { background-color: #dcfce7; color: #166534; }
    .badge-rechazado { background-color: #fee2e2; color: #991b1b; }

    .card-kpi {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 10px 14px;
        text-align: center;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .card-kpi-titulo { font-size: 11px; color: #64748b; font-weight: 600; text-transform: uppercase; }
    .card-kpi-valor { font-size: 20px; font-weight: bold; color: #0f172a; margin-top: 2px; }
</style>
"""


def render_tarjeta_presupuesto(p: dict, rol_actual: str = "administrador", idx: str = "0"):
    """Renderiza la tarjeta expandible para un presupuesto individual con transferencia íntegra de datos."""
    rol_clean = str(rol_actual or "usuario").lower().strip()
    puede_aprobar = rol_clean in ["administrador", "gerente"]
    puede_eliminar = rol_clean == "administrador"

    id_p = p.get("id") or f"temp_{idx}"
    nombre = str(p.get("nombre", "Sin nombre")).strip().upper()
    cliente = str(p.get("cliente", "N/A")).strip().upper()
    fecha_evt = p.get("fecha_evento") or "N/A"
    tipo = str(p.get("tipo_presupuesto", "General")).strip()
    estado = str(p.get("estado", "Borrador")).strip().capitalize()
    
    try:
        monto = float(p.get("monto_total", 0.0))
    except (ValueError, TypeError):
        monto = 0.0
        
    es_plantilla = bool(p.get("es_plantilla", False))

    # Distintivo visual según el estado
    badge_color = {
        "Borrador": "⚪",
        "Enviado": "🔵",
        "Aprobado": "🟢",
        "Rechazado": "🔴",
    }.get(estado, "⚪")

    titulo_tarjeta = f"#{id_p} | {badge_color} {fecha_evt} {nombre} — {cliente} (${monto:,.2f})"

    with st.expander(titulo_tarjeta, expanded=False):
        col_info1, col_info2, col_info3 = st.columns([2, 2, 2])

        with col_info1:
            st.markdown(f"**👤 Cliente:** {cliente}")
            st.markdown(f"**📍 Lugar:** {p.get('lugar_evento') or 'N/A'}")
            st.markdown(f"**📅 Fecha Evento:** {fecha_evt}")

        with col_info2:
            st.markdown(f"**📂 Tipo:** `{tipo}`")
            st.markdown(f"**💵 Monto Total:** `${monto:,.2f}`")
            st.markdown(f"**📝 Emisión:** {p.get('fecha_emision') or 'N/A'}")

        with col_info3:
            opciones_estado = ["Borrador", "Enviado", "Aprobado", "Rechazado"]
            idx_actual = opciones_estado.index(estado) if estado in opciones_estado else 0

            nuevo_estado = st.selectbox(
                "Estado del Presupuesto:",
                options=opciones_estado,
                index=idx_actual,
                key=f"select_estado_{id_p}_{idx}",
                disabled=not puede_aprobar,
                help="Requiere rol de Gerente o Administrador" if not puede_aprobar else "Cambiar estado del registro"
            )

            if puede_aprobar and nuevo_estado != estado:
                exito, msg = actualizar_estado_presupuesto_db(id_p, nuevo_estado)
                if exito:
                    st.toast(f"✅ Presupuesto #{id_p} -> {nuevo_estado}", icon="🎉")
                    st.rerun()
                else:
                    st.error(msg)

        st.divider()

        # --- FILA DE ACCIONES ---
        b_col1, b_col2, b_col3, b_col4 = st.columns(4)

        # 1. Cargar en Editor (Integridad total a Creación)
        with b_col1:
            if st.button("✏️ Cargar en Editor", key=f"btn_edit_{id_p}_{idx}", use_container_width=True, help="Carga todo el contenido en la pestaña de Creación"):
                if cargar_presupuesto_en_session_state(id_p):
                    st.session_state["pestaña_activa"] = "Creación"
                    st.session_state["modo_vista"] = "edicion"
                    st.toast(f"📥 Presupuesto #{id_p} cargado sin truncamiento en el Editor.", icon="📝")
                    st.rerun()
                else:
                    st.error("❌ No se pudo rehidratar el presupuesto seleccionado.")

        # 2. Clonar / Replicar (Duplicación 100% Fiel)
        with b_col2:
            if st.button("📋 Clonar / Replicar", key=f"btn_clonar_{id_p}_{idx}", use_container_width=True, help="Duplica el presupuesto con todas sus secciones y cláusulas exactas"):
                clausulas_origen = p.get("clausulas")
                if not clausulas_origen or not str(clausulas_origen).strip():
                    clausulas_a_guardar = CLAUSULAS_POR_DEFECTO
                else:
                    clausulas_a_guardar = str(clausulas_origen)

                payload_clon = {
                    "nombre": f"COPIA - {nombre}",
                    "cliente": f"{cliente} (COPIA)",
                    "fecha_evento": p.get("fecha_evento"),
                    "lugar_evento": p.get("lugar_evento", ""),
                    "fecha_emision": datetime.date.today().strftime("%Y-%m-%d"),
                    "tipo_presupuesto": tipo,
                    "monto_total": monto,
                    "clausulas": clausulas_a_guardar,
                    "secciones": p.get("secciones", []),
                    "estado": "Borrador",
                    "es_plantilla": False,
                    "creado_por": st.session_state.get("usuario_logueado", "Sistema")
                }
                
                exito, msg = guardar_presupuesto_db(payload_clon)
                if exito:
                    st.toast("✨ Presupuesto clonado con éxito con el 100% de su contenido.", icon="📋")
                    st.rerun()
                else:
                    st.error(f"❌ Error al clonar: {msg}")

        # 3. Marcar / Desmarcar como Plantilla (Preserva el Payload Completo)
        with b_col3:
            txt_plantilla = "⭐ Quitar de Plantillas" if es_plantilla else "⭐ Guardar como Plantilla"
            if st.button(txt_plantilla, key=f"btn_plantilla_{id_p}_{idx}", use_container_width=True):
                payload_plantilla = {
                    "nombre": nombre,
                    "cliente": cliente,
                    "fecha_evento": p.get("fecha_evento"),
                    "lugar_evento": p.get("lugar_evento", ""),
                    "fecha_emision": p.get("fecha_emision", ""),
                    "tipo_presupuesto": tipo,
                    "monto_total": monto,
                    "clausulas": p.get("clausulas", CLAUSULAS_POR_DEFECTO),
                    "secciones": p.get("secciones", []),
                    "estado": estado,
                    "es_plantilla": not es_plantilla
                }
                exito, msg = guardar_presupuesto_db(payload_plantilla, id_presupuesto=id_p)
                if exito:
                    st.toast("⭐ Plantilla removida" if es_plantilla else "⭐ Guardado como plantilla", icon="📌")
                    st.rerun()
                else:
                    st.error(msg)

        # 4. Eliminar (Con Popover de Confirmación)
        with b_col4:
            if puede_eliminar:
                with st.popover("🗑️ Eliminar", use_container_width=True):
                    st.markdown(f"**¿Borrar #{id_p}?**")
                    st.caption("Esta acción es irreversible.")
                    if st.button("Sí, borrar", key=f"confirm_del_hist_{id_p}_{idx}", type="primary", use_container_width=True):
                        exito, msg = eliminar_presupuesto_db(id_p)
                        if exito:
                            st.toast(f"🗑️ Presupuesto #{id_p} eliminado.", icon="✅")
                            st.rerun()
                        else:
                            st.error(msg)
            else:
                st.button("🗑️ Eliminar", key=f"btn_del_dis_{id_p}_{idx}", disabled=True, use_container_width=True, help="Solo Administradores pueden borrar registros.")


def render_historico_presupuestos(rol_actual: str = "administrador"):
    """Función principal para renderizar la vista de Histórico y Plantillas Base."""
    st.markdown(CSS_HISTORICO, unsafe_allow_html=True)
    st.markdown("## 📚 Histórico de Presupuestos y Plantillas Base")

    # Cargar datos desde Supabase
    with st.spinner("Cargando catálogo histórico desde la base de datos..."):
        lista_presupuestos = obtener_presupuestos_db()

    if not lista_presupuestos:
        st.info("ℹ️ No hay presupuestos registrados aún en la base de datos. Crea uno nuevo en la pestaña de Creación.")
        return

    df_p = pd.DataFrame(lista_presupuestos)

    # Sanitizar columnas necesarias
    for col in ["estado", "tipo_presupuesto", "nombre", "cliente"]:
        if col not in df_p.columns:
            df_p[col] = ""
        else:
            df_p[col] = df_p[col].fillna("").astype(str)

    if "monto_total" not in df_p.columns:
        df_p["monto_total"] = 0.0
    else:
        df_p["monto_total"] = pd.to_numeric(df_p["monto_total"], errors="coerce").fillna(0.0)

    if "es_plantilla" not in df_p.columns:
        df_p["es_plantilla"] = False
    else:
        df_p["es_plantilla"] = df_p["es_plantilla"].fillna(False).astype(bool)

    # ==========================================
    # 1. TARJETAS DE MÉTRICAS (KPIs)
    # ==========================================
    total_registros = len(df_p)
    monto_aprobado = df_p[df_p["estado"].str.lower() == "aprobado"]["monto_total"].sum()
    monto_enviado = df_p[df_p["estado"].str.lower() == "enviado"]["monto_total"].sum()
    total_plantillas = df_p[df_p["es_plantilla"] == True].shape[0]

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""
            <div class="card-kpi">
                <div class="card-kpi-titulo">Total Registros</div>
                <div class="card-kpi-valor">{total_registros}</div>
            </div>
        """, unsafe_allow_html=True)
    with k2:
        st.markdown(f"""
            <div class="card-kpi">
                <div class="card-kpi-titulo">Monto Aprobado</div>
                <div class="card-kpi-valor" style="color: #15803d;">${monto_aprobado:,.2f}</div>
            </div>
        """, unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
            <div class="card-kpi">
                <div class="card-kpi-titulo">Monto Cotizado</div>
                <div class="card-kpi-valor" style="color: #b45309;">${monto_enviado:,.2f}</div>
            </div>
        """, unsafe_allow_html=True)
    with k4:
        st.markdown(f"""
            <div class="card-kpi">
                <div class="card-kpi-titulo">Plantillas Base</div>
                <div class="card-kpi-valor" style="color: #2563eb;">{total_plantillas}</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ==========================================
    # 2. SUB-PESTAÑAS DE NAVEGACIÓN
    # ==========================================
    tab_historico, tab_plantillas = st.tabs(["📜 Histórico General", "⭐ Plantillas Base"])

    # ------------------------------------------
    # TAB 1: HISTÓRICO GENERAL
    # ------------------------------------------
    with tab_historico:
        f_col1, f_col2, f_col3 = st.columns([3, 2, 2])

        with f_col1:
            busqueda = st.text_input(
                "🔍 Buscar por Cliente o Nombre:",
                key="filter_search_hist",
                placeholder="Ej: María Pérez...",
            )

        with f_col2:
            tipos_disp = ["Todos"] + sorted(list(df_p["tipo_presupuesto"].str.strip().unique()))
            filtro_tipo = st.selectbox("📂 Filtrar por Tipo:", options=tipos_disp, key="filter_tipo_hist")

        with f_col3:
            filtro_estado = st.selectbox(
                "📌 Filtrar por Estado:",
                options=["Todos", "Borrador", "Enviado", "Aprobado", "Rechazado"],
                key="filter_estado_hist",
            )

        # Aplicar Filtros
        items_filtrados = lista_presupuestos

        if busqueda.strip():
            b_lower = busqueda.strip().lower()
            items_filtrados = [
                p for p in items_filtrados
                if b_lower in str(p.get("nombre", "")).lower() or b_lower in str(p.get("cliente", "")).lower()
            ]

        if filtro_tipo != "Todos":
            items_filtrados = [
                p for p in items_filtrados
                if str(p.get("tipo_presupuesto", "")).strip() == filtro_tipo
            ]

        if filtro_estado != "Todos":
            items_filtrados = [
                p for p in items_filtrados
                if str(p.get("estado", "")).strip().lower() == filtro_estado.lower()
            ]

        st.caption(f"Mostrando {len(items_filtrados)} de {total_registros} registros.")

        for idx_num, pres in enumerate(items_filtrados):
            render_tarjeta_presupuesto(pres, rol_actual, idx=f"hist_{idx_num}")

    # ------------------------------------------
    # TAB 2: PLANTILLAS BASE
    # ------------------------------------------
    with tab_plantillas:
        plantillas = [p for p in lista_presupuestos if bool(p.get("es_plantilla", False))]

        if not plantillas:
            st.info(
                "ℹ️ No tienes plantillas marcadas. Para guardar un presupuesto como plantilla, haz clic en el botón '⭐ Guardar como Plantilla' dentro del Histórico General."
            )
        else:
            st.markdown("Utiliza estas plantillas preconfiguradas para generar un presupuesto en segundos haciendo clic en **📋 Clonar / Replicar**.")
            for idx_num, pl in enumerate(plantillas):
                render_tarjeta_presupuesto(pl, rol_actual, idx=f"plan_{idx_num}")
