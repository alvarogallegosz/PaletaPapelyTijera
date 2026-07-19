# app.py
import streamlit as st
from datetime import datetime
from db_connection import obtener_movimientos_locales
from core_finance_engine import procesar_mes_especifico

# Importaciones de Vistas de la Caja
from view_caja_visor import render_visor
from view_caja_carga import render_carga
from view_caja_historico import render_historico
from view_caja_edicion import render_edicion

# --- ENTOCKADO DE SIMULACIÓN PARA PRUEBAS RÁPIDAS ---
st.sidebar.markdown("### 🛠️ Consola de Simulación")
rol_simulado = st.sidebar.selectbox(
    "Identidad del Sistema (Rol):",
    ["operador", "administrador", "contador", "gerente", "soporte"]
)

# Cargar la data temporal del Session State
df_completo = obtener_movimientos_locales()

# --- SELECTORES DE TIEMPO COMUNES ---
st.sidebar.markdown("---")
st.sidebar.subheader("📅 Filtro Temporal")
meses_nombres = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
anho_sel = st.sidebar.selectbox("Año comercial", [2026, 2025])
mes_sel_nombre = st.sidebar.selectbox("Mes de trabajo", list(meses_nombres.values()), index=datetime.now().month - 1)
mes_sel_num = [k for k, v in meses_nombres.items() if v == mes_sel_nombre][0]

# Procesar la matemática del mes
df_mes, saldos_ini, saldos_fin = procesar_mes_especifico(df_completo, anho_sel, mes_sel_num)

# --- CABECERA DE LA APP ---
st.title("📊 Paleta, Papel y Tijera — ERP")
st.caption(f"Visualizando aplicación con permisos asignados al rol: **{rol_simulado.upper()}**")
st.markdown("---")

# --- CONTROL DE MAPEO DE COLUMNAS (MÓDULOS DE LA IMAGEN) ---
modulos_validos = []

# Validar visibilidad de módulos según la matriz de reglas establecida
if rol_simulado in ["administrador", "gerente", "soporte"]:
    modulos_validos.append("REGISTROS DE CAJA")
if rol_simulado in ["operador", "administrador", "gerente", "soporte"]:
    modulos_validos.append("PRESUPUESTOS")
if rol_simulado in ["contador", "administrador", "gerente", "soporte"]:
    modulos_validos.append("FACTURACION")
if rol_simulado in ["contador", "administrador", "gerente", "soporte"]:
    modulos_validos.append("ADMINISTRACIÓN")
if rol_simulado in ["soporte"]:
    modulos_validos.append("SOPORTE EXCLUSIVO")

if not modulos_validos:
    st.warning("No tienes módulos asignados a tu perfil.")
else:
    modulo_activo = st.radio("Módulos de Sistema disponibles:", modulos_validos, horizontal=True)
    st.markdown("---")

    # --- DESARROLLO MÓDULO 1: REGISTROS DE CAJA ---
    if modulo_activo == "REGISTROS DE CAJA":
        # KPIs en la zona superior del módulo
        col1, col2, col3 = st.columns(3)
        col1.metric("🏁 Saldo Neto USD", f"${saldos_fin['Neto']:,.2f}")
        col2.metric("💵 Caja Efectivo", f"${saldos_fin['Ch']:,.2f}")
        col3.metric("📱 Zelle", f"${saldos_fin['Ze']:,.2f}")
        st.markdown("---")

        # Render de las 4 Sub-Pestañas exactas de la columna 1
        t_visor, t_carga, t_hist, t_edit = st.tabs([
            "Visualización Analítica", "Carga Movimientos", "Reporte Consolidado", "Consola de Edición"
        ])
        
        with t_visor:
            render_visor(df_mes, saldos_ini, saldos_fin, mes_sel_nombre, anho_sel)
        with t_carga:
            render_carga(rol_simulado)
        with t_hist:
            render_historico(df_completo)
        with t_edit:
            render_edicion(df_completo, rol_simulado)

    # --- MARCADORES PARA PRÓXIMAS ETAPAS DE DESARROLLO ---
    elif modulo_activo == "PRESUPUESTOS":
        st.header("🎯 Módulo de Presupuestos (Servicios al Cliente)")
        st.info("Estructura lista para inyectar las subtánbs de Creación, Modificación y Recarga de Plantillas.")
        
    elif modulo_activo == "FACTURACION":
        st.header("🧾 Módulo de Facturación")
        st.info("Estructura lista para Emisión e Impresión según formato.")

    elif modulo_activo == "ADMINISTRACIÓN":
        st.header("🛡️ Administración General")
        st.info("Por definir: Módulos de compras, ventas y conciliación bancaria.")

    elif modulo_activo == "SOPORTE EXCLUSIVO":
        st.header("⚙️ Panel de Soporte Técnico (Auditorías)")
        st.warning("⚠️ POLÍTICA DE PRIVACIDAD: Esta zona es restrictiva para ingenieros de soporte.")
        
        st.subheader("Historial Completo de Eliminaciones (Soft Delete)")
        df_anulados = df_completo[df_completo["activo"] == False]
        if df_anulados.empty:
            st.success("No existen transacciones anuladas en el sistema.")
        else:
            st.dataframe(df_anulados, use_container_width=True, hide_index=True)