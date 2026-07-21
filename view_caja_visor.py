# view_caja_visor.py
import streamlit as st
import pandas as pd

def preparar_columnas_monto(df):
    """Desglosa la columna genérica 'monto' en 5 columnas visuales según el tipo de movimiento."""
    if df.empty:
        for col in ["Monto Bs", "Monto $ Zelle", "Monto $ Cash", "Monto $ Ah-Ze", "Monto $ Ah-Ch"]:
            df[col] = ""
        return df

    def evaluar_monto(row, prefijo_tipo):
        monto_val = float(row["monto"]) if pd.notnull(row["monto"]) else 0.0
        tipo_str = str(row.get("tipo", "")).strip()
        
        if tipo_str == f"IN-{prefijo_tipo}":
            return f"+{monto_val:,.2f}"
        elif tipo_str == f"EG-{prefijo_tipo}":
            return f"-{monto_val:,.2f}"
        return ""

    df["Monto Bs"] = df.apply(lambda r: evaluar_monto(r, "Bs"), axis=1)
    df["Monto $ Zelle"] = df.apply(lambda r: evaluar_monto(r, "$Ze"), axis=1)
    df["Monto $ Cash"] = df.apply(lambda r: evaluar_monto(r, "$Ch"), axis=1)
    df["Monto $ Ah-Ze"] = df.apply(lambda r: evaluar_monto(r, "$AhZe"), axis=1)
    df["Monto $ Ah-Ch"] = df.apply(lambda r: evaluar_monto(r, "$AhCh"), axis=1)
    
    return df


def render_banner_saldos(saldos_dict):
    """Renderiza el bloque HTML superior con la disponibilidad de las 5 cuentas."""
    val_bs = float(saldos_dict.get('Bs', 0.0))
    val_ze = float(saldos_dict.get('Ze', 0.0))
    val_ch = float(saldos_dict.get('Ch', 0.0))
    val_ah_ze = float(saldos_dict.get('AhZe', 0.0))
    val_ah_ch = float(saldos_dict.get('AhCh', 0.0))
    
    st.markdown(f"""
        <div style="font-size: 14px; background-color: #f8f9fa; padding: 10px 14px; border-radius: 6px; border-left: 4px solid #3b82f6; margin-top: 5px; margin-bottom: 8px; line-height: 1.8;">
            <strong>Disponibilidad Neta en Cajas:</strong> <br>
            <span style="color: #111827;">🟢 <b>Bs:</b> {val_bs:,.2f}</span> &nbsp;|&nbsp;
            <span style="color: #111827;">🔵 <b>Zelle Op:</b> ${val_ze:,.2f}</span> &nbsp;|&nbsp;
            <span style="color: #111827;">💵 <b>Cash Op:</b> ${val_ch:,.2f}</span> &nbsp;|&nbsp;
            <span style="color: #0d9488;">🏦 <b>Ahorro Zelle:</b> ${val_ah_ze:,.2f}</span> &nbsp;|&nbsp;
            <span style="color: #0d9488;">🐷 <b>Ahorro Cash:</b> ${val_ah_ch:,.2f}</span>
        </div>
    """, unsafe_allow_html=True)


def calcular_acumulados_filtrados(df):
    """Calcula el flujo neto (Ingresos - Egresos) de las 5 cuentas sobre el conjunto filtrado."""
    acumulados = {'Bs': 0.0, 'Ze': 0.0, 'Ch': 0.0, 'AhZe': 0.0, 'AhCh': 0.0}
    if df.empty:
        return acumulados

    for _, row in df.iterrows():
        try:
            monto_val = float(row["monto"]) if pd.notnull(row["monto"]) else 0.0
        except (ValueError, TypeError):
            monto_val = 0.0
            
        tipo_str = str(row.get("tipo", "")).strip()
        
        if tipo_str == "IN-Bs":
            acumulados['Bs'] += monto_val
        elif tipo_str == "EG-Bs":
            acumulados['Bs'] -= monto_val
        elif tipo_str == "IN-$Ze":
            acumulados['Ze'] += monto_val
        elif tipo_str == "EG-$Ze":
            acumulados['Ze'] -= monto_val
        elif tipo_str == "IN-$Ch":
            acumulados['Ch'] += monto_val
        elif tipo_str == "EG-$Ch":
            acumulados['Ch'] -= monto_val
        elif tipo_str == "IN-$AhZe":
            acumulados['AhZe'] += monto_val
        elif tipo_str == "EG-$AhZe":
            acumulados['AhZe'] -= monto_val
        elif tipo_str == "IN-$AhCh":
            acumulados['AhCh'] += monto_val
        elif tipo_str == "EG-$AhCh":
            acumulados['AhCh'] -= monto_val
            
    return acumulados


