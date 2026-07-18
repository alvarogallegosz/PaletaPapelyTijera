import streamlit as st
import pandas as pd
from datetime import datetime

# Configuración de la página
st.set_page_config(
    page_title="Paleta, Papel y Tijera - Control de Costos",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Paleta, Papel y Tijera")
st.subheader("Estructura de Costos y Flujo de Caja Dinámico")
st.markdown("---")

# --- DATOS DE PRUEBA (MOCK DATA) ---
# Simulamos lo que vendría de Supabase
if 'movimientos' not in st.session_state:
    st.session_state.movimientos = pd.DataFrame([
        {"id": 1, "Fecha": "2026-06-01", "Detalle": "CIERRE de mayo de 2024", "Tipo": "Inicial", "Monto": 1787.74, "Tasa": 40.18, "Comentarios": "Saldo arrastrado de cuentas auditadas"},
        {"id": 2, "Fecha": "2026-06-01", "Detalle": "Egreso por pago platos lander", "Tipo": "EG-Bs", "Monto": 1332.00, "Tasa": 40.18, "Comentarios": "Almuerzo de equipo por cierre de proyecto"},
        {"id": 3, "Fecha": "2026-06-03", "Detalle": "Egreso por pago envío inflables", "Tipo": "EG-$Ze", "Monto": 66.00, "Tasa": None, "Comentarios": "Pago a proveedor logístico VIP"},
        {"id": 4, "Fecha": "2026-06-03", "Detalle": "Egreso en cash pago contador", "Tipo": "EG-$Ch", "Monto": 40.00, "Tasa": None, "Comentarios": "Honorarios correspondientes a mayo"},
        {"id": 5, "Fecha": "2026-06-04", "Detalle": "Ingreso en cash por pago de georgette", "Tipo": "IN-$Ch", "Monto": 1600.00, "Tasa": None, "Comentarios": "Anticipo de cliente recurrente"},
    ])

# --- ORGANIZACIÓN POR PESTAÑAS ---
tab_carga, tab_visor, tab_edicion = st.tabs([
    "📝 Carga de Movimientos", 
    "🔍 Visor de Flujo e Historial", 
    "⚙️ Correcciones y Ajustes"
])

# =========================================================================
# PESTAÑA 1: CARGA DE DATOS
# =========================================================================
with tab_carga:
    st.header("Registrar Nuevo Movimiento")
    
    # Formulario limpio para evitar recargas molestas en cada clic
    with st.form("form_carga", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            fecha = st.date_input("Fecha del Movimiento", datetime.now())
            detalle = st.text_input("Detalle / Concepto", placeholder="Ej. Pago de alquiler local")
            
        with col2:
            tipo_mov = st.selectbox(
                "Tipo de Movimiento",
                ["IN-Bs", "EG-Bs", "IN-$Ze", "EG-$Ze", "IN-$Ch", "EG-$Ch"]
            )
            monto = st.number_input("Monto", min_value=0.0, step=0.01, format="%.2f")
            
        with col3:
            # Tasa de cambio condicional en la mente del usuario (la app la pide siempre, pero se usa si es Bs)
            tasa = st.number_input("Tasa de Cambio Monitor (Si aplica)", min_value=0.0, step=0.01, value=39.79)
            comentarios = st.text_area("Comentarios Ocultos (Notas internas)", placeholder="Detalles extra que no deben saturar el reporte principal...")
            
        btn_guardar = st.form_submit_button("🚀 Registrar en Sistema")
        
        if btn_guardar:
            if detalle and monto > 0:
                # Lógica temporal para el prototipo
                nuevo_id = len(st.session_state.movimientos) + 1
                nueva_fila = {
                    "id": nuevo_id,
                    "Fecha": str(fecha),
                    "Detalle": detalle,
                    "Tipo": tipo_mov,
                    "Monto": monto,
                    "Tasa": tasa if "Bs" in tipo_mov else None,
                    "Comentarios": comentarios if comentarios else ""
                }
                st.session_state.movimientos = pd.concat([st.session_state.movimientos, pd.DataFrame([nueva_fila])], ignore_index=True)
                st.success(f"¡Movimiento '{detalle}' registrado con éxito!")
                st.rerun()
            else:
                st.error("Por favor, rellena el detalle y un monto mayor a 0.")

# =========================================================================
# PESTAÑA 2: VISOR E HISTORIAL (CON COMENTARIOS DINÁMICOS)
# =========================================================================
with tab_visor:
    st.header("Historial de Transacciones")
    st.markdown("*Haz clic en cualquier celda para seleccionar una fila y revelar sus comentarios ocultos en el panel lateral.*")
    
    # Columnas para separar la tabla de la visualización de notas
    col_tabla, col_lateral = st.columns([3, 1])
    
    df_visor = st.session_state.movimientos.copy()
    
    with col_tabla:
        # Usamos la selección integrada de Streamlit (Dataframe selection)
        seleccion = st.dataframe(
            df_visor[["id", "Fecha", "Detalle", "Tipo", "Monto", "Tasa"]], 
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row"
        )
        
    with col_lateral:
        st.subheader("💬 Notas e Información")
        
        # Verificar si hay una fila seleccionada
        if seleccion and len(seleccion["selection"]["rows"]) > 0:
            idx_seleccionado = seleccion["selection"]["rows"][0]
            fila_real = df_visor.iloc[idx_seleccionado]
            
            st.info(f"**ID Seleccionado:** #{fila_real['id']}")
            st.markdown(f"**Concepto:** {fila_real['Detalle']}")
            
            # El "comentario oculto" se invoca dinámicamente aquí
            if fila_real["Comentarios"]:
                st.success(f"**Comentario Oculto:**\n\n{fila_real['Comentarios']}")
            else:
                st.caption("Esta transacción no incluye notas aclaratorias.")
        else:
            st.caption("👈 Selecciona una fila de la tabla para inspeccionar los comentarios explicativos.")

# =========================================================================
# PESTAÑA 3: CORRECCIONES Y EDICIÓN
# =========================================================================
with tab_edicion:
    st.header("Módulo de Modificaciones Rápidas")
    st.warning("⚠️ Cualquier cambio realizado aquí modificará la base de datos de manera inmediata.")
    
    # El st.data_editor permite editar directamente como si fuera un Excel
    df_editable = st.session_state.movimientos.copy()
    
    datos_corregidos = st.data_editor(
        df_editable,
        hide_index=True,
        disabled=["id"], # El ID no se toca por seguridad
        use_container_width=True,
        num_rows="dynamic" # Permite eliminar filas si es necesario
    )
    
    if st.button("💾 Guardar Correcciones"):
        st.session_state.movimientos = datos_corregidos
        st.success("¡Base de datos actualizada correctamente con las correcciones!")
        st.rerun()