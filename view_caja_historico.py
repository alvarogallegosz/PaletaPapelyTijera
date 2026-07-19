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

    # --- FILA DE SALDOS COMPACTOS CORREGIDOS ---
    cols_alineacion = st.columns([100, 320, 160, 90, 140, 140, 140, 320])
    
    val_bs = float(saldos_fin.get('Bs', 0.0))
    val_ze = float(saldos_fin.get('Ze', 0.0))
    val_ch = float(saldos_fin.get('Ch', 0.0))

    with cols_alineacion[4]:
        st.markdown(f"<div class='contenedor-saldo'><p class='saldo-lbl'>Cierre Bs</p><p class='saldo-val'>{val_bs:,.2f}</p></div>", unsafe_allow_html=True)
    with cols_alineacion[5]:
        st.markdown(f"<div class='contenedor-saldo'><p class='saldo-lbl'>Cierre Zelle</p><p class='saldo-val'>${val_ze:,.2f}</p></div>", unsafe_allow_html=True)
    with cols_alineacion[6]:
        st.markdown(f"<div class='contenedor-saldo'><p class='saldo-lbl'>Cierre Cash</p><p class='saldo-val'>${val_ch:,.2f}</p></div>", unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

    if not df_mes.empty:
        df_hist_visual = df_mes.copy()
        df_hist_visual = preparar_columnas_monto(df_hist_visual)
        
        # Corrección estricta de string de fecha
        df_hist_visual["Fecha Ext"] = pd.to_datetime(df_hist_visual["fecha"]).dt.strftime("%d/%m/%Y")
        df_hist_visual = df_hist_visual.rename(columns={"detalle": "Descripción", "categoria": "Categoría", "tipo": "Tipo", "comentarios": "Comentario"})
        
        st.dataframe(
            df_hist_visual[["Fecha Ext", "Descripción", "Categoría", "Tipo", "Monto Bs", "Monto $ Zelle", "Monto $ Cash", "Comentario"]],
            column_config={
                "Fecha Ext": st.column_config.TextColumn("Fecha", width=100),
                "Descripción": st.column_config.TextColumn("Descripción", width=320),
                "Categoría": st.column_config.TextColumn("Categoría", width=160),
                "Tipo": st.column_config.TextColumn("Tipo", width=90),
                "Monto Bs": st.column_config.TextColumn("Monto Bs", width=140),
                "Monto $ Zelle": st.column_config.TextColumn("Monto $ Zelle", width=140),
                "Monto $ Cash": st.column_config.TextColumn("Monto $ Cash", width=140),
                "Comentario": st.column_config.TextColumn("Comentario", width=320),
            },
            use_container_width=False,
            hide_index=True,
            height=280
        )
    else:
        st.info("No existen registros operativos en el mes seleccionado.")

    # ... Resto del código de botones de cerrado/apertura idéntico ...