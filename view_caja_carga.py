# view_caja_carga.py
import streamlit as st
from datetime import datetime
from db_connection import guardar_movimiento_local

def render_carga(rol_actual):
    if rol_actual not in ["administrador"]:
        st.error("⛔ Tu rol actual no posee permisos de ESCRITURA en esta pestaña.")
        return

    st.markdown("### 📝 Carga de Movimientos de Caja")
    
    with st.form("form_carga_caja", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            f_ins = st.date_input("Fecha de Operación", datetime.now())
            cat_ins = st.text_input("Categoría", placeholder="Ej: Salario personal, Transporte, Impresión...")
            det_ins = st.text_input("Detalle / Concepto", placeholder="Ej. Pago de suministros...")
        with c2:
            t_ins = st.selectbox("Tipo Cuenta", ["IN-Bs", "EG-Bs", "IN-$Ze", "EG-$Ze", "IN-$Ch", "EG-$Ch"])
            monto_raw = st.text_input("Monto Ocurrencia", value="0.00")
            tas_ins = st.number_input("Tasa Monitor", min_value=0.0, value=700.00, step=1.0)
            
        com_ins = st.text_area("Notas internas / Auditoría", height=68)
        btn_guardar = st.form_submit_button("Registrar Transacción")
        
        if btn_guardar:
            if not det_ins.strip():
                st.error("El campo 'Detalle / Concepto' es obligatorio.")
                return
            
            try:
                monto_limpio = monto_raw.replace(",", ".")
                m_ins = float(monto_limpio)
                
                if m_ins <= 0:
                    st.error("El monto debe ser un número real mayor a cero.")
                    return
                
                reg = {
                    "fecha": f_ins, "categoria": cat_ins.strip(), "detalle": det_ins, "tipo": t_ins, "monto": m_ins,
                    "tasa": tas_ins if "Bs" in t_ins else None, "comentarios": com_ins,
                    "activo": True, "consolidado": False, "creado_por": rol_actual, "modificado_por": rol_actual
                }
                guardar_movimiento_local(reg)
                st.success(f"¡Asiento registrado! Monto procesado: {m_ins:,.2f}")
                st.rerun()
            except ValueError:
                st.error("Formato de monto inválido. Usa puntos o comas para los decimales de forma clara.")