# view_caja_visor.py
import streamlit as st
import pandas as pd

def render_visor(df_mes, saldos_iniciación, saldos_clausura, mes_nombre, anho):
    st.markdown(f"### 🔍 Libro de Caja: {mes_nombre} {anho}")
    
    if df_mes.empty:
        st.info("No se registran movimientos activos en este periodo.")
        return

    df_visual = df_mes.copy()
    df_visual["Monto Formato"] = df_visual["monto"].map(lambda x: f"{x:,.2f}")
    
    # Agregamos la columna 'categoria' vacía en la fila de cierre
    fila_totales = pd.DataFrame([{
        "id": "TOTALES",
        "fecha": "",
        "categoria": "",
        "detalle": "--- CIERRE CONSOLIDADO DEL MES ---",
        "tipo": "",
        "Monto Formato": "",
        "Saldo Zelle ($)": saldos_clausura['Ze'],
        "Saldo Cash ($)": saldos_clausura['Ch'],
        "Saldo Neto ($)": saldos_clausura['Neto'],
        "creado_por": ""
    }])
    
    df_con_totales = pd.concat([df_visual, fila_totales], ignore_index=True)
    
    # Incluimos 'categoria' en el orden de visualización de las columnas
    cols_mostrar = ["id", "fecha", "categoria", "detalle", "tipo", "Monto Formato", "Saldo Zelle ($)", "Saldo Cash ($)", "Saldo Neto ($)", "creado_por"]
    
    st.dataframe(
        df_con_totales[cols_mostrar],
        column_config={
            "categoria": st.column_config.TextColumn("Categoría"),
            "Saldo Zelle ($)": st.column_config.NumberColumn(format="$%.2f"),
            "Saldo Cash ($)": st.column_config.NumberColumn(format="$%.2f"),
            "Saldo Neto ($)": st.column_config.NumberColumn(format="$%.2f"),
        },
        use_container_width=True,
        hide_index=True,
        height=420 
    )