import streamlit as st
from core_finance_engine import generar_historico

def render_historico(df_todos):
    st.subheader("Reporte Consolidado Histórico")
    df_historial = generar_historico(df_todos)
    
    if df_historial.empty:
        st.info("Sin registros suficientes.")
        return

    st.dataframe(
        df_historial,
        column_config={
            "Cierre Zelle ($)": st.column_config.NumberColumn(format="$%.2f"),
            "Cierre Cash ($)": st.column_config.NumberColumn(format="$%.2f"),
            "Total Consolidado ($)": st.column_config.NumberColumn(format="$%.2f"),
        },
        use_container_width=True, hide_index=True
    )