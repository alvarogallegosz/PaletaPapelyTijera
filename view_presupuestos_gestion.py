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

def render_gestion_presupuestos(rol_simulado: str):
    st.markdown(CSS_GESTION, unsafe_allow_html=True)
    st.markdown("## 🔄 Gestión y Aprobación de Presupuestos")

    # --- 1. OBTENCIÓN DE DATOS DESDE BASE DE DATOS ---
    with st.spinner("Sincronizando presupuestos con la base de datos..."):
        lista_presupuestos = obtener_presupuestos_db()

    if not lista_presupuestos:
        st.info("ℹ️ No hay presupuestos registrados aún en la base de datos. Crea uno nuevo en la pestaña de Creación y Carga.")
        return

    df_presupuestos = pd.DataFrame(lista_presupuestos)

    # Validar columnas mínimas requeridas para evitar errores de ejecución
    columnas_esperadas = ["id", "nombre", "cliente", "monto_total", "estado", "tipo_presupuesto", "creado_por", "created_at"]
    for col in columnas_esperadas:
        if col not in df_presupuestos.columns:
            df_presupuestos[col] = "N/A" if col != "monto_total" else 0.0

    # Asegurar formato numérico
    df_presupuestos["monto_total"] = pd.to_numeric(df_presupuestos["monto_total"], errors="coerce").fillna(0.0)

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
        filtro_estado = st.selectbox("📌 Filtrar por Estado:", opciones=estados_disponibles, index=0)
    with f3:
        tipos_disponibles = ["Todos"] + list(df_presupuestos["tipo_presupuesto"].dropna().unique())
        filtro_tipo = st.selectbox("📂 Tipo de Presupuesto:", opciones=tipos_disponibles, index=0)

    # Aplicar Filtros sobre el DataFrame
    df_filtrado = df_presupuestos.copy()

    if busqueda_texto.strip():
        txt = busqueda_texto.strip().lower()
        cond_cliente = df_filtrado["cliente"].astype(str).str.lower().str.contains(txt)
        cond_nombre = df_filtrado["nombre"].astype(str).str.lower().str.contains(txt)
        df_filtrado = df_filtrado[cond_cliente | cond_nombre]

    if filtro_estado != "Todos":
        df_filtrado = df_filtrado[df_filtrado["estado"].astype(str).str.lower() == filtro_estado.lower()]

    if filtro_tipo != "Todos":
        df_filtrado = df_filtrado[df_filtrado["tipo_presupuesto"].astype(str) == filtro_tipo]

    st.markdown(f"**Registros encontrados:** {len(df_filtrado)}")

    # --- 4. VISTA DE DETALLE Y ACCIONES POR REGISTRO ---
    if df_filtrado.empty:
        st.warning("⚠️ No se encontraron presupuestos que coincidan con los criterios de búsqueda.")
        return

    # Renderizar cada presupuesto en un contenedor limpio
    for idx, row in df_filtrado.iterrows():
        p_id = row["id"]
        p_nombre = str(row.get("nombre", "SIN NOMBRE")).upper()
        p_cliente = str(row.get("cliente", "CLIENTE")).upper()
        p_monto = float(row.get("monto_total", 0.0))
        p_estado = str(row.get("estado", "Borrador")).capitalize()
        p_tipo = str(row.get("tipo_presupuesto", "Decoración"))
        p_creador = str(row.get("creado_por", "N/A"))

        # Determinar clase CSS para la etiqueta de estado
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

            # Columna 2: Cambio de Estado Dinámico
            with c_cambio:
                st.markdown("<span style='font-size: 12px; font-weight: bold; color: #64748b;'>Cambiar Estado:</span>", unsafe_allow_html=True)
                opciones_estado = ["Borrador", "Enviado", "Aprobado", "Rechazado"]
                idx_actual = opciones_estado.index(p_estado) if p_estado in opciones_estado else 0
                
                nuevo_estado_sel = st.selectbox(
                    "Estado",
                    options=opciones_estado,
                    index=idx_actual,
                    key=f"sel_est_{p_id}",
                    label_visibility="collapsed"
                )

                if nuevo_estado_sel != p_estado:
                    puede_cambiar = rol_simulado in ["administrador", "gerente"]
                    if puede_cambiar:
                        exito, msj = actualizar_estado_presupuesto_db(p_id, nuevo_estado_sel)
                        if exito:
                            st.toast(f"✅ Estado de #{p_id} actualizado a '{nuevo_estado_sel}'", icon="🎉")
                            st.rerun()
                        else:
                            st.error(f"❌ {msj}")
                    else:
                        st.error("⛔ Requiere rol de Gerente o Administrador.")

            # Columna 3: Botones de Acción
            with c_acciones:
                st.markdown("<span style='font-size: 12px; font-weight: bold; color: #64748b;'>Acciones:</span>", unsafe_allow_html=True)
                col_b1, col_b2 = st.columns(2)

                with col_b1:
                    if st.button("✏️ Editar", key=f"btn_edit_{p_id}", use_container_width=True, help="Carga este presupuesto en el editor para modificarlo"):
                        if cargar_presupuesto_en_session_state(p_id):
                            st.toast(f"📥 Presupuesto #{p_id} cargado en el Editor.", icon="📝")
                            st.rerun()

                with col_b2:
                    puede_eliminar = rol_simulado == "administrador"
                    if st.button("🗑️ Borrar", key=f"btn_del_{p_id}", disabled=not puede_eliminar, use_container_width=True, help="Elimina permanentemente el registro (Solo Administrador)"):
                        exito, msj = eliminar_presupuesto_db(p_id)
                        if exito:
                            st.toast(f"🗑️ Presupuesto #{p_id} eliminado.", icon="✅")
                            st.rerun()
                        else:
                            st.error(f"❌ {msj}")
