# view_caja_visor.py
import streamlit as st
import pandas as pd

def preparar_columnas_monto(df):
    if df.empty:
        df["Monto Bs"] = ""
        df["Monto $ Zelle"] = ""
        df["Monto $ Cash"] = ""
        return df

    def evaluar_monto(row, cuenta_esperada):
        try:
            monto_val = float(row["monto"]) if pd.notnull(row["monto"]) else 0.0
        except (ValueError, TypeError):
            monto_val = 0.0

        if str(row.get("tipo", "")).strip() == f"IN-{cuenta_esperada}":
            return f"+{monto_val:,.2f}"
        elif str(row.get("tipo", "")).strip() == f"EG-{cuenta_esperada}":
            return f"-{monto_val:,.2f}"
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

    # --- BANNER DE TEXTO SEGURO (INMUNE A DEFORMACIONES POR PANTALLA VERTICAL) ---
    val_bs = float(saldos_fin.get('Bs', 0.0))
    val_ze = float(saldos_fin.get('Ze', 0.0))
    val_ch = float(saldos_fin.get('Ch', 0.0))
    
    st.markdown(f"""
        <div style="font-size: 15px; background-color: #f8f9fa; padding: 8px 12px; border-radius: 6px; border-left: 4px solid #3b82f6; margin-bottom: 10px; line-height: 1.6;">
            <strong>Disponibilidad Neta en Cajas:</strong> &nbsp;&nbsp;&nbsp;&nbsp;
            <span style="color: #111827; white-space: nowrap;">🟢 <b>Bs:</b> {val_bs:,.2f}</span> &nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;&nbsp;
            <span style="color: #111827; white-space: nowrap;">🔵 <b>Zelle:</b> ${val_ze:,.2f}</span> &nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;&nbsp;
            <span style="color: #111827; white-space: nowrap;">💵 <b>Cash:</b> ${val_ch:,.2f}</span>
        </div>
    """, unsafe_allow_html=True)

    df_visual = df_mes.copy()
    df_visual = preparar_columnas_monto(df_visual)
    
    # Formateo ultra-seguro de fecha string para evitar fallos de visualización
    try:
        df_visual["Fecha Ext"] = pd.to_datetime(df_visual["fecha"]).dt.strftime("%d/%m/%Y")
    except Exception:
        df_visual["Fecha Ext"] = df_visual["fecha"].astype(str)
    
    df_visual = df_visual.rename(columns={"detalle": "Descripción", "categoria": "Categoría", "tipo": "Tipo", "comentarios": "Comentario"})
    
    # Exclusión definitiva de la columna ID
    cols_mostrar = ["Fecha Ext", "Descripción", "Categoría", "Tipo", "Monto Bs", "Monto $ Zelle", "Monto $ Cash", "Comentario"]
    
    st.dataframe(
        df_visual[cols_mostrar],
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
        use_container_width=False, # Habilita scrollbar horizontal si el ancho de la pantalla disminuye
        hide_index=True,
        height=600 # Ajustado para mostrar ~20 filas de forma continua
    )