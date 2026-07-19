# db_connection.py
import streamlit as st
import pandas as pd
import os

def obtener_movimientos_locales():
    """Carga los datos reales respetando la estructura de punto y coma y formato numérico regional."""
    if "df_movimientos" not in st.session_state:
        ruta_archivo = "movimientos_real.csv"
        if os.path.exists(ruta_archivo):
            # Lectura inteligente: configuramos el delimitador y formato numérico hispano
            df = pd.read_csv(ruta_archivo, sep=';', decimal=',', thousands='.', encoding='latin-1')
            
            # Formato de fecha flexible para soportar días y meses de un solo dígito (Ej: 1/7/2026)
            df["fecha"] = pd.to_datetime(df["fecha"], format="%d/%m/%Y").dt.date
            
            df["activo"] = df["activo"].astype(bool)
            df["consolidado"] = df["consolidado"].astype(bool)
            
            # Tratamiento preventivo para filas sin categoría (como los cierres)
            df["categoria"] = df["categoria"].fillna("")
            
            st.session_state["df_movimientos"] = df
        else:
            # Fallback seguro incluyendo la nueva columna 'categoria'
            st.session_state["df_movimientos"] = pd.DataFrame(columns=[
                "id", "fecha", "detalle", "categoria", "tipo", "monto", "tasa", 
                "comentarios", "activo", "consolidado", "creado_por", "modificado_por"
            ])
    return st.session_state["df_movimientos"]

def guardar_movimiento_local(nuevo_registro):
    df = st.session_state["df_movimientos"]
    nuevo_id = int(df["id"].max() + 1) if not df.empty else 1
    nuevo_registro["id"] = nuevo_id
    nuevo_registro["consolidado"] = False
    st.session_state["df_movimientos"] = pd.concat([df, pd.DataFrame([nuevo_registro])], ignore_index=True)
