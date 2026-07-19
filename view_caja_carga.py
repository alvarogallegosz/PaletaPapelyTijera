import streamlit as st
from datetime import datetime
from db_connection import guardar_movimiento_local

def render_carga(rol_actual):
    # Verificación estricta de jerarquía
    if rol_actual not in ["administrador"]:
        st.error("⛔ Tu rol actual no posee permisos de ESCRITURA en esta pestaña.")
        return

    st.subheader("Carga de Movimientos de Caja")
    with st.form("form_carga_caja", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            f_ins = st.date_input("Fecha de Operación", datetime.now())
            det_ins = st.text_input("Detalle / Concepto")
        with c2:
            t_ins = st.selectbox("Tipo Cuenta", ["IN-Bs", "EG-Bs", "IN-$Ze", "EG-$Ze", "IN-$Ch", "EG-$Ch"])
            m_ins = st.number_input("Monto", min_value=0.0, step=0.01)
        with c3:
            tas_ins = st.number_input("Tasa Monitor", min_value=0.0, value=40.00)
            com_ins = st.text_area("Notas internas")
            
        if st.form_submit_button("Registrar Transacción"):
            if det_ins and m_ins > 0:
                reg = {
                    "fecha": f_ins, "detalle": det_ins, "tipo": t_ins, "monto": m_ins,
                    "tasa": tas_ins if "Bs" in t_ins else None, "comentarios": com_ins,
                    "activo": True, "creado_por": rol_actual, "modificado_por": rol_actual
                }
                guardar_movimiento_local(reg)
                st.success("¡Operación guardada de forma temporal en pantalla!")
                st.rerun()