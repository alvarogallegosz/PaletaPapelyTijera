# view_caja_edicion.py
import streamlit as st
import pandas as pd
from db_connection import guardar_cambios_en_disco

def render_edicion(df_mes, rol_actual, es_consolidado):
    st.markdown("### 🛠️ Modificaciones Generales de Auditoría")
    
    if df_mes.empty:
        st.info("No hay registros editables en este periodo.")
        return

    if es_consolidado:
        st.warning("🔒 **EDICIÓN SUSPENDIDA:** Los registros están blindados por consolidación administrativa.")
        return

    st.caption("💡 Puedes modificar cualquier celda haciendo doble clic directamente sobre ella (Estilo Excel). Al finalizar, presiona el botón inferior para procesar los cambios.")

    # Dataframe interactivo
    df_editado = st.data_editor(
        df_mes,
        column_order=["id", "fecha", "categoria", "detalle", "tipo", "monto", "tasa", "comentarios"],
        column_config={
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "fecha": st.column_config.DateColumn("Fecha"),
            "tipo": st.column_config.SelectboxColumn("Tipo Cuenta", options=["IN-Bs", "EG-Bs", "IN-$Ze", "EG-$Ze", "IN-$Ch", "EG-$Ch"]),
            "monto": st.column_config.NumberColumn("Monto", min_value=0.0, format="%.2f"),
            "tasa": st.column_config.NumberColumn("Tasa", min_value=0.0),
            "categoria": st.column_config.TextColumn("Categoría"),
            "detalle": st.column_config.TextColumn("Detalle"),
            "comentarios": st.column_config.TextColumn("Comentarios")
        },
        disabled=es_consolidado,
        hide_index=True,
        use_container_width=True,
        key="editor_excel_caja"
    )

    # Botón unificado de guardado masivo
    if not es_consolidado:
        if st.button("💾 Aplicar Cambios Consolidados en Base de Datos"):
            df_global = st.session_state["df_movimientos"]
            
            # Sincronizamos las filas alteradas usando el ID como clave primaria
            for _, row_editada in df_editado.iterrows():
                idx_original = df_global[df_global["id"] == row_editada["id"]].index
                if not idx_original.empty:
                    idx = idx_original[0]
                    df_global.at[idx, "fecha"] = row_editada["fecha"]
                    df_global.at[idx, "categoria"] = str(row_editada["categoria"]).strip().upper()
                    df_global.at[idx, "detalle"] = str(row_editada["detalle"]).strip()
                    df_global.at[idx, "tipo"] = row_editada["tipo"]
                    df_global.at[idx, "monto"] = float(row_editada["monto"])
                    df_global.at[idx, "tasa"] = float(row_editada["tasa"]) if pd.notnull(row_editada["tasa"]) else None
                    df_global.at[idx, "comentarios"] = str(row_editada["comentarios"]).strip()
                    df_global.at[idx, "modificado_por"] = rol_actual
            
            guardar_cambios_en_disco()
            st.success("🎉 ¡Todos los cambios han sido consolidados exitosamente en el archivo local!")
            st.rerun()