# view_caja_historico.py
import streamlit as st
import pandas as pd
from core_finance_engine import procesar_mes_aislado
from db_connection import actualizar_consolidado_mes_db, obtener_movimientos_locales
from view_caja_visor import preparar_columnas_monto

def render_historico(df_todos, rol_actual):
    # --- FILA SUPERIOR PARALELA MÁXIMA ---
    c_title, c_ano, c_mes, c_date, c_cat, c_tipo = st.columns([1.4, 0.7, 0.9, 1.2, 1.2, 1.2])
    
    with c_title:
        st.markdown("### 📚 Histórico\n*Reportes*")
        
    with c_ano:
        anho_rep = st.selectbox("Año", [2026, 2025], key="h_anho")
        
    with c_mes:
        meses = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
        mes_rep_nom = st.selectbox("Mes", list(meses.values()), key="h_mes")
        mes_rep_num = [k for k, v in meses.items() if v == mes_rep_nom][0]

    df_mes, _, saldos_fin = procesar_mes_aislado(df_todos, anho_rep, mes_rep_num)
    df_filtrado = df_mes.copy()

    with c_date:
        df_filtrado["fecha_date"] = pd.to_datetime(df_filtrado["fecha"]).dt.date
        min_f = df_filtrado["fecha_date"].min() if not df_filtrado.empty else pd.Timestamp.now().date()
        max_f = df_filtrado["fecha_date"].max() if not df_filtrado.empty else pd.Timestamp.now().date()
        rango_fecha = st.date_input("Rango Diario", value=(min_f, max_f), min_value=min_f, max_value=max_f, key="h_date")

    with c_cat:
        cats_opts = sorted(df_filtrado["categoria"].unique()) if not df_filtrado.empty else []
        cats_sel = st.multiselect("Categoría", options=cats_opts, key="h_cat")

    with c_tipo:
        tipos_opts = sorted(df_filtrado["tipo"].unique()) if not df_filtrado.empty else []
        tipos_sel = st.multiselect("Tipo Cuenta", options=tipos_opts, key="h_tipo")

    if isinstance(rango_fecha, tuple) and len(rango_fecha) == 2:
        df_filtrado = df_filtrado[(df_filtrado["fecha_date"] >= rango_fecha[0]) & (df_filtrado["fecha_date"] <= rango_fecha[1])]
    elif isinstance(rango_fecha, tuple) and len(rango_fecha) == 1:
        df_filtrado = df_filtrado[df_filtrado["fecha_date"] == rango_fecha[0]]
        
    if cats_sel:
        df_filtrado = df_filtrado[df_filtrado["categoria"].isin(cats_sel)]
    if tipos_sel:
        df_filtrado = df_filtrado[df_filtrado["tipo"].isin(tipos_sel)]

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

    val_bs = float(saldos_fin.get('Bs', 0.0))
    val_ze = float(saldos_fin.get('Ze', 0.0))
    val_ch = float(saldos_fin.get('Ch', 0.0))
    
    st.markdown(f"""
        <div style="font-size: 15px; background-color: #f8f9fa; padding: 8px 12px; border-radius: 6px; border-left: 4px solid #10b981; margin-top: 5px; margin-bottom: 12px; line-height: 1.6;">
            <strong>Cierre de Saldos Disponibles:</strong> &nbsp;&nbsp;&nbsp;&nbsp;
            <span style="color: #111827; white-space: nowrap;">🟢 <b>Bs:</b> {val_bs:,.2f}</span> &nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;&nbsp;
            <span style="color: #111827; white-space: nowrap;">🔵 <b>Zelle:</b> ${val_ze:,.2f}</span> &nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;&nbsp;
            <span style="color: #111827; white-space: nowrap;">💵 <b>Cash:</b> ${val_ch:,.2f}</span>
        </div>
    """, unsafe_allow_html=True)

    if df_filtrado.empty:
        st.info("Ningún registro histórico coincide con los filtros aplicados.")
    else:
        df_hist_visual = df_filtrado.copy()
        df_hist_visual = preparar_columnas_monto(df_hist_visual)
        df_hist_visual["Fecha Ext"] = pd.to_datetime(df_hist_visual["fecha"]).dt.strftime("%d/%m/%Y")
        df_hist_visual = df_hist_visual.rename(columns={"detalle": "Descripción", "categoria": "Categoría", "tipo": "Tipo", "comentarios": "Comentario"})
        
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

    rol_limpio = str(rol_actual).strip().lower()
    if rol_limpio in ["administrador", "gerente"]:
        st.markdown("---")
        indices_mes = df_global[mascara_mes]["id"].tolist()
        
        if not estado_consolidado:
            if st.button("✅ Consolidar y Bloquear Mes Definición"):
                actualizar_consolidado_mes_db(indices_mes, True, rol_actual)
                obtener_movimientos_locales()
                st.success(f"🎉 El período {mes_rep_nom} {anho_rep} ha sido cerrado de forma definitiva.")
                st.rerun()
        else:
            if st.button("🔓 Reabrir Auditoría de este Mes"):
                actualizar_consolidado_mes_db(indices_mes, False, rol_actual)
                obtener_movimientos_locales()
                st.success(f"🔓 El período {mes_rep_nom} {anho_rep} se encuentra abierto nuevamente para modificaciones.")
                st.rerun()
