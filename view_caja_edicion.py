import streamlit as st
import pandas as pd

def render_edicion(df_todos, rol_actual):
    if rol_actual not in ["administrador"]:
        st.error("⛔ Solo el Administrador puede efectuar anulaciones o cambios quirúrgicos aquí.")
        return

    st.subheader("Consola de Edición y Anulaciones Dinámicas")
    st.caption("Los registros anulados desaparecerán de los saldos pero quedarán almacenados para Soporte.")
    
    # Mostrar solo registros activos para que el Administrador edite o anule
    df_activos = df_todos[df_todos["activo"] == True].copy()
    
    if df_activos.empty:
        st.info("No hay registros activos editables.")
        return
        
    cols_visibles = ["id", "fecha", "detalle", "tipo", "monto", "tasa", "comentarios"]
    datos_editor = st.data_editor(df_activos[cols_visibles], hide_index=True, disabled=["id"], use_container_width=True)
    
    st.markdown("### ⚠️ Zona de Anulación (Soft Delete)")
    id_a_anular = st.number_input("Introduce el ID del asiento a anular:", min_value=0, step=1)
    
    if st.button("❌ Aplicar Anulación de Asiento"):
        if id_a_anular in st.session_state["df_movimientos"]["id"].values:
            # Encontrar el índice original en la sesión y apagar el registro
            idx = st.session_state["df_movimientos"][st.session_state["df_movimientos"]["id"] == id_a_anular].index[0]
            st.session_state["df_movimientos"].at[idx, "activo"] = False
            st.session_state["df_movimientos"].at[idx, "modificado_por"] = rol_actual
            st.success(f"¡Asiento #{id_a_anular} anulado exitosamente!")
            st.rerun()
        else:
            st.error("ID no válido.")