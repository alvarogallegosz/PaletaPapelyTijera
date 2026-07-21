# core_finance_engine.py
import datetime
import pandas as pd


def obtener_saldo_inicial_mes(
    df_todos: pd.DataFrame, anho: int, mes: int
) -> tuple[float, float, float, float, float]:
  """Calcula vectorialmente el saldo acumulado de las 5 cajas antes del mes consultado."""
  if df_todos.empty:
    return 0.0, 0.0, 0.0, 0.0, 0.0

  # Verificar existencia de columnas requeridas
  cols_requeridas = {"fecha", "activo", "tipo", "monto"}
  if not cols_requeridas.issubset(df_todos.columns):
    return 0.0, 0.0, 0.0, 0.0, 0.0

  df = df_todos.copy()

  # Conversión uniforme de fechas a Timestamp de Pandas para comparación segura
  df["fecha_dt"] = pd.to_datetime(df["fecha"], errors="coerce")
  fecha_corte = pd.Timestamp(int(anho), int(mes), 1)

  # Filtro: registros anteriores a la fecha de corte y marcados como activos
  es_activo = df["activo"].fillna(True).astype(bool)
  df_anterior = df[(df["fecha_dt"] < fecha_corte) & es_activo]

  if df_anterior.empty:
    return 0.0, 0.0, 0.0, 0.0, 0.0

  # Asegurar que la columna monto sea numérica
  df_anterior["monto"] = pd.to_numeric(df_anterior["monto"], errors="coerce").fillna(0.0)

  # Sumatorias vectoriales por tipo de cuenta (5 cajas)
  in_bs = df_anterior[df_anterior["tipo"] == "IN-Bs"]["monto"].sum()
  eg_bs = df_anterior[df_anterior["tipo"] == "EG-Bs"]["monto"].sum()

  in_ze = df_anterior[df_anterior["tipo"] == "IN-$Ze"]["monto"].sum()
  eg_ze = df_anterior[df_anterior["tipo"] == "EG-$Ze"]["monto"].sum()

  in_ch = df_anterior[df_anterior["tipo"] == "IN-$Ch"]["monto"].sum()
  eg_ch = df_anterior[df_anterior["tipo"] == "EG-$Ch"]["monto"].sum()

  in_ah_ze = df_anterior[df_anterior["tipo"] == "IN-$AhZe"]["monto"].sum()
  eg_ah_ze = df_anterior[df_anterior["tipo"] == "EG-$AhZe"]["monto"].sum()

  in_ah_ch = df_anterior[df_anterior["tipo"] == "IN-$AhCh"]["monto"].sum()
  eg_ah_ch = df_anterior[df_anterior["tipo"] == "EG-$AhCh"]["monto"].sum()

  return (
      (in_bs - eg_bs),
      (in_ze - eg_ze),
      (in_ch - eg_ch),
      (in_ah_ze - eg_ah_ze),
      (in_ah_ch - eg_ah_ch),
  )


def procesar_mes_aislado(
    df_todos: pd.DataFrame, anho: int, mes: int
) -> tuple[pd.DataFrame, dict[str, float], dict[str, float]]:
  """Genera la línea de tiempo financiera de saldos para las 5 cuentas únicamente en el mes seleccionado."""
  s_bs, s_ze, s_ch, s_ah_ze, s_ah_ch = obtener_saldo_inicial_mes(
      df_todos, anho, mes
  )

  saldos_iniciales = {
      "Bs": s_bs,
      "Ze": s_ze,
      "Ch": s_ch,
      "AhZe": s_ah_ze,
      "AhCh": s_ah_ch,
  }

  if df_todos.empty:
    return pd.DataFrame(), saldos_iniciales, saldos_iniciales

  df_filtro = df_todos.copy()
  df_filtro["fecha_dt"] = pd.to_datetime(df_filtro["fecha"], errors="coerce")

  es_activo = df_filtro["activo"].fillna(True).astype(bool)
  mascara = (
      (df_filtro["fecha_dt"].dt.year == int(anho))
      & (df_filtro["fecha_dt"].dt.month == int(mes))
      & es_activo
  )

  df_mes = (
      df_filtro[mascara]
      .drop(columns=["fecha_dt"], errors="ignore")
      .sort_values(by=["fecha", "id"])
      .copy()
  )

  if df_mes.empty:
    return df_mes, saldos_iniciales, saldos_iniciales

  lista_bs, lista_ze, lista_ch, lista_ah_ze, lista_ah_ch = [], [], [], [], []

  for _, row in df_mes.iterrows():
    tipo = str(row.get("tipo", ""))
    try:
      monto = float(row.get("monto", 0.0)) if pd.notnull(row.get("monto")) else 0.0
    except (ValueError, TypeError):
      monto = 0.0

    if tipo == "IN-Bs":
      s_bs += monto
    elif tipo == "EG-Bs":
      s_bs -= monto
    elif tipo == "IN-$Ze":
      s_ze += monto
    elif tipo == "EG-$Ze":
      s_ze -= monto
    elif tipo == "IN-$Ch":
      s_ch += monto
    elif tipo == "EG-$Ch":
      s_ch -= monto
    elif tipo == "IN-$AhZe":
      s_ah_ze += monto
    elif tipo == "EG-$AhZe":
      s_ah_ze -= monto
    elif tipo == "IN-$AhCh":
      s_ah_ch += monto
    elif tipo == "EG-$AhCh":
      s_ah_ch -= monto

    lista_bs.append(s_bs)
    lista_ze.append(s_ze)
    lista_ch.append(s_ch)
    lista_ah_ze.append(s_ah_ze)
    lista_ah_ch.append(s_ah_ch)

  df_mes["Saldo Bs"] = lista_bs
  df_mes["Saldo Zelle ($)"] = lista_ze
  df_mes["Saldo Cash ($)"] = lista_ch
  df_mes["Saldo Ah-Zelle ($)"] = lista_ah_ze
  df_mes["Saldo Ah-Cash ($)"] = lista_ah_ch

  saldos_finales = {
      "Bs": s_bs,
      "Ze": s_ze,
      "Ch": s_ch,
      "AhZe": s_ah_ze,
      "AhCh": s_ah_ch,
  }

  return df_mes, saldos_iniciales, saldos_finales