# db_connection.py
import streamlit as st
import pandas as pd
from datetime import date

def obtener_movimientos_locales():
    """Inicializa y retorna el dataset temporal en Session State con campos de auditoría."""
    if "df_movimientos" not in st.session_state:
        # Mock data inicial adaptado con columnas de control
        st.session_state["df_movimientos"] = pd.DataFrame([
            {"id": 1, "fecha": date(2026, 6, 1), "detalle": "Saldo inicial Cash", "tipo": "IN-$Ch", "monto": 2500.00, "tasa": None, "comentarios": "", "activo": True, "creado_por": "sistema", "modificado_por": "sistema"},
            {"id": 2, "fecha": date(2026, 6, 2), "detalle": "Ingreso Zelle por evento", "tipo": "IN-$Ze", "monto": 850.00, "tasa": None, "comentarios": "Aprobado", "activo": True, "creado_por": "gerente", "modificado_por": "gerente"},
            {"id": 3, "fecha": date(2026, 6, 4), "detalle": "Egreso platos Lander (Anulado)", "tipo": "EG-Bs", "monto": 1200.00, "tasa": 40.20, "comentarios": "Error de tipeo en monto", "activo": False, "creado_por": "operador", "modificado_por": "administrador"},
            {"id": 4, "fecha": date(2026, 6, 10), "detalle": "Pago transporte suministros", "tipo": "EG-$Ch", "monto": 150.00, "tasa": None, "comentarios": "", "activo": True, "creado_por": "administrador", "modificado_por": "administrador"}
        ])
    return st.session_state["df_movimientos"]

def guardar_movimiento_local(nuevo_registro):
    """Inserta un registro temporalmente en la memoria del sistema."""
    df = st.session_state["df_movimientos"]
    nuevo_id = int(df["id"].max() + 1) if not df.empty else 1
    nuevo_registro["id"] = nuevo_id
    
    # Insertar al dataframe de sesión
    st.session_state["df_movimientos"] = pd.concat([df, pd.DataFrame([nuevo_registro])], ignore_index=True)