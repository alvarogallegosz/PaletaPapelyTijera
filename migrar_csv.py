# migrar_csv.py
import pandas as pd
import streamlit as st
from supabase import create_client

# 1. Conexión usando tus secretos
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Nombre exacto de tu archivo CSV local
ARCHIVO_CSV = "migrar_data_2026.csv"  # 👈 Cambia esto por el nombre real de tu CSV

def migrar_datos():
    print("⏳ Leyendo y limpiando archivo CSV...")
    df = pd.read_csv(ARCHIVO_CSV)
    
    # Limpieza previa de tipos de datos para PostgreSQL
    if "id" in df.columns:
        df = df.drop(columns=["id"]) # Permitir que Supabase genere IDs limpios si aplica
        
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce").dt.strftime("%Y-%m-%d")
    df["monto"] = pd.to_numeric(df["monto"].astype(str).str.replace(" - ", "0").str.replace(",", "."), errors="coerce").fillna(0.0)
    df["tasa"] = pd.to_numeric(df["tasa"].astype(str).str.replace(" - ", "1.0").str.replace(",", "."), errors="coerce").fillna(1.0)
    
    if "activo" in df.columns:
        df["activo"] = df["activo"].fillna(True).astype(bool)
    else:
        df["activo"] = True
        
    if "consolidado" in df.columns:
        df["consolidado"] = df["consolidado"].fillna(False).astype(bool)
    else:
        df["consolidado"] = False

    df["categoria"] = df["categoria"].fillna("SIN CATEGORIA").astype(str).str.strip().str.upper()
    df["detalle"] = df["detalle"].fillna("").astype(str).str.strip()
    df["comentarios"] = df["comentarios"].fillna("").astype(str).str.strip()

    # Convertir a lista de diccionarios
    registros = df.to_dict(orient="records")
    total = len(registros)
    print(f"📦 Se procesarán {total} registros...")

    # Subida por lotes de 300 en 300 para no saturar la red
    TAMANO_LOTE = 300
    for i in range(0, total, TAMANO_LOTE):
        lote = registros[i : i + TAMANO_LOTE]
        try:
            supabase.table("movimientos").insert(lote).execute()
            print(f"✅ Insertados {min(i + TAMANO_LOTE, total)} de {total} registros...")
        except Exception as e:
            print(f"❌ Error en lote {i}: {e}")
            break

    print("🎉 ¡Migración masiva completada con éxito!")

if __name__ == "__main__":
    migrar_datos()