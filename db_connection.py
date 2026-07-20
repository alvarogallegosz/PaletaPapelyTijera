import streamlit as st
import pandas as pd
from supabase import create_client, Client

@st.cache_resource
def init_supabase() -> Client:
    """Inicializa el cliente de Supabase leyendo st.secrets (soportando minúsculas y mayúsculas)."""
    supabase_secrets = st.secrets["supabase"]
    url = supabase_secrets.get("url") or supabase_secrets.get("SUPABASE_URL")
    key = supabase_secrets.get("key") or supabase_secrets.get("SUPABASE_KEY")
    return create_client(url, key)

def obtener_movimientos_locales():
    """Consulta los movimientos en tiempo real desde Supabase y los procesa para Streamlit."""
    try:
        supabase = init_supabase()
        response = supabase.table("movimientos").select("*").order("fecha", desc=False).order("id", desc=False).execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            
            # Formateo y tipado estricto
            df["fecha"] = pd.to_datetime(df["fecha"]).dt.date
            df["activo"] = df["activo"].fillna(True).astype(bool) if "activo" in df.columns else True
            df["consolidado"] = df["consolidado"].fillna(False).astype(bool) if "consolidado" in df.columns else False
            df["categoria"] = df["categoria"].fillna("GENERAL").astype(str) if "categoria" in df.columns else "GENERAL"
            df["detalle"] = df["detalle"].fillna("").astype(str)
            df["comentarios"] = df["comentarios"].fillna("").astype(str)
            
            df["monto"] = pd.to_numeric(df["monto"], errors="coerce").fillna(0.0).astype(float)
            df["tasa"] = pd.to_numeric(df["tasa"], errors="coerce").fillna(1.0).astype(float)
            
            # Garantizar columnas obligatorias de auditoría
            for col in ["activo", "consolidado", "categoria", "creado_por", "modificado_por"]:
                if col not in df.columns:
                    df[col] = "sistema" if "por" in col else ("GENERAL" if col == "categoria" else False)
            
            st.session_state["df_movimientos"] = df
        else:
            st.session_state["df_movimientos"] = pd.DataFrame(columns=[
                "id", "fecha", "categoria", "detalle", "tipo", "monto", "tasa", 
                "comentarios", "activo", "consolidado", "creado_por", "modificado_por"
            ])
    except Exception as e:
        st.error(f"⚠️ Error al conectar con Supabase: {e}")
        if "df_movimientos" not in st.session_state:
            st.session_state["df_movimientos"] = pd.DataFrame(columns=[
                "id", "fecha", "categoria", "detalle", "tipo", "monto", "tasa", 
                "comentarios", "activo", "consolidado", "creado_por", "modificado_por"
            ])
            
    return st.session_state["df_movimientos"]

def guardar_movimiento_local(nuevo_registro):
    """Inserta una nueva transacción directamente en la tabla 'movimientos' de Supabase."""
    supabase = init_supabase()
    
    registro_db = nuevo_registro.copy()
    registro_db["fecha"] = str(registro_db["fecha"])
    registro_db.pop("id", None) # Supabase autogenera el ID
    
    response = supabase.table("movimientos").insert(registro_db).execute()
    obtener_movimientos_locales()
    return response

def actualizar_movimiento_db(id_registro: int, campos_actualizar: dict):
    """Edita celdas específicas de un registro existente en Supabase."""
    supabase = init_supabase()
    if "fecha" in campos_actualizar:
        campos_actualizar["fecha"] = str(campos_actualizar["fecha"])
        
    response = supabase.table("movimientos").update(campos_actualizar).eq("id", id_registro).execute()
    return response

def actualizar_consolidado_mes_db(ids_list: list, estado_consolidado: bool, rol_actual: str):
    """Cierra o reabre masivamente un período mensual en Supabase."""
    if not ids_list:
        return
    supabase = init_supabase()
    supabase.table("movimientos").update({
        "consolidado": estado_consolidado,
        "modificado_por": rol_actual
    }).in_("id", ids_list).execute()
