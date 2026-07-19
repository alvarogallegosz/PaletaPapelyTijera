# view_caja_visor.py
import streamlit as st
import pandas as pd

def render_visor(df_mes, mes_nombre, anho):
    st.markdown(f"### 🔍 Libro de Caja Integrado: {mes_nombre} {anho}")
    
    if df_mes.empty:
        st.info("No se registran movimientos activos en este periodo.")
        return

    df_visual = df_mes.copy()
    df_visual["Monto Formato"] = df_visual["monto"].map(lambda x: f"{x:,.2f}")
    
    ultima_fila = df_visual.iloc[-1]
    
    # Fila de Totales de Cierre para el pie de tabla
    fila_totales = pd.DataFrame([{
        "id": "TOTALES", "fecha": "", "categoria": "",
        "detalle": "--- DISPONIBILIDAD TOTAL EN CAJAS ---", "tipo": "", "Monto Formato": "",
        "Saldo Bs": ultima_fila["Saldo Bs"],
        "Saldo Zelle ($)": ultima_fila["Saldo Zelle ($)"],
        "Saldo Cash ($)": ultima_fila["Saldo Cash ($)"],
        "creado_por": ""
    }])
    
    df_con_totales = pd.concat([df_visual, fila_totales], ignore_index=True)
    cols_mostrar = ["id", "fecha", "categoria", "detalle", "tipo", "Monto Formato", "Saldo Bs", "Saldo Zelle ($)", "Saldo Cash ($)", "creado_por"]
    
    st.dataframe(
        df_con_totales[cols_mostrar],
        column_config={
            "categoria": st.column_config.TextColumn("Categoría"),
            "tipo": st.column_config.TextColumn("Cuenta"),
            "Monto Formato": st.column_config.TextColumn("Monto"),
            "Saldo Bs": st.column_config.NumberColumn("Saldo Bs", format="Bs %.2f"),
            "Saldo Zelle ($)": st.column_config.NumberColumn("Saldo Zelle", format="$%.2f"),
            "Saldo Cash ($)": st.column_config.NumberColumn("Saldo Cash", format="$%.2f"),
        },
        use_container_width=True,
        hide_index=True,
        height=450 
    )