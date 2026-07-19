# view_caja_edicion.py
import streamlit as st
import pandas as pd
from db_connection import guardar_cambios_en_disco

def render_edicion(df_mes, rol_actual, es_consolidado):
    st.markdown("### 🛠️ Modificación y Ajuste de Registros")
    
    if df_mes.empty:
        st.info("No hay registros editables en este periodo.")
        return

    if es_consolidado:
        st.warning("🔒 **EDICIÓN SUSPENDIDA:** Los registros están blindados por consolidación.")

    opciones = {
        row["id"]: f"ID: {row['id']} | {row['tipo']} | {row['detalle'][:25]}... | {row['monto']:,.2f}"
        for _, row in df_mes.iterrows()
    }
    
    id_sel = st.selectbox("Seleccione el registro a modificar:", options=list(opciones.keys()), format_func=lambda x: opciones[x], disabled=es_consolidado)
    registro_actual = df_mes[df_mes["id"] == id_sel].iloc[0]
    
    with st.form("form_edicion", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            f_edit = st.date_input("Fecha", registro_actual["fecha"], disabled=es_consolidado)
            cat_edit = st.text_input("Categoría", value=str(registro_actual["categoria"]), disabled=es_consolidado)
            det_edit = st.text_input("Detalle", value=str(registro_actual["detalle"]), disabled=es_consolidado)
        with c2:
            t_edit = st.selectbox("Tipo Cuenta", ["IN-Bs", "EG-Bs", "IN-$Ze", "EG-$Ze", "IN-$Ch", "EG-$Ch"], index=["IN-Bs", "EG-Bs", "IN-$Ze", "EG-$Ze", "IN-$Ch", "EG-$Ch"].index(registro_actual["tipo"]), disabled=es_consolidado)
            monto_edit = st.number_input("Monto", min_value=0.0, value=float(registro_actual["monto"]), disabled=es_consolidado)
            tasa_edit = st.number_input("Tasa", min_value=0.0, value=float(registro_actual["tasa"]) if pd.notnull(registro_actual["tasa"]) else 0.0, disabled=es_consolidado)
            
        com_edit = st.text_area("Notas", value=str(registro_actual["comentarios"]) if pd.notnull(registro_actual["comentarios"]) else "", disabled=es_consolidado)
        
        b1, b2 = st.columns(2)
        with b1: btn_upd = st.form_submit_button("💾 Guardar Cambios", disabled=es_consolidado)
        with b2: btn_del = st.form_submit_button("❌ Eliminar Registro", disabled=es_consolidado)
        
        if (btn_upd or btn_del) and es_consolidado:
            st.error("Mes Consolidado. No puedes forzar la escritura.")
            return

        df_global = st.session_state["df_movimientos"]
        idx = df_global[df_global["id"] == id_sel].index[0]

        if btn_upd:
            df_global.at[idx, "fecha"] = f_edit
            df_global.at[idx, "categoria"] = cat_edit.strip().upper()
            df_global.at[idx, "detalle"] = det_edit.strip()
            df_global.at[idx, "tipo"] = t_edit
            df_global.at[idx, "monto"] = monto_edit
            df_global.at[idx, "tasa"] = tasa_edit if "Bs" in t_edit else None
            df_global.at[idx, "comentarios"] = com_edit.strip()
            df_global.at[idx, "modificado_por"] = rol_actual
            
            guardar_cambios_en_disco()
            st.success("Registro actualizado.")
            st.rerun()
            
        if btn_del:
            df_global.at[idx, "activo"] = False
            df_global.at[idx, "modificado_por"] = rol_actual
            guardar_cambios_en_disco()
            st.success("Registro removido.")
            st.rerun()