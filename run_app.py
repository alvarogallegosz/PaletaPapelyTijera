# run_app.py
import streamlit as st
import datetime
from db_connection import obtener_movimientos_locales
from core_finance_engine import procesar_mes_aislado
from view_caja_carga import render_carga
from view_caja_visor import render_visor
from view_caja_edicion import render_edicion
from view_caja_historico import render_historico

st.set_page_config(page_title="Control Maestro ERP", layout="wide")

# CSS Correcto inyectado sin vulnerabilidades de compilación
st.markdown("""
    <style>
    h1 { font-size: 24px !important; font-weight: 700 !important; margin-bottom: 5px !important; }
    h2 { font-size: 20px !important; margin-top: 5px !important; }
    h3 { font-size: 16px !important; font-weight: 600 !important; }
    .stTabs [data-baseweb="tab"] { font-size: 13px !important; padding: 6px 12px !important; }
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

# Título Ejecutivo
st.markdown(f"<h1>📊 Control Maestro ERP — Rol: {rol_simulado.upper()}</h1>", unsafe_allow_html=True)

modulos_validos = []
if rol_simulado in ["administrador", "gerente", "contador", "operador"]:
    modulos_validos.append("REGISTROS DE CAJA")

if modulos_validos:
    modulo_activo = st.radio("Módulos:", modulos_validos, horizontal=True)
    st.markdown("---")
    
    if modulo_activo == "REGISTROS DE CAJA":
        # Bloque de pestañas de trabajo
        tab1, tab2, tab3, tab4 = st.tabs(["📝 Carga de Movimientos", "🔍 Ver Libro Diario", "🛠️ Modificaciones/Ajustes", "📚 Histórico de Cierres"])
        
        with tab1:
            render_carga(rol_simulado, es_consolidado)
        with tab2:
            render_visor(df_mes, mes_sel_nombre, anho_sel)
        with tab3:
            render_edicion(df_mes, rol_simulado, es_consolidado)
        with tab4:
            render_historico(df_completo, rol_simulado)