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

    # Procesamiento financiero aislado
    df_mes, _, saldos_fin = procesar_mes_aislado(df_todos, anho_rep, mes_rep_num)
    
    # Re-evaluación defensiva del candado de consolidación
    df_global = st.session_state["df_movimientos"].copy()
    df_global["fecha_dt"] = pd.to_datetime(df_global["fecha"], errors="coerce")
    mascara_mes = (df_global["fecha_dt"].dt.year == anho_rep) & (df_global["fecha_dt"].dt.month == mes_rep_num)
    
    estado_consolidado = False
    if not df_global[mascara_mes].empty:
        estado_consolidado = df_global[mascara_mes]["consolidado"].all()

    if estado_consolidado:
        st.success("🔒 **ESTADO PERÍODO: CONSOLIDADO / COMPLETO**")
    else:
        st.warning("🔓 **ESTADO PERÍODO: ABIERTO / EN AUDITORÍA**")

    # --- BANNER DE SALDOS DE CIERRE SEGURO ---
    val_bs = float(saldos_fin.get('Bs', 0.0))
    val_ze = float(saldos_fin.get('Ze', 0.0))
    val_ch = float(saldos_fin.get('Ch', 0.0))
    
    st.markdown(f"""
        <div style="font-size: 15px; background-color: #f8f9fa; padding: 8px 12px; border-radius: 6px; border-left: 4px solid #10b981; margin-bottom: 12px; line-height: 1.6;">
            <strong>Cierre de Saldos Disponibles:</strong> &nbsp;&nbsp;&nbsp;&nbsp;
            <span style="color: #111827; white-space: nowrap;">🟢 <b>Bs:</b> {val_bs:,.2f}</span> &nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;&nbsp;
            <span style="color: #111827; white-space: nowrap;">🔵 <b>Zelle:</b> ${val_ze:,.2f}</span> &nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;&nbsp;
            <span style="color: #111827; white-space: nowrap;">💵 <b>Cash:</b> ${val_ch:,.2f}</span>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("#### 📋 Detalle de Movimientos del Período:")
    
    if not df_mes.empty:
        df_hist_visual = df_mes.copy()
        df_hist_visual = preparar_columnas_monto(df_hist_visual)
        
        try:
            df_hist_visual["Fecha Ext"] = pd.to_datetime(df_hist_visual["fecha"]).dt.strftime("%d/%m/%Y")
        except Exception:
            df_hist_visual["Fecha Ext"] = df_hist_visual["fecha"].astype(str)
            
        df_hist_visual = df_hist_visual.rename(columns={"detalle": "Descripción", "categoria": "Categoría", "tipo": "Tipo", "comentarios": "Comentario"})
        
        # Tabla extendida a 20 filas sin ID expuesto
        st.dataframe(
            df_hist_visual[["Fecha Ext", "Descripción", "Categoría", "Tipo", "Monto Bs", "Monto $ Zelle", "Monto $ Cash", "Comentario"]],
            column_config={
                "Fecha Ext": st.column_config.TextColumn("Fecha", width=100),
                "Descripción": st.column_config.TextColumn("Descripción", width=340),
                "Categoría": st.column_config.TextColumn("Categoría", width=160),
                "Tipo": st.column_config.TextColumn("Tipo", width=90),
                "Monto Bs": st.column_config.TextColumn("Monto Bs", width=130),
                "Monto $ Zelle": st.column_config.TextColumn("Monto $ Zelle", width=130),
                "Monto $ Cash": st.column_config.TextColumn("Monto $ Cash", width=130),
                "Comentario": st.column_config.TextColumn("Comentario", width=340),
            },
            use_container_width=False,
            hide_index=True,
            height=600
        )
    else:
        st.info("No existen registros operativos en el mes seleccionado.")

    # --- PANEL UNIFICADO DE BOTONES DE CONTROL (CONTABILIDAD / GERENCIA) ---
    # Convertimos los roles a minúsculas para evitar rechazos por variaciones de caja de texto
    rol_limpio = str(rol_actual).strip().lower()
    if rol_limpio in ["administrador", "gerente"]:
        st.markdown("---")
        if not estado_consolidado:
            if st.button("✅ Consolidar y Bloquear Mes Definición"):
                df_maestro = st.session_state["df_movimientos"]
                df_maestro["fecha_dt"] = pd.to_datetime(df_maestro["fecha"], errors="coerce")
                indices = df_maestro[(df_maestro["fecha_dt"].dt.year == anho_rep) & (df_maestro["fecha_dt"].dt.month == mes_rep_num)].index
                
                st.session_state["df_movimientos"].loc[indices, "consolidado"] = True
                st.session_state["df_movimientos"].loc[indices, "modificado_por"] = rol_actual
                guardar_cambios_en_disco()
                st.success(f"🎉 El período {mes_rep_nom} {anho_rep} ha sido cerrado de forma definitiva.")
                st.rerun()
        else:
            if st.button("🔓 Reabrir Auditoría de este Mes"):
                df_maestro = st.session_state["df_movimientos"]
                df_maestro["fecha_dt"] = pd.to_datetime(df_maestro["fecha"], errors="coerce")
                indices = df_maestro[(df_maestro["fecha_dt"].dt.year == anho_rep) & (df_maestro["fecha_dt"].dt.month == mes_rep_num)].index
                
                st.session_state["df_movimientos"].loc[indices, "consolidado"] = False
                st.session_state["df_movimientos"].loc[indices, "modificado_por"] = rol_actual
                guardar_cambios_en_disco()
                st.success(f"🔓 El período {mes_rep_nom} {anho_rep} se encuentra abierto nuevamente para modificaciones.")
                st.rerun()