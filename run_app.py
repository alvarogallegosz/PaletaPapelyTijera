# app.py
import streamlit as st
from datetime import datetime
from db_connection import obtener_movimientos_locales
from core_finance_engine import procesar_mes_especifico

from view_caja_carga import render_carga
from view_caja_visor import render_visor
from view_caja_historico import render_historico
from view_caja_edicion import render_edicion

# Reducción global del tamaño de letra de títulos nativos de Streamlit vía CSS inyectado
st.markdown("""
    <style>
    h1 { font-size: 24px !important; font-weight: 700 !important; margin-bottom: 5px !important; }
    h2 { font-size: 20px !important; margin-top: 5px !important; }
    h3 { font-size: 16px !important; font-weight: 600 !important; color: #333; }
    .stTabs [data-baseweb="tab"] { font-size: 13px !important; padding: 6px 12px !important; }
    </style>
""", unsafe_html=True)

st.sidebar.markdown("### 🛠️ Entorno de Desarrollo")
rol_simulado = st.sidebar.selectbox("Rol Activo:", ["administrador", "gerente", "contador", "operador", "soporte"])

df_completo = obtener_movimientos_locales()

st.sidebar.markdown("---")
st.sidebar.subheader("📅 Filtro Global Temporal")
meses_nombres = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
anho_sel = st.sidebar.selectbox("Año", [2026, 2025])
mes_sel_nombre = st.sidebar.selectbox("Mes", list(meses_nombres.values()), index=datetime.now().month - 1)
mes_sel_num = [k for k, v in meses_nombres.items() if v == mes_sel_nombre][0]

df_mes, saldos_ini, saldos_fin = procesar_mes_especifico(df_completo, anho_sel, mes_sel_num)

# Título Ejecutivo Compacto
st.markdown(f"<h1>📊 Control Maestro ERP — Rol: {rol_simulado.upper()}</h1>", unsafe_html=True)

modulos_validos = []
if rol_simulado in ["administrador", "gerente", "soporte"]: modulos_validos.append("REGISTROS DE CAJA")
if rol_simulado in ["operador", "administrador", "gerente", "soporte"]: modulos_validos.append("PRESUPUESTOS")
if rol_simulado in ["contador", "administrador", "gerente", "soporte"]: modulos_validos.append("FACTURACION")
if rol_simulado in ["contador", "administrador", "gerente", "soporte"]: modulos_validos.append("ADMINISTRACIÓN")
if rol_simulado in ["soporte"]: modulos_validos.append("SOPORTE")

if modulos_validos:
    modulo_activo = st.radio("Módulos:", modulos_validos, horizontal=True)
    st.markdown("---")

    if modulo_activo == "REGISTROS DE CAJA":
        # Totales expresados SOBRE los encabezados de pestañas
        col1, col2, col3 = st.columns(3)
        col1.metric("🏁 SALDO NETO USD", f"${saldos_fin['Neto']:,.2f}", f"${saldos_fin['Neto'] - saldos_ini['Neto']:,.2f} flujo")
        col2.metric("💵 EFECTIVO CASH", f"${saldos_fin['Ch']:,.2f}")
        col3.metric("📱 DIGITAL ZELLE", f"${saldos_fin['Ze']:,.2f}")
        
        st.markdown("---")

        # NUEVO ORDEN SOLICITADO DE SUBPESTAÑAS
        t_carga, t_visor, t_hist, t_edit = st.tabs([
            "📝 Cargar Nueva Operación", 
            "🔍 Libro de Caja del Mes", 
            "📚 Reporte Consolidado de Cierres", 
            "⚙️ Consola de Edición"
        ])
        
        with t_carga:
            render_carga(rol_simulado)
        with t_visor:
            render_visor(df_mes, saldos_ini, saldos_fin, mes_sel_nombre, anho_sel)
        with t_hist:
            render_historico(df_completo, rol_simulado)
        with t_edit:
            render_edicion(df_completo, rol_simulado)
            
    elif modulo_activo == "SOPORTE":
        st.markdown("### ⚙️ Panel Técnico (Auditoría Soft Delete)")
        df_anulados = df_completo[df_completo["activo"] == False]
        st.dataframe(df_anulados, use_container_width=True, hide_index=True)