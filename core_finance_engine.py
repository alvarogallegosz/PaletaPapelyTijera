# core_finance_engine.py
import pandas as pd
import datetime

def obtener_saldo_inicial_mes(df_todos, anho, mes):
    """Calcula vectorialmente el saldo acumulado acumulado de las 3 cajas antes del mes consultado."""
    if df_todos.empty:
        return 0.0, 0.0, 0.0
        
    fecha_corte = datetime.date(anho, mes, 1)
    df_anterior = df_todos[(df_todos["fecha"] < fecha_corte) & (df_todos["activo"] == True)]
    
    if df_anterior.empty:
        return 0.0, 0.0, 0.0
        
    # Sumatorias vectoriales instantáneas por tipo de cuenta
    in_bs = df_anterior[df_anterior["tipo"] == "IN-Bs"]["monto"].sum()
    eg_bs = df_anterior[df_anterior["tipo"] == "EG-Bs"]["monto"].sum()
    
    in_ze = df_anterior[df_anterior["tipo"] == "IN-$Ze"]["monto"].sum()
    eg_ze = df_anterior[df_anterior["tipo"] == "EG-$Ze"]["monto"].sum()
    
    in_ch = df_anterior[df_anterior["tipo"] == "IN-$Ch"]["monto"].sum()
    eg_ch = df_anterior[df_anterior["tipo"] == "EG-$Ch"]["monto"].sum()
    
    return (in_bs - eg_bs), (in_ze - eg_ze), (in_ch - eg_ch)

def procesar_mes_aislado(df_todos, anho, mes):
    """Genera la línea de tiempo financiera de saldos únicamente para el mes seleccionado."""
    s_bs, s_ze, s_ch = obtener_saldo_inicial_mes(df_todos, anho, mes)
    saldos_iniciales = {"Bs": s_bs, "Ze": s_ze, "Ch": s_ch}
    
    df_filtro = df_todos.copy()
    df_filtro["fecha_dt"] = pd.to_datetime(df_filtro["fecha"])
    mascara = (df_filtro["fecha_dt"].dt.year == anho) & (df_filtro["fecha_dt"].dt.month == mes) & (df_filtro["activo"] == True)
    
    df_mes = df_filtro[mascara].drop(columns=["fecha_dt"]).sort_values(by=["fecha", "id"]).copy()
    
    if df_mes.empty:
        return df_mes, saldos_iniciales, saldos_iniciales
        
    lista_bs, lista_ze, lista_ch = [], [], []
    
    for _, row in df_mes.iterrows():
        tipo = row["tipo"]
        monto = float(row["monto"]) if pd.notnull(row["monto"]) else 0.0
        
        if tipo == "IN-Bs": s_bs += monto
        elif tipo == "EG-Bs": s_bs -= monto
        elif tipo == "IN-$Ze": s_ze += monto
        elif tipo == "EG-$Ze": s_ze -= monto
        elif tipo == "IN-$Ch": s_ch += monto
        elif tipo == "EG-$Ch": s_ch -= monto
            
        lista_bs.append(s_bs)
        lista_ze.append(s_ze)
        lista_ch.append(s_ch)
        
    df_mes["Saldo Bs"] = lista_bs
    df_mes["Saldo Zelle ($)"] = lista_ze
    df_mes["Saldo Cash ($)"] = lista_ch
    
    saldos_finales = {"Bs": s_bs, "Ze": s_ze, "Ch": s_ch}
    return df_mes, saldos_iniciales, saldos_finales