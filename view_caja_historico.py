# view_caja_historico.py
import streamlit as st
import pandas as pd
from core_finance_engine import procesar_mes_aislado
from db_connection import guardar_cambios_en_disco
from view_caja_visor import preparar_columnas_monto

def render_historico(df_todos, rol_actual):
    st.markdown("### 📚 Reporte e Histórico de Cierres de Mes")
    
    c1, c2 = st.columns(2)
    with c1:
        anho_rep = st.selectbox("Año Consulta", [2026, 2025], key="h_anho")
    with c2:
        meses = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
        mes_rep_nom = st.selectbox("Mes Consulta", list(meses.values()), key="h_mes")
        mes_rep_num = [k for k, v in meses.items() if v == mes_rep_nom][0]

    df_mes, _, saldos_fin = procesar_mes_aislado(df_todos, anho_rep, mes_rep_num)
    
    df_global = st.session_state["df_movimientos"]
    df_global["fecha_dt"] = pd.to_datetime(df_global["fecha"])
    mascara_mes = (df_global["fecha_dt"].dt.year == anho_rep) & (df_global["fecha_dt"].dt.month == mes_rep_num)
    
    estado_consolidado = df_global[mascara_mes]["consolidado"].all() if not df_global[mascara_mes].empty else False
    df_global.drop(columns=["fecha_dt"], inplace=True)

    if estado_consolidado:
        st.success("🔒 **ESTADO PERÍODO: CONSOLIDADO / COMPLETO**")
    else:
        st.warning("🔓 **ESTADO PERÍODO: ABIERTO / EN AUDITORÍA**")

    # --- CORRECCIÓN DE TIPOGRAFÍA DE SALDOS ---
    st.markdown("#### 📊 Cierre de Saldos Disponibles:")
    col_s1, col_s2, col_s3 = st.columns(3)
    col_s1.metric("Disponibilidad Bs", f"Bs {saldos_fin['Bs']:,.2f}")
    col_s2.metric("Disponibilidad Zelle", f"$ {saldos_fin['Ze']:,.2f}")
    col_s3.metric("Disponibilidad Cash", f"$ {saldos_fin['Ch']:,.2f}")

    # --- DESPLEGAR TODOS LOS MOVIMIENTOS EN ESTA VENTANA ---
    st.markdown("#### 📋 Detalle de Movimientos del Período:")
    if not df_mes.empty:
        df_hist_visual = df_mes.copy()
        df_hist_visual = preparar_columnas_monto(df_hist_visual)
        df_hist_visual = df_hist_visual.rename(columns={"detalle": "Descripción", "categoria": "Categoría", "tipo": "Tipo", "comentarios": "Comentario"})
        
        st.dataframe(
            df_hist_visual[["id", "fecha", "Descripción", "Categoría", "Tipo", "Monto Bs", "Monto $ Zelle", "Monto $ Cash", "Comentario"]],
            use_container_width=True,
            hide_index=True,
            height=250
        )
    else:
        st.info("No existen registros operativos en el mes seleccionado.")

    if rol_actual in ["administrador", "gerente"]:
        st.markdown("---")
        if not estado_consolidado:
            if st.button("✅ Consolidar y Bloquear Mes"):
                indices = df_global[mascara_mes].index
                st.session_state["df_movimientos"].loc[indices, "consolidado"] = True
                st.session_state["df_movimientos"].loc[indices, "modificado_por"] = rol_actual
                guardar_cambios_en_disco()
                st.success("Mes cerrado administrativamente.")
                st.rerun()
        else:
            if st.button("🔓 Reabrir Auditoría de este Mes"):
                indices = df_global[mascara_mes].index
                st.session_state["df_movimientos"].loc[indices, "consolidado"] = False
                st.session_state["df_movimientos"].loc[indices, "modificado_por"] = rol_actual
                guardar_cambios_en_disco()
                st.success("El candado se ha retirado. Ahora puedes corregir desde las pestañas de Carga y Modificaciones.")
                st.rerun()