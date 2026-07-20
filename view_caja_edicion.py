# view_caja_edicion.py
import streamlit as st
import pandas as pd
from db_connection import actualizar_movimiento_db, obtener_movimientos_locales

def render_edicion(df_mes, rol_actual, es_consolidado):
    st.markdown("### 🛠️ Modificaciones Generales de Auditoría")
    
    if df_mes.empty:
        st.info("No hay registros editables en este periodo.")
        return

    es_consolidado_puro = bool(es_consolidado)
    if es_consolidado_puro:
        st.warning("🔒 **EDICIÓN SUSPENDIDA:** Los registros están blindados por consolidación administrativa.")
        return

    st.caption("💡 Haz doble clic sobre cualquier celda para modificar en línea (Estilo Excel). Al finalizar, presiona el botón inferior.")

    df_editado = st.data_editor(
        df_mes,
        column_order=["fecha", "categoria", "detalle", "tipo", "monto", "tasa", "comentarios"],
        column_config={
            "fecha": st.column_config.DateColumn("Fecha", width=100, format="DD/MM/YYYY"),
            "categoria": st.column_config.TextColumn("Categoría", width=160),
            "detalle": st.column_config.TextColumn("Descripción", width=340),
            "tipo": st.column_config.SelectboxColumn("Tipo Cuenta", width=90, options=["IN-Bs", "EG-Bs", "IN-$Ze", "EG-$Ze", "IN-$Ch", "EG-$Ch"]),
            "monto": st.column_config.NumberColumn("Monto Base", width=130, min_value=0.0, format="%.2f"),
            "tasa": st.column_config.NumberColumn("Tasa Monitor", width=110, min_value=0.0, format="%.2f"),
            "comentarios": st.column_config.TextColumn("Comentario", width=340)
        },
        disabled=es_consolidado_puro,
        hide_index=True,
        use_container_width=False,
        height=600,
        key="editor_excel_caja"
    )

    if not es_consolidado_puro:
        if st.button("💾 Aplicar Cambios Consolidados en Base de Datos"):
            for _, row_editada in df_editado.iterrows():
                id_reg = int(row_editada["id"])
                cambios = {
                    "fecha": str(row_editada["fecha"]),
                    "categoria": str(row_editada["categoria"]).strip().upper(),
                    "detalle": str(row_editada["detalle"]).strip(),
                    "tipo": row_editada["tipo"],
                    "monto": float(row_editada["monto"]),
                    "tasa": float(row_editada["tasa"]) if pd.notnull(row_editada["tasa"]) else 1.0,
                    "comentarios": str(row_editada["comentarios"]).strip(),
                    "modificado_por": rol_actual
                }
                actualizar_movimiento_db(id_reg, cambios)
            
            obtener_movimientos_locales()
            st.success("🎉 ¡Todos los cambios han sido actualizados en Supabase!")
            st.rerun()
