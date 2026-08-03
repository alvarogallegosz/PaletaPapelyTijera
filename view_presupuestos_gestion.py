import streamlit as st
import pandas as pd
from datetime import datetime
from db_connection import (
    obtener_presupuestos_db, 
    actualizar_estado_presupuesto_db, 
    eliminar_presupuesto_db
)
from view_presupuestos_creacion import cargar_presupuesto_en_session_state

# ===================================================
# 🎨 ESTILOS CSS COMPACTOS Y BADGES DE ESTADO
# ===================================================
CSS_GESTION = """
<style>
    /* Compactación vertical de contenedores Streamlit */
    div[data-testid="stVerticalBlock"] {
        gap: 0.4rem !important;
    }
    div[data-testid="stMarkdownContainer"] h2,
    div[data-testid="stMarkdownContainer"] h3,
    div[data-testid="stMarkdownContainer"] h4 {
        margin-top: 2px !important;
        margin-bottom: 4px !important;
        padding-top: 0px !important;
        padding-bottom: 0px !important;
    }
    hr {
        margin-top: 8px !important;
        margin-bottom: 12px !important;
    }

    /* Badges de Estado */
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

    /* Estilo de Tarjeta resumida */
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

# ===================================================
# 🖥️ RENDER PRINCIPAL: GESTIÓN Y APROBACIÓN
# ===================================================

def render_gestion_presupuestos(rol_simulado: str = "usuario"):
    st.markdown(CSS_GESTION, unsafe_allow_html=True)
    st.markdown("## 🔄 Gestión y Aprobación de Presupuestos")

    # Determinar privilegios según el rol activo
    rol_actual = str(rol_simulado or "usuario").lower().strip()
    puede_aprobar = rol_actual in ["administrador", "gerente"]
    puede_eliminar = rol_actual == "administrador"

    # --- 1. OBTENCIÓN Y SANITIZACIÓN DE DATOS ---
    with st.spinner("Sincronizando presupuestos con la base de datos..."):
        lista_presupuestos = obtener_presupuestos_db()

    if not lista_presupuestos:
        st.info("ℹ️ No hay presupuestos registrados aún en la base de datos. Crea uno nuevo en la pestaña de Creación.")
        return

    df_presupuestos = pd.DataFrame(lista_presupuestos)

    # Validar columnas mínimas requeridas para evitar errores KeyError
    columnas_esperadas = ["id", "nombre", "cliente", "monto_total", "estado", "tipo_presupuesto", "creado_por", "created_at"]
    for col in columnas_esperadas:
        if col not in df_presupuestos.columns:
            df_presupuestos[col] = "N/A" if col != "monto_total" else 0.0

    # Normalización segura de tipos de datos
    df_presupuestos["monto_total"] = pd.to_numeric(df_presupuestos["monto_total"], errors="coerce").fillna(0.0)
    df_presupuestos["estado"] = df_presupuestos["estado"].fillna("Borrador").astype(str).str.strip().str.capitalize()
    df_presupuestos["tipo_presupuesto"] = df_presupuestos["tipo_presupuesto"].fillna("Decoración").astype(str).str.strip()
    df_presupuestos["nombre"] = df_presupuestos["nombre"].fillna("SIN NOMBRE").astype(str).str.strip()
    df_presupuestos["cliente"] = df_presupuestos["cliente"].fillna("CLIENTE").astype(str).str.strip()

    # --- 2. PANEL DE MÉTRICAS RÁPIDAS (KPIs) ---
    total_registros = len(df_presupuestos)
    monto_total_general = df_presupuestos["monto_total"].sum()
    
    df_aprobados = df_presupuestos[df_presupuestos["estado"].str.lower() == "aprobado"]
    monto_aprobado = df_aprobados["monto_total"].sum()
    cant_aprobados = len(df_aprobados)

    df_pendientes = df_presupuestos[df_presupuestos["estado"].str.lower().isin(["borrador", "enviado"])]
    monto_pendiente = df_pendientes["monto_total"].sum()

    tasa_conversion = (cant_aprobados / total_registros * 100) if total_registros > 0 else 0.0

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
                <div class="card-kpi-titulo">Monto Total Aprobado</div>
                <div class="card-kpi-valor" style="color: #15803d;">${monto_aprobado:,.2f}</div>
            </div>
        """, unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
            <div class="card-kpi">
                <div class="card-kpi-titulo">Por Aprobar / Enviados</div>
                <div class="card-kpi-valor" style="color: #b45309;">${monto_pendiente:,.2f}</div>
            </div>
        """, unsafe_allow_html=True)
    with k4:
        st.markdown(f"""
            <div class="card-kpi">
                <div class="card-kpi-titulo">Tasa de Aprobación</div>
                <div class="card-kpi-valor" style="color: #2563eb;">{tasa_conversion:.1f}%</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # --- 3. BARRA DE FILTROS Y BÚSQUEDA ---
    f1, f2, f3 = st.columns([3, 2, 2])
    with f1:
        busqueda_texto = st.text_input(
            "🔍 Buscar por Cliente o Nombre:", 
            placeholder="Ej: María Pérez o MOD 2 COMUNIÓN",
            key="filtro_busqueda_gestion"
        )
    with f2:
        estados_disponibles = ["Todos", "Borrador", "Enviado", "Aprobado", "Rechazado"]
        filtro_estado = st.selectbox("📌 Filtrar por Estado:", options=estados_disponibles, index=0)
    with f3:
        tipos_unicos = sorted(list(df_presupuestos["tipo_presupuesto"].unique()))
        tipos_disponibles = ["Todos"] + tipos_unicos
        filtro_tipo = st.selectbox("📂 Tipo de Presupuesto:", options=tipos_disponibles, index=0)

    # Aplicar Filtros dinámicos sobre el DataFrame
    df_filtrado = df_presupuestos.copy()

    if busqueda_texto.strip():
        txt = busqueda_texto.strip().lower()
        cond_cliente = df_filtrado["cliente"].str.lower().str.contains(txt, na=False)
        cond_nombre = df_filtrado["nombre"].str.lower().str.contains(txt, na=False)
        df_filtrado = df_filtrado[cond_cliente | cond_nombre]

    if filtro_estado != "Todos":
        df_filtrado = df_filtrado[df_filtrado["estado"].str.lower() == filtro_estado.lower()]

    if filtro_tipo != "Todos":
        df_filtrado = df_filtrado[df_filtrado["tipo_presupuesto"] == filtro_tipo]

    st.markdown(f"**Registros encontrados:** {len(df_filtrado)}")

    # --- 4. VISTA DE DETALLE Y ACCIONES POR REGISTRO ---
    if df_filtrado.empty:
        st.warning("⚠️ No se encontraron presupuestos que coincidan con los criterios de búsqueda.")
        return

    # Renderizar cada presupuesto en un contenedor aislado
    for idx, row in df_filtrado.iterrows():
        p_id = int(row["id"])
        p_nombre = str(row["nombre"]).upper()
        p_cliente = str(row["cliente"]).upper()
        p_monto = float(row["monto_total"])
        p_estado = str(row["estado"]).capitalize()
        p_tipo = str(row["tipo_presupuesto"])
        p_creador = str(row.get("creado_por", "N/A"))

        # Clase CSS correspondiente al estado
        clase_badge = f"badge-{p_estado.lower()}" if p_estado.lower() in ["borrador", "enviado", "aprobado", "rechazado"] else "badge-borrador"

        with st.container(border=True):
            c_info, c_cambio, c_acciones = st.columns([4, 3, 3])

            # Columna 1: Información General
            with c_info:
                st.markdown(
                    f"""
                    <div style="line-height: 1.4;">
                        <span class="badge-estado {clase_badge}">{p_estado}</span> 
                        <strong style="font-size: 15px; margin-left: 6px;">#{p_id} - {p_nombre}</strong><br>
                        <span style="font-size: 13px; color: #475569;">👤 <b>Cliente:</b> {p_cliente}</span><br>
                        <span style="font-size: 13px; color: #475569;">📂 <b>Tipo:</b> {p_tipo} | ✍️ <b>Por:</b> {p_creador}</span><br>
                        <span style="font-size: 16px; font-weight: bold; color: #059669;">Monto: ${p_monto:,.2f}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            # Columna 2: Cambio de Estado Controlado por Rol
            with c_cambio:
                st.markdown("<span style='font-size: 12px; font-weight: bold; color: #64748b;'>Cambiar Estado:</span>", unsafe_allow_html=True)
                opciones_estado = ["Borrador", "Enviado", "Aprobado", "Rechazado"]
                idx_actual = opciones_estado.index(p_estado) if p_estado in opciones_estado else 0
                
                nuevo_estado_sel = st.selectbox(
                    "Estado",
                    options=opciones_estado,
                    index=idx_actual,
                    key=f"sel_est_{p_id}",
                    label_visibility="collapsed",
                    disabled=not puede_aprobar,
                    help="Requiere permisos de Gerente o Administrador" if not puede_aprobar else "Seleccione para actualizar el estado inmediatamente"
                )

                # Si el usuario con permisos cambia el estado en el selector
                if puede_aprobar and nuevo_estado_sel != p_estado:
                    exito, msj = actualizar_estado_presupuesto_db(p_id, nuevo_estado_sel)
                    if exito:
                        st.toast(f"✅ Estado de #{p_id} actualizado a '{nuevo_estado_sel}'", icon="🎉")
                        st.rerun()
                    else:
                        st.error(f"❌ {msj}")

            # Columna 3: Botones de Acción (Editar y Eliminar Seguro)
            with c_acciones:
                st.markdown("<span style='font-size: 12px; font-weight: bold; color: #64748b;'>Acciones:</span>", unsafe_allow_html=True)
                col_b1, col_b2 = st.columns(2)

                with col_b1:
                    if st.button("✏️ Editar", key=f"btn_edit_{p_id}", use_container_width=True, help="Carga este presupuesto en el editor para modificarlo"):
                        if cargar_presupuesto_en_session_state(p_id):
                            st.session_state["pestaña_activa"] = "Creación"
                            st.session_state["modo_vista"] = "edicion"
                            st.toast(f"📥 Presupuesto #{p_id} cargado en el Editor.", icon="📝")
                            st.rerun()
                        else:
                            st.error("❌ No se pudo cargar el presupuesto desde la base de datos.")

                with col_b2:
                    if puede_eliminar:
                        with st.popover("🗑️ Borrar", use_container_width=True):
                            st.markdown(f"**¿Eliminar #{p_id}?**")
                            st.caption("Esta acción no se puede deshacer.")
                            if st.button("Sí, eliminar", key=f"confirm_del_{p_id}", type="primary", use_container_width=True):
                                exito, msj = eliminar_presupuesto_db(p_id)
                                if exito:
                                    st.toast(f"🗑️ Presupuesto #{p_id} eliminado con éxito.", icon="✅")
                                    st.rerun()
                                else:
                                    st.error(f"❌ {msj}")
                    else:
                        st.button("🗑️ Borrar", key=f"btn_del_dis_{p_id}", disabled=True, use_container_width=True, help="Solo el Administrador puede eliminar presupuestos.")
