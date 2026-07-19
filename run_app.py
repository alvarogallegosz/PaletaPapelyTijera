# run_app.py
import streamlit as st
import datetime
from db_connection import obtener_movimientos_locales
from core_finance_engine import procesar_mes_aislado
from view_caja_carga import render_carga
from view_caja_visor import render_visor
from view_caja_edicion import render_edicion
from view_caja_historico import render_historico
from view_presupuestos_creacion import render_creacion_presupuestos

st.set_page_config(page_title="Estructura Administrativa PaletaPapelyTijera", layout="wide")

# --- INYECCIÓN DE CSS GLOBAL OPTIMIZADO (ESPACIOS ULTRA COMPACTOS Y RESPETO DE TÍTULOS) ---
st.markdown("""
    <style>
        /* 1. Ajuste del lienzo superior para respetar la barra de herramientas de Streamlit */
        .block-container {
            padding-top: 2.4rem !important; 
            padding-bottom: 1rem !important;
            max-width: 98% !important;     
        }
        
        /* 2. Compactar espacio muerto entre elementos */
        div[data-testid="stVerticalBlock"] {
            gap: 0.5rem !important; 
        }
        .element-container {
            margin-bottom: 5px !important;
        }
        
        /* 3. Control estricto de tipografías y márgenes para evitar solapamientos */
        h1 { 
            font-size: 22px !important; 
            font-weight: 700 !important; 
            margin-top: 4px !important;     
            margin-bottom: 6px !important;    
            padding-bottom: 0px !important; 
        }
        h2 { font-size: 18px !important; font-weight: 700 !important; margin-top: 2px !important; }
        h3 { font-size: 15px !important; font-weight: 600 !important; margin-bottom: 2px !important; }
        
        /* El SegmentedControl viaja a una distancia proporcional perfecta (Ajuste 7mm) */
        div[data-testid="stSegmentedControl"] {
            margin-top: 4px !important;    
            margin-bottom: 6px !important;
        }

        /* 4. Unificación estética de las subpestañas */
        .stTabs [data-baseweb="tab-list"] {
            gap: 4px;
            background-color: #f8f9fa;
            padding: 4px 6px 0px 6px;
            border-radius: 8px 8px 0px 0px;
            border-bottom: 1px solid #e5e7eb;
        }
        .stTabs [data-baseweb="tab"] {
            height: 34px !important;
            background-color: transparent;
            border-radius: 6px 6px 0px 0px;
            padding: 4px 14px !important;
            font-size: 13px !important;
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
""", unsafe_allow_html=True)

# --- SIDEBAR DE CONFIGURACIÓN GLOBAL ---
st.sidebar.markdown("### 🛠️ Entorno de Desarrollo")
rol_simulado = st.sidebar.selectbox("Rol Activo:", ["administrador", "gerente", "contador", "operador"])

df_completo = obtener_movimientos_locales()

st.sidebar.markdown("---")
st.sidebar.subheader("📅 Filtro Global Temporal")
meses_nombres = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
anho_sel = st.sidebar.selectbox("Año", [2026, 2025])
mes_sel_nombre = st.sidebar.selectbox("Mes", list(meses_nombres.values()), index=datetime.datetime.now().month - 1)
mes_sel_num = [k for k, v in meses_nombres.items() if v == mes_sel_nombre][0]

# Procesamiento financiero aislado por mes
df_mes, saldos_ini, saldos_fin = procesar_mes_aislado(df_completo, anho_sel, mes_sel_num)

# Detección vectorial en caliente de consolidación
es_consolidado = df_mes["consolidado"].all() if not df_mes.empty else False

# --- CUERPO PRINCIPAL ---
# Título Ejecutivo Compactado
st.markdown(f"<h1>📊 Estructura Administrativa — {rol_simulado.upper()}</h1>", unsafe_allow_html=True)

# Definición homologada de los módulos principales en formato Botones de Píldora
modulos_sistema = ["📦 Registro Movimientos de Caja", "📊 Presupuestos (Servicios al Cliente)", "📊 Facturación", "📊 Administración", "⚙️ Soporte Técnico"]

# Reemplazo de st.radio por control segmentado de bajo perfil con eliminación total de etiquetas verticales
modulo_activo = st.segmented_control(
    label="Navegación Módulos",
    options=modulos_sistema,
    default="📦 Registro Movimientos de Caja",
    label_visibility="collapsed"  # Elimina el label superior y compacta la distancia con el H1
)

# Enrutador de Módulos con subpestañas consistentes
# I. REGISTRO MOVIMIENTOS DE CAJA
if modulo_activo == "📦 Registro Movimientos de Caja":
    tab1, tab2, tab3, tab4 = st.tabs([
        "📝 Carga de Movimientos", 
        "🔍 Libro Diario", 
        "🛠️ Modificaciones/Auditoría", 
        "📚 Histórico de Cierres Mensuales"
    ])
    
    with tab1:
        render_carga(rol_simulado, es_consolidado)
    with tab2:
        render_visor(df_mes, mes_sel_nombre, anho_sel, saldos_fin)
    with tab3:
        render_edicion(df_mes, rol_simulado, es_consolidado)
    with tab4:
        render_historico(df_completo, rol_simulado)

# II. PRESUPUESTOS (SERVICIOS AL CLIENTE)
elif modulo_activo == "📊 Presupuestos (Servicios al Cliente)":
    st.markdown("### 📊 Panel General de Presupuestos")
    tab1, tab2, tab3 = st.tabs(["📝 Creación y Carga", "🔄 Gestión y Aprobación", "📚 Plantillas e Histórico"])
    with tab1:
        render_creacion_presupuestos(rol_simulado)
        
# III. FACTURACIÓN
elif modulo_activo == "📊 Facturación":
    st.markdown("### 📊 Panel General de facturación")
    st.info("Módulo de generación de facturas fiscales por servicios al cliente.")

# IV. ADMINISTRACIÓN
elif modulo_activo == "📊 Administración":
    st.markdown("### 📊 Panel General de Administración")
    st.info("Módulo de bancos, compras, ventas, cuantas por pagar, cuentas por cobrar.")

# V. SOPORTE TÉCNICO
elif modulo_activo == "⚙️ Soporte Técnico":
    st.markdown("### ⚙️ Configuración y Auditorías Técnicas")
    st.info("Módulo de infraestructura con visualización exclusiva del histórico transaccional del sistema. y respaldos de BD.")
