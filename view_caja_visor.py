import datetime
import calendar
import pandas as pd
import streamlit as st

from db_connection import obtener_movimientos_locales


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


def render_banner_saldos(saldos_dict, fecha_hasta_str=None):
    """Renderiza el bloque HTML superior con la disponibilidad acumulada hasta la fecha máxima."""
    val_bs = float(saldos_dict.get('Bs', 0.0))
    val_ze = float(saldos_dict.get('Ze', 0.0))
    val_ch = float(saldos_dict.get('Ch', 0.0))
    val_ah_ze = float(saldos_dict.get('AhZe', 0.0))
    val_ah_ch = float(saldos_dict.get('AhCh', 0.0))
    
    texto_fecha = f" hasta el {fecha_hasta_str}" if fecha_hasta_str else ""
    
    st.markdown(f"""
        <div style="font-size: 12px; background-color: #f8f9fa; padding: 10px 14px; border-radius: 6px; border-left: 4px solid #3b82f6; margin-top: 5px; margin-bottom: 8px; line-height: 1.8;">
            <strong>Saldos netos acumulados{texto_fecha}:</strong> <br>
            <span style="color: #111827;">🟢 <b>Bs:</b> {val_bs:,.2f}</span> &nbsp;|&nbsp;
            <span style="color: #111827;">🔵 <b>Zelle Operativo:</b> ${val_ze:,.2f}</span> &nbsp;|&nbsp;
            <span style="color: #111827;">💵 <b>Cash Operativo:</b> ${val_ch:,.2f}</span> &nbsp;|&nbsp;
            <span style="color: #0d9488;">🏦 <b>Ahorro Zelle:</b> ${val_ah_ze:,.2f}</span> &nbsp;|&nbsp;
            <span style="color: #0d9488;">🐷 <b>Ahorro Cash:</b> ${val_ah_ch:,.2f}</span>
        </div>
    """, unsafe_allow_html=True)


def calcular_acumulados_filtrados(df):
    """Calcula el flujo neto (Ingresos - Egresos) de las 5 cuentas sobre el conjunto de datos recibido."""
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
    """Renderiza el bloque secundario con los flujos netos condicionados por los filtros (sin acumulado anterior)."""
    ac = calcular_acumulados_filtrados(df_filtrado)
    st.markdown(f"""
        <div style="font-size: 13px; background-color: #f0fdf4; padding: 8px 14px; border-radius: 6px; border-left: 4px solid #16a34a; margin-bottom: 12px; line-height: 1.8;">
            <strong>Montos del período filtrado (sin acumulado anterior):</strong> <br>
            <span style="color: #14532d;">🟢 <b>Bs:</b> {ac['Bs']:,.2f}</span> &nbsp;|&nbsp;
            <span style="color: #14532d;">🔵 <b>Zelle Op:</b> ${ac['Ze']:,.2f}</span> &nbsp;|&nbsp;
            <span style="color: #14532d;">💵 <b>Cash Op:</b> ${ac['Ch']:,.2f}</span> &nbsp;|&nbsp;
            <span style="color: #166534;">🏦 <b>Ahorro Zelle:</b> ${ac['AhZe']:,.2f}</span> &nbsp;|&nbsp;
            <span style="color: #166534;">🐷 <b>Ahorro Cash:</b> ${ac['AhCh']:,.2f}</span>
        </div>
    """, unsafe_allow_html=True)


