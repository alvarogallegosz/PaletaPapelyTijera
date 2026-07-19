# view_caja_visor.py
import streamlit as st
import pandas as pd

def preparar_columnas_monto(df):
    """Segmenta dinámicamente los montos en columnas independientes aplicando el signo matemático."""
    if df.empty:
        df["Monto Bs"] = ""
        df["Monto $ Zelle"] = ""
        df["Monto $ Cash"] = ""
        return df

    def evaluar_monto(row, cuenta_esperada):
        if row["tipo"] == f"IN-{cuenta_esperada}":
            return f"+{row['monto']:,.2f}"
        elif row["tipo"] == f"EG-{cuenta_esperada}":
            return f"-{row['monto']:,.2f}"
        return ""

    df["Monto Bs"] = df.apply(lambda r: evaluar_monto(r, "Bs"), axis=1)
    df["Monto $ Zelle"] = df.apply(lambda r: evaluar_monto(r, "$Ze"), axis=1)
    df["Monto $ Cash"] = df.apply(lambda r: evaluar_monto(r, "$Ch"), axis=1)
    return df

def render_visor(df_mes, mes_nombre, anho, saldos_fin):
    st.markdown(f"### 🔍 Libro de Caja Diario: {mes_nombre} {anho}")
    
    if df_mes.empty:
        st.info("No se registran movimientos activos en este periodo.")
        return

    # --- BANNER DE SALDOS DINÁMICOS SUPERIORES ALINEADOS ---
    st.markdown("#### 💰 Disponibilidad Actual en Cajas")
    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        st.metric(label="Saldo Neto Bs", value=f"Bs {saldos_fin['Bs']:,.2f}")
    with m_col2:
        st.metric(label="Saldo Neto Zelle", value=f"$ {saldos_fin['Ze']:,.2f}")
    with m_col3:
        st.metric(label="Saldo Neto Cash", value=f"$ {saldos_fin['Ch']:,.2f}")
    st.markdown("---")

    # Construcción de la estructura solicitada
    df_visual = df_mes.copy()
    df_visual = preparar_columnas_monto(df_visual)
    
    # Renombrado de etiquetas de visualización requeridas por auditoría
    df_visual = df_visual.rename(columns={"detalle": "Descripción", "categoria": "Categoría", "tipo": "Tipo", "comentarios": "Comentario"})
    
    cols_mostrar = ["id", "fecha", "Descripción", "Categoría", "Tipo", "Monto Bs", "Monto $ Zelle", "Monto $ Cash", "Comentario"]
    
    st.dataframe(
        df_visual[cols_mostrar],
        column_config={
            "id": st.column_config.TextColumn("ID"),
            "fecha": st.column_config.TextColumn("Fecha"),
            "Monto Bs": st.column_config.TextColumn("Monto Bs"),
            "Monto $ Zelle": st.column_config.TextColumn("Monto $ Zelle"),
            "Monto $ Cash": st.column_config.TextColumn("Monto $ Cash"),
        },
        use_container_width=True,
        hide_index=True,
        height=400
    )