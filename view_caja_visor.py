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

        if row["tipo"] == f"IN-{cuenta_esperada}":
            return f"+{monto_val:,.2f}"
        elif row["tipo"] == f"EG-{cuenta_esperada}":
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

    # --- FILA DE SALDOS COMPACTOS ALINEADOS EXACTAMENTE CON SUS COLUMNAS ---
    # Configuración de proporciones idénticas a los anchos de la tabla
    # Columnas: Fecha(100px), Descripción(320px), Categoría(160px), Tipo(90px), MontoBs(140px), Zelle(140px), Cash(140px), Comentario(320px)
    cols_alineacion = st.columns([100, 320, 160, 90, 140, 140, 140, 320])
    
    val_bs = float(saldos_fin.get('Bs', 0.0))
    val_ze = float(saldos_fin.get('Ze', 0.0))
    val_ch = float(saldos_fin.get('Ch', 0.0))

    with cols_alineacion[4]: # Encima de Monto Bs
        st.markdown(f"<div class='contenedor-saldo'><p class='saldo-lbl'>Saldo Bs</p><p class='saldo-val'>{val_bs:,.2f}</p></div>", unsafe_allow_html=True)
    with cols_alineacion[5]: # Encima de Monto $ Zelle
        st.markdown(f"<div class='contenedor-saldo'><p class='saldo-lbl'>Saldo Zelle</p><p class='saldo-val'>${val_ze:,.2f}</p></div>", unsafe_allow_html=True)
    with cols_alineacion[6]: # Encima de Monto $ Cash
        st.markdown(f"<div class='contenedor-saldo'><p class='saldo-lbl'>Saldo Cash</p><p class='saldo-val'>${val_ch:,.2f}</p></div>", unsafe_allow_html=True)
    
    st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)

    # Preparar visualización limpia
    df_visual = df_mes.copy()
    df_visual = preparar_columnas_monto(df_visual)
    
    # 🛡️ Corrección de Fecha: Forzar formato String estricto DD/MM/YYYY para evitar herencias numéricas de Pandas
    df_visual["Fecha Ext"] = pd.to_datetime(df_visual["fecha"]).dt.strftime("%d/%m/%Y")
    
    df_visual = df_visual.rename(columns={"detalle": "Descripción", "categoria": "Categoría", "tipo": "Tipo", "comentarios": "Comentario"})
    
    # Se elimina por completo el ID del orden visual expuesto
    cols_mostrar = ["Fecha Ext", "Descripción", "Categoría", "Tipo", "Monto Bs", "Monto $ Zelle", "Monto $ Cash", "Comentario"]
    
    st.dataframe(
        df_visual[cols_mostrar],
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
        use_container_width=False, # Mantiene los anchos fijos estrictos forzando el scrollbar nativo si sale de pantalla
        hide_index=True,
        height=380
    )