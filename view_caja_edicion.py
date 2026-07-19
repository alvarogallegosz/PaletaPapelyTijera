# view_caja_edicion.py
import streamlit as st
import pandas as pd
from db_connection import guardar_cambios_en_disco

def render_edicion(df_mes, rol_actual, es_consolidado):
    st.markdown("### 🛠️ Modificaciones Generales de Auditoría")
    
    if df_mes.empty:
        st.info("No hay registros editables en este periodo.")
        return

    es_consolidado_puro = bool(es_consolidado)
    if es_consolidado_puro:
        st.warning("🔒 **EDICIÓN SUSPENDIDA:** Los registros están blindados por consolidación administrativa.")
        return

    st.caption("💡 Haz doble clic sobre cualquier celda para modificar en línea. Los anchos están optimizados para evitar desbordes.")

    # Dataframe interactivo con control estricto de anchos y ordenamiento sin ID en pantalla
    df_editado = st.data_editor(
        df_mes,
        column_order=["fecha", "categoria", "detalle", "tipo", "monto", "tasa", "comentarios"],
        column_config={
            "fecha": st.column_config.DateColumn("Fecha", width=110, format="DD/MM/YYYY"),
            "categoria": st.column_config.TextColumn("Categoría", width=160),
            "detalle": st.column_config.TextColumn("Descripción", width=320),
            "tipo": st.column_config.SelectboxColumn("Tipo Cuenta", width=100, options=["IN-Bs", "EG-Bs", "IN-$Ze", "EG-$Ze", "IN-$Ch", "EG-$Ch"]),
            "monto": st.column_config.NumberColumn("Monto Base", width=130, min_value=0.0, format="%.2f"),
            "tasa": st.column_config.NumberColumn("Tasa Monitor", width=110, min_value=0.0, format="%.2f"),
            "comentarios": st.column_config.TextColumn("Comentario", width=320)
        },
        disabled=es_consolidado_puro,
        hide_index=True,
        use_container_width=False,
        key="editor_excel_caja"
    )

    if not es_consolidado_puro:
        if st.button("💾 Aplicar Cambios Consolidados en Base de Datos"):
            df_global = st.session_state["df_movimientos"]
            
            for _, row_editada in df_editado.iterrows():
                idx_original = df_global[df_global["id"] == row_editada["id"]].index
                if not idx_original.empty:
                    idx = idx_original[0]
                    df_global.at[idx, "fecha"] = row_editada["fecha"]
                    df_global.at[idx, "categoria"] = str(row_editada["categoria"]).strip().upper()
                    df_global.at[idx, "detalle"] = str(row_editada["detalle"]).strip()
                    df_global.at[idx, "tipo"] = row_editada["tipo"]
                    df_global.at[idx, "monto"] = float(row_editada["monto"])
                    df_global.at[idx, "tasa"] = float(row_editada["tasa"]) if pd.notnull(row_editada["tasa"]) else 1.0
                    df_global.at[idx, "comentarios"] = str(row_editada["comentarios"]).strip()
                    df_global.at[idx, "modificado_por"] = rol_actual
            
            guardar_cambios_en_disco()
            st.success("🎉 ¡Todos los cambios han sido consolidados de forma masiva!")
            st.rerun()