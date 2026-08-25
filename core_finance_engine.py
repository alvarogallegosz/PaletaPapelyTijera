# core_finance_engine.py
import pandas as pd
import datetime
import xml.sax.saxutils

def obtener_saldos_iniciales_dict(df_todos, anho, mes, lista_cuentas=None):
    """
    Calcula el saldo acumulado antes del mes consultado para todas las cuentas activas.
    Devuelve un diccionario dinámico: {'Bs': 0.0, '$Ze': 0.0, '$Ch': 0.0, ...}
    """
    if df_todos.empty:
        return {}
        
    fecha_corte = datetime.date(anho, mes, 1)
    df_anterior = df_todos[(df_todos["fecha"] < fecha_corte) & (df_todos["activo"] == True)]
    
    if lista_cuentas is None:
        # Extraer dinámicamente las cuentas presentes en el dataset
        tipos = df_todos["tipo"].dropna().unique()
        cuentas_set = set()
        for t in tipos:
            if "-" in str(t):
                pref, cta = str(t).split("-", 1)
                if pref in ["IN", "EG"]:
                    cuentas_set.add(cta)
        lista_cuentas = sorted(list(cuentas_set))

    saldos = {}
    for cta in lista_cuentas:
        if df_anterior.empty:
            saldos[cta] = 0.0
        else:
            in_monto = df_anterior[df_anterior["tipo"] == f"IN-{cta}"]["monto"].sum()
            eg_monto = df_anterior[df_anterior["tipo"] == f"EG-{cta}"]["monto"].sum()
            saldos[cta] = float(in_monto - eg_monto)

    return saldos


def obtener_saldo_inicial_mes(df_todos, anho, mes):
    """
    Wrapper compatible con código heredado que devuelve los saldos iniciales como diccionario de claves estándar.
    """
    saldos = obtener_saldos_iniciales_dict(df_todos, anho, mes)
    
    # Normalización de claves comunes para vistas
    return (
        saldos.get("Bs", 0.0),
        saldos.get("$Ze", saldos.get("Ze", 0.0)),
        saldos.get("$Ch", saldos.get("Ch", 0.0)),
        saldos.get("usDT", saldos.get("usDT", 0.0)),
        saldos.get("$AhZe", saldos.get("AhZe", 0.0)),
        saldos.get("$AhCh", saldos.get("AhCh", 0.0)),
        saldos.get("AhDT", saldos.get("AhDT", 0.0))
    )


def procesar_mes_aislado(df_todos, anho, mes, cuentas_ordenadas=None):
    """
    Genera la línea de tiempo financiera de saldos para todas las cuentas activas en el mes seleccionado.
    Construye dinámicamente las columnas de saldos para la tabla.
    """
    df_filtro = df_todos.copy()
    
    # Detectar todas las cuentas en el dataset si no se especifican
    if cuentas_ordenadas is None:
        tipos_unicos = df_filtro["tipo"].dropna().unique() if not df_filtro.empty else []
        cuentas_set = set()
        for t in tipos_unicos:
            if "-" in str(t):
                pref, cta = str(t).split("-", 1)
                if pref in ["IN", "EG"]:
                    cuentas_set.add(cta)
        cuentas_ordenadas = sorted(list(cuentas_set)) if cuentas_set else ["Bs", "$Ze", "$Ch", "$AhZe", "$AhCh"]

    # Diccionario de saldos iniciales
    saldos_iniciales = obtener_saldos_iniciales_dict(df_filtro, anho, mes, lista_cuentas=cuentas_ordenadas)
    saldos_corrientes = saldos_iniciales.copy()

    # Filtrar registros del mes
    if not df_filtro.empty:
        df_filtro["fecha_dt"] = pd.to_datetime(df_filtro["fecha"])
        mascara = (df_filtro["fecha_dt"].dt.year == anho) & (df_filtro["fecha_dt"].dt.month == mes) & (df_filtro["activo"] == True)
        df_mes = df_filtro[mascara].drop(columns=["fecha_dt"]).sort_values(by=["fecha", "id"]).copy()
    else:
        df_mes = pd.DataFrame()

    if df_mes.empty:
        return df_mes, saldos_iniciales, saldos_iniciales

    # Seguimiento acumulativo fila a fila
    historial_saldos = {cta: [] for cta in cuentas_ordenadas}

    for _, row in df_mes.iterrows():
        tipo = str(row["tipo"])
        monto = float(row["monto"]) if pd.notnull(row["monto"]) else 0.0

        if "-" in tipo:
            prefijo, cta = tipo.split("-", 1)
            if cta in saldos_corrientes:
                if prefijo == "IN":
                    saldos_corrientes[cta] += monto
                elif prefijo == "EG":
                    saldos_corrientes[cta] -= monto

        for cta in cuentas_ordenadas:
            historial_saldos[cta].append(saldos_corrientes[cta])

    # Asignación de columnas dinámicas de saldo
    for cta in cuentas_ordenadas:
        df_mes[f"Saldo {cta}"] = historial_saldos[cta]

    saldos_finales = saldos_corrientes.copy()
    return df_mes, saldos_iniciales, saldos_finales


# ===================================================
# 🗓️ HELPER DE FORMATO DE FECHA EN ESPAÑOL
# ===================================================
MESES_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
DIAS_ES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

def fecha_a_larga(f):
    """Convierte una fecha en texto largo en español de forma segura."""
    if not f:
        return datetime.date.today().strftime("%Y-%m-%d")
    if isinstance(f, str):
        try:
            f = datetime.datetime.strptime(f, "%Y-%m-%d").date()
        except ValueError:
            try:
                f = datetime.datetime.strptime(f, "%d/%m/%Y").date()
            except ValueError:
                return str(f).upper()
    if isinstance(f, (datetime.date, datetime.datetime)):
        dia_semana = DIAS_ES[f.weekday()]
        mes = MESES_ES[f.month - 1]
        return f"{dia_semana.upper()} {f.day} DE {mes.upper()} DE {f.year}"
    return str(f).upper()

def limpiar_texto_pdf(texto, valor_por_defecto="N/A"):
    """Sanitiza y prepara cualquier texto para ReportLab evitando errores de sintaxis XML."""
    if not texto:
        return valor_por_defecto
    return xml.sax.saxutils.escape(str(texto).strip().upper())
