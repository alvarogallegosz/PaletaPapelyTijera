# run_app.py
import datetime
import pandas as pd
import streamlit as st

from core_finance_engine import procesar_mes_aislado
from db_connection import obtener_movimientos_locales
from view_auth import render_modulo_autenticacion
from view_caja_carga import render_carga
from view_caja_edicion import render_edicion
from view_caja_historico import render_historico
from view_caja_visor import render_visor
from view_presupuestos_creacion import render_creacion_presupuestos

st.set_page_config(
    page_title="Estructura Administrativa PaletaPapelyTijera", layout="wide"
)

# --- INYECCIÓN DE CSS GLOBAL OPTIMIZADO ---
st.markdown(
    """
    <style>
        /* 1. Ajuste del lienzo superior */
        .block-container {
            padding-top: 3.8rem !important; 
            padding-bottom: 2rem !important;
            max-width: 98% !important;     
        }
        
        /* 2. Compactar espacio muerto */
        div[data-testid="stVerticalBlock"] {
            gap: 0.8rem !important; 
        }
        .element-container {
            margin-bottom: 4px !important;
        }
        
        /* 3. Control de tipografías y márgenes para cabecera responsiva */
        h1 { 
            font-size: 18px !important; 
            font-weight: 700 !important; 
            margin-top: 2px !important;     
            margin-bottom: 4px !important;    
            padding-bottom: 0px !important; 
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        h2 { font-size: 16px !important; font-weight: 700 !important; margin-top: 2px !important; }
        h3 { font-size: 14px !important; font-weight: 600 !important; margin-bottom: 2px !important; }
        
        /* SegmentedControl */
        div[data-testid="stSegmentedControl"] {
            margin-top: 2px !important;    
            margin-bottom: 4px !important;
        }

        /* 4. Subpestañas */
        .stTabs [data-baseweb="tab-list"] {
            gap: 4px;
            background-color: #f8f9fa;
            padding: 4px 6px 0px 6px;
            border-radius: 8px 8px 0px 0px;
            border-bottom: 1px solid #e5e7eb;
        }
        .stTabs [data-baseweb="tab"] {
            height: 32px !important;
            background-color: transparent;
            border-radius: 6px 6px 0px 0px;
            padding: 2px 10px !important;
            font-size: 12px !important;
            font-weight: 500 !important;
            color: #6b7280 !important;
            border: none !important;
        }
        .stTabs [aria-selected="true"] {
            background-color: #ffffff !important;
            color: #1f2937 !important;
            font-weight: 600 !important;
            border-bottom: 3px solid #3b82f6 !important;
        }
    </style>
""",
    unsafe_allow_html=True,
)

# ===================================================
# 🔒 CONTROL DE SESIÓN Y AUTENTICACIÓN
# ===================================================
if "usuario_logueado" not in st.session_state:
    render_modulo_autenticacion()
    st.stop()

rol_actual = st.session_state.get("usuario_rol", "operador").strip().lower()
usuario_activo = st.session_state.get("usuario_logueado", "Usuario")

# --- SIDEBAR: Usuario, rol y control de salida ---
st.sidebar.markdown(f"### 👤 **{usuario_activo.upper()}**")
st.sidebar.caption(f"Rol: {rol_actual.upper()}")

if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True, type="secondary"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.toast("Sesión cerrada correctamente", icon="👋")
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown(
    "<p style='font-size: 11px; color: gray;'>[Espacio reservado para futuros usos]</p>",
    unsafe_allow_html=True,
)

# --- CARGA DE DATOS CENTRALIZADA ---
df_completo = obtener_movimientos_locales()
st.session_state["df_movimientos"] = df_completo

# --- CUERPO PRINCIPAL ---
st.markdown(
    f"<h1>📊 Estructura Administrativa — {usuario_activo.upper()} ({rol_actual.upper()})</h1>",
    unsafe_allow_html=True,
)

# Valores por defecto automáticos para el motor financiero (mes y año en curso)
meses_nombres = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}
anho_sel = datetime.datetime.now().year
mes_sel_num = datetime.datetime.now().month
mes_sel_nombre = meses_nombres[mes_sel_num]

# Procesamiento financiero aislado por mes (5 Cuentas)
if not df_completo.empty:
    df_mes, saldos_ini, saldos_fin = procesar_mes_aislado(
        df_completo, anho_sel, mes_sel_num
    )
    es_consolidado = df_mes["consolidado"].all() if not df_mes.empty and "consolidado" in df_mes.columns else False
else:
    df_mes = pd.DataFrame()
    saldos_ini, saldos_fin = {}, {}
    es_consolidado = False

