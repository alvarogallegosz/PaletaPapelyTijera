# view_caja_historico.py
import streamlit as st
import pandas as pd
from core_finance_engine import procesar_mes_especifico

def render_historico(df_todos, rol_actual):
    st.markdown("### 📚 Reporte Consolidado de Cierres de Mes")
    
    c1, c2 = st.columns(2)
    with c1:
        anho_rep = st.selectbox("Seleccionar Año Consulta", [2026, 2025], key="rep_anho")
    with c2:
        meses_nombres = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
        mes_rep_nom = st.selectbox("Seleccionar Mes Consulta", list(meses_nombres.values()), key="rep_mes")
        mes_rep_num = [k for k, v in meses_nombres.items() if v == mes_rep_nom][0]

    df_mes, _, saldos_fin = procesar_mes_especifico(df_todos, anho_rep, mes_rep_num)
    
    if df_mes.empty:
        st.info("Sin transacciones registradas en este periodo seleccionado.")
        return

    df_general = st.session_state["df_movimientos"]
    mascara_mes = (pd.to_datetime(df_general["fecha"]).dt.year == anho_rep) & (pd.to_datetime(df_general["fecha"]).dt.month == mes_rep_num)
    estado_consolidado = df_general[mascara_mes]["consolidado"].all() if not df_general[mascara_mes].empty else False

    if estado_consolidado:
        st.success("🔒 **ESTADO: CONSOLIDADO Y APROBADO POR GERENCIA**")
    else:
        st.warning("🔓 **ESTADO: FLUJO PENDIENTE DE REVISIÓN**")

    st.markdown("**Detalle Operativo Analítico de la Consulta:**")
    # Mostramos la categoría en la vista previa del cierre histórico
    st.dataframe(df_mes[["id", "fecha", "categoria", "detalle", "tipo", "monto"]], use_container_width=True, hide_index=True, height=220)

    if not estado_consolidado:
        if rol_actual in ["administrador", "gerente"]:
            if st.button("✅ Aprobar Cierre y Consolidar Mes"):
                indices_mes = df_general[mascara_mes].index
                st.session_state["df_movimientos"].loc[indices_mes, "consolidated"] = True
                st.session_state["df_movimientos"].loc[indices_mes, "modificado_por"] = rol_actual
                st.success("El período ha sido cerrado administrativamente de forma exitosa.")
                st.rerun()