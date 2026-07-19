import streamlit as st
import pandas as pd

def render_visor(df_mes, saldos_iniciación, saldos_clausura, mes_nombre, anho):
    st.subheader(f"Movimientos del Mes: {mes_nombre} {anho}")
    st.markdown(f"**Arrastre Inicial:** 💵 **${saldos_iniciación['Ch']:,.2f}** Cash | 📱 **${saldos_iniciación['Ze']:,.2f}** Zelle | 🇻🇪 **{saldos_iniciación['Bs']:,.2f}** Bs")
    
    if df_mes.empty:
        st.info("No se registran movimientos activos en este periodo.")
        return

    cols = ["id", "fecha", "detalle", "tipo", "monto", "tasa", "Saldo Zelle ($)", "Saldo Cash ($)", "Saldo Neto ($)", "creado_por"]
    
    col_t, col_l = st.columns([3, 1])
    with col_t:
        sel = st.dataframe(df_mes[cols], use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")
    with col_l:
        st.subheader("💬 Auditoría de Fila")
        if sel and len(sel["selection"]["rows"]) > 0:
            fila = df_mes.iloc[sel["selection"]["rows"][0]]
            st.info(f"**Asiento:** #{fila['id']}\n\n**Concepto:** {fila['detalle']}\n\n**Registrado Por:** {fila['creado_por']}")
            if fila["comentarios"]: st.success(f"**Comentarios:** {fila['comentarios']}")