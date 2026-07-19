# db_connection.py
import streamlit as st
import pandas as pd
import os

RUTA_ARCHIVO = "movimientos_real.csv"

def obtener_movimientos_locales():
    """Carga los datos reales desde el CSV en el Session State con tipado correcto."""
    if "df_movimientos" not in st.session_state:
        if os.path.exists(RUTA_ARCHIVO):
            # Lectura tolerante a eñes, acentos y formato numérico hispano
            df = pd.read_csv(RUTA_ARCHIVO, sep=';', decimal=',', thousands='.', encoding='latin-1')
            
            # Forzar parseo de fechas sin romper por días/meses de un solo dígito
            df["fecha"] = pd.to_datetime(df["fecha"], format="%d/%m/%Y").dt.date
            df["activo"] = df["activo"].astype(bool)
            df["consolidado"] = df["consolidado"].astype(bool)
            df["categoria"] = df["categoria"].fillna("").astype(str)
            
            st.session_state["df_movimientos"] = df
        else:
            # Estructura base si el archivo no existe
            st.session_state["df_movimientos"] = pd.DataFrame(columns=[
                "id", "fecha", "categoria", "detalle", "tipo", "monto", "tasa", 
                "comentarios", "activo", "consolidado", "creado_por", "modificado_por"
            ])
    return st.session_state["df_movimientos"]

def guardar_cambios_en_disco():
    """Guarda el estado actual de session_state directamente en el archivo CSV."""
    df = st.session_state["df_movimientos"].copy()
    # Convertir las fechas a formato string estándar D/M/YYYY antes de guardar
    df["fecha"] = pd.to_datetime(df["fecha"]).dt.strftime("%d/%m/%Y")
    df.to_csv(RUTA_ARCHIVO, sep=';', decimal=',', index=False, encoding='latin-1')

def guardar_movimiento_local(nuevo_registro):
    """Inserta un nuevo registro en la cola del DataFrame y persiste en disco."""
    df = st.session_state["df_movimientos"]
    nuevo_id = int(df["id"].max() + 1) if not df.empty else 1
    nuevo_registro["id"] = nuevo_id
    
    df_nuevo = pd.DataFrame([nuevo_registro])
    st.session_state["df_movimientos"] = pd.concat([df, df_nuevo], ignore_index=True)
    guardar_cambios_en_disco()