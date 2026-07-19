# view_presupuestos_creacion.py
import streamlit as st
import pandas as pd

def render_creacion_presupuestos(rol_simulado):
    # --- 🖨️ INYECCIÓN DE CSS DE IMPRESIÓN (OCULTA SIDEBAR, BOTONES Y REDUCE MÁRGENES) ---
    st.markdown("""
        <style>
            @media print {
                /* Ocultar barra lateral de desarrollo, controles de navegación y botones operativos */
                section[data-testid="stSidebar"], 
                div[data-testid="stSegmentedControl"],
                .stButton, 
                header {
                    display: none !important;
                }
                /* Ajustar el lienzo al 100% del ancho del papel sin márgenes muertos */
                .block-container {
                    padding-top: 0rem !important;
                    padding-bottom: 0rem !important;
                    max-width: 100% !important;
                }
                /* Forzar que las tablas rompan de forma limpia si hay muchas páginas */
                tr { page-break-inside: avoid; }
            }
            
            /* Estilo visual para simular la división física de secciones en pantalla */
            .seccion-header {
                background-color: #f1f5f9;
                padding: 6px 12px;
                border-left: 4px solid #3b82f6;
                margin-top: 14px;
                font-weight: bold;
                font-size: 14px;
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("## 📝 Creación de Nuevo Presupuesto")

    # --- DATOS DE CABECERA (MAESTRO) ---
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        cliente = st.text_input("Cliente / Razón Social", placeholder="Ej. Restaurante La Casona")
    with col2:
        ubicacion = st.text_input("Ubicación / Destino", placeholder="Ej. Lechería, Edo. Anzoátegui")
    with col3:
        # Selector de categoría exclusiva para indexación y filtros posteriores
        categoria_filtro = st.selectbox("Categoría (Filtro)", ["Fiesta", "Decoración", "Alquiler", "Suministro", "Otro"])

    st.markdown("---")

    # --- GESTIÓN MÚLTIPLE DE SECCIONES EN SESSION STATE ---
    if "secciones_presupuesto" not in st.session_state:
        # Inicializamos con una sección por defecto
        st.session_state.secciones_presupuesto = [
            {
                "titulo": "ZONA DE DECORACIÓN PRINCIPAL",
                "df": pd.DataFrame(columns=["item", "descripción", "medidas", "juegos/kits", "cantidad", "precio_unitario", "total"])
            }
        ]

    # Controles para añadir/remover secciones físicas
    col_acc1, col_acc2 = st.columns([1, 4])
    with col_acc1:
        if st.button("➕ Añadir Sección Física", use_container_width=True):
            st.session_state.secciones_presupuesto.append({
                "titulo": f"NUEVA SECCIÓN {len(st.session_state.secciones_presupuesto) + 1}",
                "df": pd.DataFrame(columns=["item", "descripción", "medidas", "juegos/kits", "cantidad", "precio_unitario", "total"])
            })
            st.rerun()

    # --- RENDERIZADO DINÁMICO DE SECCIONES ---
    total_general = 0.0

    for idx, sec in enumerate(st.session_state.secciones_presupuesto):
        # Título editable de la sección física
        st.markdown(f"<div class='seccion-header'>{sec['titulo']}</div>", unsafe_allow_html=True)
        nuevo_titulo = st.text_input(f"Editar nombre de sección {idx+1}:", value=sec["titulo"], key=f"title_{idx}", label_visibility="collapsed")
        st.session_state.secciones_presupuesto[idx]["titulo"] = nuevo_titulo.upper()

        # Configuración de columnas del editor de datos limpio
        df_editado = st.data_editor(
            sec["df"],
            key=f"editor_{idx}",
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "item": st.column_config.NumberColumn("Item", min_value=1, format="%d"),
                "descripción": st.column_config.TextColumn("Descripción / Detalle", required=True),
                "medidas": st.column_config.TextColumn("Medidas"),
                "juegos/kits": st.column_config.NumberColumn("Juegos/Kits", default=1),
                "cantidad": st.column_config.NumberColumn("Cantidad", min_value=1, default=1),
                "precio_unitario": st.column_config.NumberColumn("Precio Unitario ($)", min_value=0.0, format="$%.2f"),
                "total": st.column_config.NumberColumn("Total ($)", disabled=True, format="$%.2f")
            }
        )

        # 🔄 Cálculo automático vectorizado de la columna 'total' por sección
        if not df_editado.empty:
            # Asegurar numéricos para evitar errores de tipo
            cant = pd.to_numeric(df_editado["cantidad"]).fillna(0)
            precio = pd.to_numeric(df_editado["precio_unitario"]).fillna(0)
            df_editado["total"] = cant * precio
            subtotal_seccion = df_editado["total"].sum()
        else:
            subtotal_seccion = 0.0

        st.session_state.secciones_presupuesto[idx]["df"] = df_editado

        # Render visual del subtotal de la sección
        col_sub1, col_sub2 = st.columns([4, 1])
        with col_sub2:
            st.markdown(f"**Subtotal Sección:** ${subtotal_seccion:,.2f}")
        
        total_general += subtotal_seccion

    st.markdown("---")

    # --- RESUMEN FINAL Y CLÁUSULAS ---
    col_t1, col_t2 = st.columns([3, 2])
    
    with col_t1:
        st.markdown("#### 📄 Cláusulas Comerciales")
        clausulas_defecto = (
            "* Precios se entienden en: Dólares netos. El costo debe ser pagado el 50% a la aceptación del contrato y el otro 50% 2 días antes del evento.\n"
            "* Si el pago lo realizará en Bs, la tasa que manejamos es Euro indicado por el Banco Central de Venezuela.\n"
            "* Validez de la Oferta: 3 días continuos.\n"
            "* El cliente es enteramente responsable de todo el material suministrado para el evento."
        )
        st.text_area("Términos Legales a Imprimir:", value=clausulas_defecto, height=110, label_visibility="collapsed")

    with col_t2:
        st.markdown(f"### 💰 Total General: ${total_general:,.2f}")
        
        # Validación de rol administrador/gerente según el informe ejecutivo
        permite_escritura = rol_simulado in ["administrador", "gerente"]
        
        if st.button("💾 Guardar y Consolidar Presupuesto", disabled=not permite_escritura, type="primary", use_container_width=True):
            st.success("🎉 Presupuesto guardado con éxito en estado 'Presentado'. ¡Listo para imprimir (Ctrl + P)!")