def render_visor(df_mes, mes_nombre, anho, saldos_fin, rol_actual=None):
    """Punto de entrada principal invocado por run_app.py."""
    
    # CSS dinámico para asegurar la barra de desplazamiento horizontal
    st.markdown("""
        <style>
            div[data-testid="stDataFrame"] > div {
                overflow-x: auto !important;
            }
        </style>
    """, unsafe_allow_html=True)
    
    # --- EVALUACIÓN RIGUROSA DE PERMISOS DE ROL ---
    rol_detectado = (
        rol_actual 
        or st.session_state.get("rol_actual") 
        or st.session_state.get("rol_simulado") 
        or st.session_state.get("rol") 
        or "administrador"
    )
    es_soporte = (str(rol_detectado).strip().lower() == "soporte")

    # --- OBTENCIÓN DEL HISTÓRICO COMPLETO (MISMO ESQUEMA QUE EN EDICIÓN) ---
    df_completo = st.session_state.get("df_movimientos")
    if df_completo is None or df_completo.empty:
        df_completo = obtener_movimientos_locales()

    df_base = df_completo.copy() if df_completo is not None and not df_completo.empty else df_mes.copy()

    if not df_base.empty:
        df_base["fecha_dt"] = pd.to_datetime(df_base["fecha"])
        df_base["fecha_date"] = df_base["fecha_dt"].dt.date
        if "activo" not in df_base.columns:
            df_base["activo"] = True

    # --- FECHAS PREDETERMINADAS: MES ACTUAL ---
    hoy = datetime.date.today()
    primer_dia_mes = datetime.date(hoy.year, hoy.month, 1)
    _, ultimo_dia_num = calendar.monthrange(hoy.year, hoy.month)
    ultimo_dia_mes = datetime.date(hoy.year, hoy.month, ultimo_dia_num)

    if not df_base.empty:
        min_limite = min(df_base["fecha_date"].min(), primer_dia_mes)
        max_limite = max(df_base["fecha_date"].max(), ultimo_dia_mes)
    else:
        min_limite = primer_dia_mes
        max_limite = ultimo_dia_mes

    # --- FILA SUPERIOR PARALELA: SUBTÍTULO + FILTROS ---
    col_title, col_f1, col_f2, col_f3 = st.columns([1.6, 1.3, 1.4, 1.4])
    
    with col_title:
        st.markdown(f"### 🔍 Libro Diario\n*{mes_nombre} {anho}*")
        
    with col_f1:
        rango_fecha = st.date_input(
            "Rango Fechas",
            value=(primer_dia_mes, ultimo_dia_mes),
            min_value=min_limite,
            max_value=max_limite,
            key="v_date"
        )
        
    with col_f2:
        cats_opts = sorted(df_base["categoria"].dropna().unique()) if not df_base.empty and "categoria" in df_base.columns else []
        cats_sel = st.multiselect("Filtrar Categoría", options=cats_opts, key="v_cat")
        
    with col_f3:
        tipos_opts = sorted(df_base["tipo"].dropna().unique()) if not df_base.empty and "tipo" in df_base.columns else []
        tipos_sel = st.multiselect("Filtrar Tipo", options=tipos_opts, key="v_tipo")

    # --- APLICACIÓN DE RANGOS ---
    fecha_desde = primer_dia_mes
    fecha_hasta = ultimo_dia_mes

    if isinstance(rango_fecha, (list, tuple)):
        if len(rango_fecha) == 2:
            fecha_desde, fecha_hasta = rango_fecha[0], rango_fecha[1]
        elif len(rango_fecha) == 1:
            fecha_desde = fecha_hasta = rango_fecha[0]

    # --- 1. SALDO ACUMULADO REAL (HISTÓRICO HASTA FECHA_HASTA) ---
    df_activos_historicos = df_base[df_base["activo"] == True] if "activo" in df_base.columns else df_base
    df_hasta_max = df_activos_historicos[df_activos_historicos["fecha_date"] <= fecha_hasta]
    
    saldos_hasta_max = calcular_acumulados_filtrados(df_hasta_max)
    fecha_hasta_str = fecha_hasta.strftime("%d/%m/%Y") if fecha_hasta else ""
    render_banner_saldos(saldos_hasta_max, fecha_hasta_str=fecha_hasta_str)

    # --- 2. FILTRADO ESPECÍFICO DEL PERÍODO ---
    df_filtrado = df_activos_historicos[
        (df_activos_historicos["fecha_date"] >= fecha_desde) & 
        (df_activos_historicos["fecha_date"] <= fecha_hasta)
    ]

    if cats_sel and not df_filtrado.empty:
        df_filtrado = df_filtrado[df_filtrado["categoria"].isin(cats_sel)]
    if tipos_sel and not df_filtrado.empty:
        df_filtrado = df_filtrado[df_filtrado["tipo"].isin(tipos_sel)]

    # Flujo neto exclusivo del rango seleccionado
    render_banner_acumulados(df_filtrado)

    if df_filtrado.empty:
        st.info("Ningún registro operativo coincide con la parametrización seleccionada.")
        return

    # --- PREPARACIÓN DE LA TABLA CONTABLE ---
    df_visual = df_filtrado.copy()
    df_visual = preparar_columnas_monto(df_visual)
    df_visual["Fecha Ext"] = pd.to_datetime(df_visual["fecha"]).dt.strftime("%d/%m/%Y")
    
    columnas_activo_detectadas = [c for c in df_visual.columns if c.lower() in ["activo", "activos"]]
    if not es_soporte:
        df_visual = df_visual.drop(columns=columnas_activo_detectadas, errors="ignore")
    else:
        for col_act in columnas_activo_detectadas:
            df_visual = df_visual.rename(columns={col_act: "Activos"})

    df_visual = df_visual.rename(columns={
        "detalle": "Descripción",
        "categoria": "Categoría",
        "tipo": "Tipo",
        "comentarios": "Comentario"
    })
    
    columnas_pantalla = ["Fecha Ext", "Descripción", "Categoría", "Tipo"]
    if es_soporte and "Activos" in df_visual.columns:
        columnas_pantalla.append("Activos")
        
    columnas_pantalla.extend([
        "Monto Bs", "Monto $ Zelle", "Monto $ Cash", "Monto $ Ah-Ze", "Monto $ Ah-Ch", "Comentario"
    ])
    
    cols_existentes = [c for c in columnas_pantalla if c in df_visual.columns]

    config_cols = {
        "Fecha Ext": st.column_config.TextColumn("Fecha", width=100),
        "Descripción": st.column_config.TextColumn("Descripción", width=320),
        "Categoría": st.column_config.TextColumn("Categoría", width=150),
        "Tipo": st.column_config.TextColumn("Tipo", width=100),
        "Activos": st.column_config.TextColumn("Activos", width=120),
        "Monto Bs": st.column_config.TextColumn("Monto Bs", width=120),
        "Monto $ Zelle": st.column_config.TextColumn("Monto $ Zelle", width=120),
        "Monto $ Cash": st.column_config.TextColumn("Monto $ Cash", width=120),
        "Monto $ Ah-Ze": st.column_config.TextColumn("Monto $ Ah-Ze", width=120),
        "Monto $ Ah-Ch": st.column_config.TextColumn("Monto $ Ah-Ch", width=120),
        "Comentario": st.column_config.TextColumn("Comentario", width=320),
    }

    st.dataframe(
        df_visual[cols_existentes],
        column_config={k: v for k, v in config_cols.items() if k in cols_existentes},
        use_container_width=False,
        hide_index=True,
        height=550
    )
