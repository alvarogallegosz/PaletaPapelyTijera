# core_finance_engine.py
import pandas as pd
from datetime import date

def procesar_mes_especifico(df, anio, mes):
    if df.empty:
        return pd.DataFrame(), {k: 0.0 for k in ['Bs', 'Ze', 'Ch', 'Neto']}, {k: 0.0 for k in ['Bs', 'Ze', 'Ch', 'Neto']}
    
    # POLÍTICA DE BORRADO SUAVE: El motor financiero solo calcula sobre registros activos
    df_activos = df[df["activo"] == True].copy()
    
    if df_activos.empty:
        return pd.DataFrame(), {k: 0.0 for k in ['Bs', 'Ze', 'Ch', 'Neto']}, {k: 0.0 for k in ['Bs', 'Ze', 'Ch', 'Neto']}

    df_activos = df_activos.sort_values(by=["fecha", "id"]).reset_index(drop=True)
    fecha_inicio_mes = date(anio, mes, 1)
    
    # 1. Calcular Saldo Inicial Histórico
    df_anterior = df_activos[df_activos["fecha"] < fecha_inicio_mes]
    init_bs = sum(df_anterior[df_anterior["tipo"] == "IN-Bs"]["monto"]) - sum(df_anterior[df_anterior["tipo"] == "EG-Bs"]["monto"])
    init_ze = sum(df_anterior[df_anterior["tipo"] == "IN-$Ze"]["monto"]) - sum(df_anterior[df_anterior["tipo"] == "EG-$Ze"]["monto"])
    init_ch = sum(df_anterior[df_anterior["tipo"] == "IN-$Ch"]["monto"]) - sum(df_anterior[df_anterior["tipo"] == "EG-$Ch"]["monto"])
    
    tasa_ref = df_anterior[df_anterior["tasa"].notnull()]["tasa"].last_valid_index()
    ultima_tasa = df_anterior.loc[tasa_ref]["tasa"] if tasa_ref is not None else 40.0
    init_bs_usd = (init_bs / ultima_tasa) if init_bs > 0 else 0.0
    saldos_iniciales = {'Bs': init_bs, 'Ze': init_ze, 'Ch': init_ch, 'Neto': init_bs_usd + init_ze + init_ch}
    
    # 2. Filtrar Mes Solicitado
    df_mes = df_activos[(df_activos["fecha"] >= fecha_inicio_mes) & (df_activos["fecha"].apply(lambda x: x.year == anio and x.month == mes))].copy()
    
    # 3. Flujo Acumulado
    saldos_bs, saldos_ze, saldos_ch, saldos_netos = [], [], [], []
    ac_bs, ac_ze, ac_ch, ac_bs_usd = init_bs, init_ze, init_ch, init_bs_usd
    
    for _, fila in df_mes.iterrows():
        t = fila["tipo"]
        m = float(fila["monto"] or 0.0)
        tasa = float(fila["tasa"] or 1.0) if fila["tasa"] else ultima_tasa
        
        if t == "IN-Bs": ac_bs += m; ac_bs_usd += (m / tasa)
        elif t == "EG-Bs": ac_bs -= m; ac_bs_usd -= (m / tasa)
        elif t == "IN-$Ze": ac_ze += m
        elif t == "EG-$Ze": ac_ze -= m
        elif t == "IN-$Ch": ac_ch += m
        elif t == "EG-$Ch": ac_ch -= m
            
        saldos_bs.append(ac_bs)
        saldos_ze.append(ac_ze)
        saldos_ch.append(ac_ch)
        saldos_netos.append(ac_bs_usd + ac_ze + ac_ch)
        
    df_mes["Saldo Bs"] = saldos_bs
    df_mes["Saldo Zelle ($)"] = saldos_ze
    df_mes["Saldo Cash ($)"] = saldos_ch
    df_mes["Saldo Neto ($)"] = saldos_netos
    
    saldos_finales = {'Bs': ac_bs, 'Ze': ac_ze, 'Ch': ac_ch, 'Neto': ac_bs_usd + ac_ze + ac_ch}
    return df_mes, saldos_iniciales, saldos_finales

def generar_historico(df):
    if df.empty: return pd.DataFrame()
    df_activos = df[df["activo"] == True].copy()
    if df_activos.empty: return pd.DataFrame()
    
    df_activos["periodo"] = pd.to_datetime(df_activos["fecha"]).dt.to_period("M")
    periodos = sorted(df_activos["periodo"].unique())
    
    resumen = []
    for p in periodos:
        _, _, finales = procesar_mes_especifico(df_activos, p.year, p.month)
        resumen.append({
            "Mes / Período": str(p),
            "Cierre Bs": f"{finales['Bs']:,.2f}",
            "Cierre Zelle ($)": finales['Ze'],
            "Cierre Cash ($)": finales['Ch'],
            "Total Consolidado ($)": finales['Neto']
        })
    return pd.DataFrame(resumen)