# view_caja_carga.py
import streamlit as st
from datetime import datetime
from db_connection import guardar_movimiento_local

opciones_cuentas = [
    "IN-Bs", "EG-Bs", 
    "IN-$Ze", "EG-$Ze", 
    "IN-$Ch", "EG-$Ch",
    "IN-$AhZe", "EG-$AhZe",
    "IN-$AhCh", "EG-$AhCh"
]

def render_carga(rol_actual, es_consolidado):
    if rol_actual not in ["administrador", "gerente", "contador"]:
        st.error("⛔ Tu rol actual no posee permisos de ESCRITURA en esta pestaña.")
        return

    st.markdown("### 📝 Carga de Movimientos de Caja")
    
    if es_consolidado:
        st.warning("🔒 **PERÍODO CONSOLIDADO:** Este mes ha sido cerrado por la administración. No se permiten modificaciones.")
        return
    
    # clear_on_submit=False evita el vaciado accidental al presionar Enter prematuramente
    with st.form("form_carga_caja", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            f_ins = st.date_input("Fecha de Operación", datetime.now(), disabled=es_consolidado)
            cat_ins = st.text_input("Categoría", placeholder="Ej: SALARIO PERSONAL, IMPRESIÓN...", disabled=es_consolidado)
            det_ins = st.text_input("Detalle / Concepto", placeholder="Ej. Pago de arriendo...", disabled=es_consolidado)
        with c2:
            t_ins = st.selectbox("Tipo Cuenta", opciones_cuentas, disabled=es_consolidado)
            monto_raw = st.text_input("Monto Ocurrencia", value="0.00", disabled=es_consolidado)
            tas_ins = st.number_input("Tasa Monitor", min_value=0.0, value=40.00, step=0.1, disabled=es_consolidado)
            
        com_ins = st.text_area("Notas internas / Auditoría", height=68, disabled=es_consolidado)
        btn_guardar = st.form_submit_button("Registrar Transacción", disabled=es_consolidado)
        
        if btn_guardar:
            if not det_ins.strip():
                st.error("El campo 'Detalle / Concepto' es obligatorio.")
                return
            
            try:
                monto_limpio = monto_raw.replace(".", "").replace(",", ".")
                m_ins = float(monto_limpio)
                
                if m_ins <= 0:
                    st.error("El monto debe ser mayor a cero.")
                    return
                
                reg = {
                    "fecha": f_ins, "categoria": cat_ins.strip().upper(), "detalle": det_ins.strip(), "tipo": t_ins, "monto": m_ins,
                    "tasa": tas_ins if "Bs" in t_ins else None, "comentarios": com_ins.strip(),
                    "activo": True, "consolidado": False, "creado_por": rol_actual, "modificado_por": rol_actual
                }
                guardar_movimiento_local(reg)
                st.success(f"💥 ¡Asiento registrado con éxito! Recuerda usar TAB para navegar entre casillas.")
                st.rerun()
            except ValueError:
                st.error("Formato numérico inválido.")