def render_banner_acumulados(df_filtrado):
    """Renderiza el bloque secundario con los flujos netos condicionados por los filtros actuales."""
    ac = calcular_acumulados_filtrados(df_filtrado)
    st.markdown(f"""
        <div style="font-size: 13px; background-color: #f0fdf4; padding: 8px 14px; border-radius: 6px; border-left: 4px solid #16a34a; margin-bottom: 12px; line-height: 1.8;">
            <strong>Flujo Neto del Periodo (Acumulado según Filtros):</strong> <br>
            <span style="color: #14532d;">🟢 <b>Bs:</b> {ac['Bs']:,.2f}</span> &nbsp;|&nbsp;
            <span style="color: #14532d;">🔵 <b>Zelle Op:</b> ${ac['Ze']:,.2f}</span> &nbsp;|&nbsp;
            <span style="color: #14532d;">💵 <b>Cash Op:</b> ${ac['Ch']:,.2f}</span> &nbsp;|&nbsp;
            <span style="color: #166534;">🏦 <b>Ahorro Zelle:</b> ${ac['AhZe']:,.2f}</span> &nbsp;|&nbsp;
            <span style="color: #166534;">🐷 <b>Ahorro Cash:</b> ${ac['AhCh']:,.2f}</span>
        </div>
    """, unsafe_allow_html=True)


def render_visor(df_mes, mes_nombre, anho, saldos_fin):
    """Punto de entrada principal invocado por run_app.py."""
    df_filtrado = df_mes.copy()
    
    # --- FILA SUPERIOR PARALELA: SUBTÍTULO + FILTROS ---
    col_title, col_f1, col_f2, col_f3 = st.columns([1.6, 1.3, 1.4, 1.4])
    
    with col_title:
        st.markdown(f"### 🔍 Libro Diario\n*{mes_nombre} {anho}*")
        
    with col_f1:
        df_filtrado["fecha_date"] = pd.to_datetime(df_filtrado["fecha"]).dt.date
        min_f = df_filtrado["fecha_date"].min() if not df_filtrado.empty else pd.Timestamp.now().date()
        max_f = df_filtrado["fecha_date"].max() if not df_filtrado.empty else pd.Timestamp.now().date()
        rango_fecha = st.date_input("Rango Fechas", value=(min_f, max_f), min_value=min_f, max_value=max_f, key="v_date")
        
    with col_f2:
        cats_opts = sorted(df_filtrado["categoria"].unique()) if not df_filtrado.empty else []
        cats_sel = st.multiselect("Filtrar Categoría", options=cats_opts, key="v_cat")
        
    with col_f3:
        tipos_opts = sorted(df_filtrado["tipo"].unique()) if not df_filtrado.empty else []
        tipos_sel = st.multiselect("Filtrar Tipo", options=tipos_opts, key="v_tipo")

    # Aplicación defensiva de filtros
    if isinstance(rango_fecha, tuple) and len(rango_fecha) == 2:
        df_filtrado = df_filtrado[(df_filtrado["fecha_date"] >= rango_fecha[0]) & (df_filtrado["fecha_date"] <= rango_fecha[1])]
    elif isinstance(rango_fecha, tuple) and len(rango_fecha) == 1:
        df_filtrado = df_filtrado[df_filtrado["fecha_date"] == rango_fecha[0]]
        
    if cats_sel:
        df_filtrado = df_filtrado[df_filtrado["categoria"].isin(cats_sel)]
    if tipos_sel:
        df_filtrado = df_filtrado[df_filtrado["tipo"].isin(tipos_sel)]

    # BANNER DE SALDOS DINÁMICOS GLOBALES
    render_banner_saldos(saldos_fin)
    
    # BANNER DE ACUMULADOS NETOS (SUSCEPTIBLES A FILTROS, SIN SALDO INICIAL)
    render_banner_acumulados(df_filtrado)

    if df_filtrado.empty:
        st.info("Ningún registro operativo coincide con la parametrización seleccionada.")
        return

    # Renderizado de la tabla contable
    df_visual = df_filtrado.copy()
    df_visual = preparar_columnas_monto(df_visual)
    df_visual["Fecha Ext"] = pd.to_datetime(df_visual["fecha"]).dt.strftime("%d/%m/%Y")
    df_visual = df_visual.rename(columns={"detalle": "Descripción", "categoria": "Categoría", "tipo": "Tipo", "comentarios": "Comentario"})
    
    st.dataframe(
        df_visual[["Fecha Ext", "Descripción", "Categoría", "Tipo", "Monto Bs", "Monto $ Zelle", "Monto $ Cash", "Monto $ Ah-Ze", "Monto $ Ah-Ch", "Comentario"]],
        column_config={
            "Fecha Ext": st.column_config.TextColumn("Fecha", width=100),
            "Descripción": st.column_config.TextColumn("Descripción", width=300),
            "Categoría": st.column_config.TextColumn("Categoría", width=140),
            "Tipo": st.column_config.TextColumn("Tipo", width=90),
            "Monto Bs": st.column_config.TextColumn("Monto Bs", width=110),
            "Monto $ Zelle": st.column_config.TextColumn("Monto $ Zelle", width=110),
            "Monto $ Cash": st.column_config.TextColumn("Monto $ Cash", width=110),
            "Monto $ Ah-Ze": st.column_config.TextColumn("Monto $ Ah-Ze", width=110),
            "Monto $ Ah-Ch": st.column_config.TextColumn("Monto $ Ah-Ch", width=110),
            "Comentario": st.column_config.TextColumn("Comentario", width=300),
        },
        use_container_width=False,
        hide_index=True,
        height=600
    )