# ===================================================
# 🧭 NAVEGACIÓN Y PERMISOS SEGÚN MATRIZ DE ROLES
# ===================================================
if rol_actual == "operador":
    modulos_sistema = ["📊 Presupuestos (Servicios al Cliente)"]
elif rol_actual == "gerente":
    modulos_sistema = [
        "📦 Registro Movimientos de Caja",
        "📊 Presupuestos (Servicios al Cliente)",
    ]
elif rol_actual == "contador":
    modulos_sistema = [
        "📦 Registro Movimientos de Caja",
        "📊 Facturación",
        "📊 Administración",
    ]
elif rol_actual == "soporte":
    modulos_sistema = [
        "📦 Registro Movimientos de Caja",
        "📊 Presupuestos (Servicios al Cliente)",
        "📊 Facturación",
        "📊 Administración",
        "⚙️ Soporte Técnico",
    ]
else:  # administrador
    modulos_sistema = [
        "📦 Registro Movimientos de Caja",
        "📊 Presupuestos (Servicios al Cliente)",
        "📊 Facturación",
        "📊 Administración",
        "⚙️ Soporte Técnico",
    ]

modulo_activo = st.segmented_control(
    label="Navegación Módulos",
    options=modulos_sistema,
    default=modulos_sistema[0],
    label_visibility="collapsed",
    key="nav_modulo_principal",
)

# --- ENRUTADOR DE MÓDULOS ---

# 1. CAJA
if modulo_activo == "📦 Registro Movimientos de Caja":
    if rol_actual == "administrador":
        tab1, tab2, tab3, tab4 = st.tabs([
            "📝 Carga de Movimientos",
            "🔍 Libro Diario",
            "🛠️ Modificaciones/Auditoría",
            "📚 Histórico de Cierres Mensuales",
        ])
        with tab1:
            render_carga(rol_actual, es_consolidado)
        with tab2:
            render_visor(df_mes, mes_sel_nombre, anho_sel, saldos_fin)
        with tab3:
            render_edicion(df_completo, rol_actual, es_consolidado)
        with tab4:
            render_historico(df_completo, rol_actual)

    elif rol_actual in ["gerente", "soporte"]:
        tab1, tab2 = st.tabs([
            "🔍 Libro Diario",
            "📚 Histórico de Cierres Mensuales",
        ])
        with tab1:
            render_visor(df_mes, mes_sel_nombre, anho_sel, saldos_fin)
        with tab2:
            render_historico(df_completo, rol_actual)

    elif rol_actual == "contador":
        tab1 = st.tabs(["📚 Histórico de Cierres Mensuales"])[0]
        with tab1:
            render_historico(df_completo, rol_actual)

# 2. PRESUPUESTOS
elif modulo_activo == "📊 Presupuestos (Servicios al Cliente)":
    st.markdown("### 📊 Panel General de Presupuestos")
    
    if rol_actual == "operador":
        tab1 = st.tabs(["📚 Plantillas e Histórico (Impresión)"])[0]
        with tab1:
            st.info("🔍 Módulo de búsqueda y descarga/impresión de presupuestos (Modo Solo Lectura).")
    elif rol_actual in ["gerente", "administrador", "soporte"]:
        tab1, tab2, tab3 = st.tabs([
            "📝 Creación y Carga",
            "🔄 Gestión y Aprobación",
            "📚 Plantillas e Histórico",
        ])
        with tab1:
            render_creacion_presupuestos(rol_actual)
        with tab2:
            st.caption("Gestión y aprobación de presupuestos.")
        with tab3:
            st.caption("Plantillas e histórico de presupuestos.")

# 3. FACTURACIÓN
elif modulo_activo == "📊 Facturación":
    st.markdown("### 📊 Panel General de Facturación")
    if rol_actual in ["contador", "soporte"]:
        st.info("Módulo de visualización y descarga de facturas fiscales (Modo Solo Lectura).")
    else:
        st.info("Módulo de generación de facturas fiscales por servicios al cliente.")

# 4. ADMINISTRACIÓN
elif modulo_activo == "📊 Administración":
    st.markdown("### 📊 Panel General de Administración")
    if rol_actual in ["contador", "soporte"]:
        st.info("Módulo de consulta de bancos, compras, ventas, cuentas por pagar y cobro (Modo Solo Lectura / Descarga).")
    else:
        st.info("Módulo de bancos, compras, ventas, cuentas por pagar y cuentas por cobrar.")

# 5. SOPORTE TÉCNICO
elif modulo_activo == "⚙️ Soporte Técnico":
    st.markdown("### ⚙️ Configuración y Auditorías Técnicas")
    st.info(
        "Módulo de infraestructura con visualización exclusiva del histórico"
        " transaccional del sistema y respaldos de BD."
    )