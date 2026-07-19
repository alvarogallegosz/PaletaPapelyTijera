# view_presupuestos_creacion.py
import streamlit as st
import pandas as pd
import datetime

def render_creacion_presupuestos(rol_simulado):
    # --- 🎨 INYECCIÓN DE CSS PARA EMULAR LA ESTÉTICA EXACTA DEL RENDER ---
    st.markdown("""
        <style>
            /* Paleta de Colores Oficiales basada en la Imagen */
            :root {
                --verde-banner: #b8d7a3;
                --gris-cabecera: #f2f2f2;
                --magenta-clausula: #d53f8c;
            }

            @media print {
                section[data-testid="stSidebar"], 
                div[data-testid="stSegmentedControl"],
                .no-print,
                header {
                    display: none !important;
                }
                .block-container {
                    padding-top: 0rem !important;
                    padding-bottom: 0rem !important;
                    max-width: 100% !important;
                }
                tr { page-break-inside: avoid; }
            }

            /* Contenedor del Presupuesto Estilo Factura */
            .presupuesto-container {
                font-family: 'Arial', sans-serif;
                color: #333333;
                line-height: 1.4;
            }
            
            /* Banners de color Verde Suave */
            .banner-verde {
                background-color: #b8d7a3 !important;
                color: #ffffff !important;
                text-align: center;
                font-weight: bold;
                padding: 6px 0px;
                font-size: 15px;
                letter-spacing: 0.5px;
                text-transform: uppercase;
                margin-top: 15px;
                margin-bottom: 10px;
            }
            
            .banner-total {
                background-color: #b8d7a3 !important;
                color: #000000 !important;
                font-weight: bold;
                font-size: 22px;
                padding: 8px 15px;
                margin-top: 15px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            /* Tabla de Presupuesto Limpia */
            .tabla-presupuesto {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 5px;
            }
            
            /* Cabecera de columnas de la sección */
            .tabla-presupuesto th {
                background-color: #f8f9fa;
                border-bottom: 2px solid #e2e8f0;
                color: #000000;
                font-weight: bold;
                font-size: 12px;
                padding: 6px 8px;
                text-transform: uppercase;
            }
            
            /* Nombre de la sección física */
            .seccion-row-header {
                background-color: #f2f2f2 !important;
                font-weight: bold;
                font-size: 13px;
                color: #000000;
                text-align: left;
                padding: 6px 8px;
            }
            
            .tabla-presupuesto td {
                padding: 6px 8px;
                font-size: 12px;
                border-bottom: 1px solid #edf2f7;
                vertical-align: top;
            }
            
            /* Subtotales Dinámicos por Sección */
            .subtotal-row {
                background-color: #edf2f7;
                font-weight: bold;
                font-size: 13px;
                text-align: right;
                padding: 6px 15px;
                margin-bottom: 15px;
            }

            /* Cláusulas con Encabezado Magenta */
            .clausulas-box {
                font-size: 11px;
                margin-top: 20px;
                color: #2d3748;
            }
            .clausulas-titulo {
                color: #d53f8c;
                font-weight: bold;
                font-size: 12px;
                margin-bottom: 4px;
            }
        </style>
    """, unsafe_allow_html=True)

    # --- CONTROL DE MODOS OPERATIVOS ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("🖨️ Modo de Visualización")
    modo_impresion = st.sidebar.checkbox("👁️ Activar Vista de Impresión / PDF", value=False)

    # --- INICIALIZACIÓN DEL ESTADO DE LAS 5 SECCIONES MÁXIMAS ---
    if "secciones_presupuesto" not in st.session_state:
        st.session_state.secciones_presupuesto = [
            {"titulo": "DECORACIÓN PRINCIPAL (ALQUILER)", "df": pd.DataFrame(columns=["descripción", "medidas", "juegos/kits", "cantidad", "precio_unitario"])},
            {"titulo": "ZONA DE CENTRO DE MESA", "df": pd.DataFrame(columns=["descripción", "medidas", "juegos/kits", "cantidad", "precio_unitario"])}
        ]

    if "meta_presupuesto" not in st.session_state:
        st.session_state.meta_presupuesto = {
            "cliente": "REST. LA CASONA",
            "nombre": "MOD 2 DECORACIÓN COMUNIÓN",
            "fecha_evento": "SÁBADO 25 DE JULIO DE 2026",
            "lugar": "LECHERÍA, ESTADO ANZOATEGUI",
            "fecha_larga": "17 de julio de 2026"
        }

    # ==========================================
    # 📝 MODO 1: EDICIÓN E INYECCIÓN DE DATOS
    # ==========================================
    if not modo_impresion:
        st.markdown("## 📝 Panel de Maquetación de Presupuestos")
        
        # Formulario de Metadata Superior
        with st.container(border=True):
            st.markdown("### 🏛️ Datos del Evento y Cabecera")
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.meta_presupuesto["cliente"] = st.text_input("Cliente / Razón Social:", value=st.session_state.meta_presupuesto["cliente"])
                st.session_state.meta_presupuesto["nombre"] = st.text_input("Nombre del Presupuesto:", value=st.session_state.meta_presupuesto["nombre"])
                st.session_state.meta_presupuesto["lugar"] = st.text_input("Lugar del Evento:", value=st.session_state.meta_presupuesto["lugar"])
            with col2:
                st.session_state.meta_presupuesto["fecha_evento"] = st.text_input("Fecha del Evento (Formato Libre):", value=st.session_state.meta_presupuesto["fecha_evento"])
                st.session_state.meta_presupuesto["fecha_larga"] = st.text_input("Fecha Larga de Emisión (Tope Superior Derecho):", value=st.session_state.meta_presupuesto["fecha_larga"])
                categoria_filtro = st.selectbox("Categoría Indexación (Filtro BD):", ["Decoración", "Fiesta", "Alquiler", "Suministro", "Otro"])

        # Control Dinámico de Secciones (Tope máximo de 5)
        st.markdown("### 📦 Contenido y Bloques del Presupuesto")
        col_btn1, col_btn2 = st.columns([1, 4])
        with col_btn1:
            if st.button("➕ Añadir Sección", use_container_width=True, disabled=len(st.session_state.secciones_presupuesto) >= 5):
                st.session_state.secciones_presupuesto.append({
                    "titulo": f"NUEVA SECCIÓN {len(st.session_state.secciones_presupuesto) + 1}",
                    "df": pd.DataFrame(columns=["descripción", "medidas", "juegos/kits", "cantidad", "precio_unitario"])
                })
                st.rerun()

        # Renderizado de editores interactivos en pantalla
        for idx, sec in enumerate(st.session_state.secciones_presupuesto):
            with st.expander(f"🔹 Sección {idx+1}: {sec['titulo']}", expanded=True):
                col_t_sec, col_t_del = st.columns([4, 1])
                with col_t_sec:
                    nuevo_titulo = st.text_input(f"Nombre de la Sección {idx+1}:", value=sec["titulo"], key=f"title_input_{idx}")
                    st.session_state.secciones_presupuesto[idx]["titulo"] = nuevo_titulo.upper()
                with col_t_del:
                    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                    if st.button("🗑️ Eliminar", key=f"del_sec_{idx}", use_container_width=True) and len(st.session_state.secciones_presupuesto) > 1:
                        st.session_state.secciones_presupuesto.pop(idx)
                        st.rerun()

                # Tabla limpia interactiva (El ID/Item se autogenera en la vista final)
                df_editado = st.data_editor(
                    sec["df"],
                    key=f"editor_data_{idx}",
                    num_rows="dynamic",
                    use_container_width=True,
                    column_config={
                        "descripción": st.column_config.TextColumn("Descripción / Detalle", required=True),
                        "medidas": st.column_config.TextColumn("Medidas / Notas"),
                        "juegos/kits": st.column_config.NumberColumn("Juegos/Kits (Opcional)", min_value=1, format="%d"),
                        "cantidad": st.column_config.NumberColumn("Cantidad", min_value=1, default=1),
                        "precio_unitario": st.column_config.NumberColumn("Precio Unitario ($)", min_value=0.0, format="$%.2f")
                    }
                )
                st.session_state.secciones_presupuesto[idx]["df"] = df_editado

        # Guardado en base de datos estructural
        st.markdown("---")
        permite_escritura = rol_simulado in ["administrador", "gerente"]
        if st.button("💾 Guardar Estructura Completa en BD", disabled=not permite_escritura, type="primary", use_container_width=True):
            st.success("🎉 Presupuesto consolidado exitosamente en base de datos con formato multi-sección JSON.")

    # ==========================================
    # 🖨️ MODO 2: EMULACIÓN FIEL DE IMPRESIÓN / PDF
    # ==========================================
    else:
        meta = st.session_state.meta_presupuesto
        
        st.info("💡 Modo de impresión activo. Presiona **Ctrl + P** en tu teclado para exportar a PDF limpio.")
        
        # Contenedor Maestro Estilizado
        st.markdown('<div class="presupuesto-container">', unsafe_allow_html=True)
        
        # 1. Encabezado e Imagen Corporativa desde la Raíz
        st.image("encabezado_paleta.png", use_container_width=True)
        
        # 2. Bloque de Datos del Evento (Izquierda) y Fecha Larga (Derecha)
        col_meta_izq, col_meta_der = st.columns([3, 2])
        with col_meta_izq:
            st.markdown(f"""
                <div style='font-size: 13px; font-weight: bold; margin-top: 5px;'>{meta['nombre']}</div>
                <div style='font-size: 12px; margin-top: 3px;'>FECHA {meta['fecha_evento']}</div>
                <div style='font-size: 12px; margin-top: 3px;'>{meta['lugar']}</div>
            """, unsafe_allow_html=True)
        with col_meta_der:
            st.markdown(f"<div style='text-align: right; font-size: 13px; font-weight: bold; margin-top: 5px;'>{meta['fecha_larga']}</div>", unsafe_allow_html=True)
            
        # 3. Banner Principal del Presupuesto
        st.markdown(f'<div class="banner-verde">PRESUPUESTO {meta["nombre"]}</div>', unsafe_allow_html=True)
        
        # 4. Procesamiento Analítico y Construcción de las Tablas Físicas
        total_general = 0.0
        
        for sec in st.session_state.secciones_presupuesto:
            df_sec = sec["df"]
            
            # Construcción de la tabla pura en HTML para control absoluto de sombreados
            html_tabla = f"""
            <table class="tabla-presupuesto">
                <thead>
                    <tr>
                        <th style="width: 6%; text-align: center;">ITEM</th>
                        <th style="text-align: left;">{sec['titulo']}</th>
                        <th style="width: 25%; text-align: left;">MEDIDAS</th>
                        <th style="width: 12%; text-align: center;">JUEGOS/KITS</th>
                        <th style="width: 10%; text-align: center;">CANTIDAD</th>
                        <th style="width: 12%; text-align: right;">PRECIO</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            subtotal_seccion = 0.0
            
            if not df_sec.empty:
                for i, row in enumerate(df_sec.itertuples(), start=1):
                    # Validación matemática estricta de la regla Juegos/Kits Null
                    jk = getattr(row, 'juegos_kits', None)
                    cant = getattr(row, 'cantidad', 1)
                    pu = getattr(row, 'precio_unitario', 0.0)
                    
                    # Limpieza de valores nulos o vacíos en pandas
                    cant = cant if pd.notna(cant) else 1
                    pu = pu if pd.notna(pu) else 0.0
                    
                    if pd.isna(jk) or jk is None or jk == 0:
                        total_fila = cant * pu
                        jk_str = "" # No se imprime si es null
                    else:
                        total_fila = jk * cant * pu
                        jk_str = f"{int(jk)}"
                        
                    subtotal_seccion += total_fila
                    
                    # Inyección de celdas formateadas
                    medidas_str = getattr(row, 'medidas', '')
                    medidas_str = medidas_str if pd.notna(medidas_str) else ''
                    
                    html_tabla += f"""
                    <tr>
                        <td style="text-align: center;">{i}</td>
                        <td style="text-align: left;">{getattr(row, 'descripción', '')}</td>
                        <td style="text-align: left;">{medidas_str}</td>
                        <td style="text-align: center;">{jk_str}</td>
                        <td style="text-align: center;">{int(cant)}</td>
                        <td style="text-align: right;">{int(total_fila) if total_fila.is_integer() else f"{total_fila:,.2f}"}</td>
                    </tr>
                    """
            else:
                html_tabla += f'<tr><td colspan="6" style="text-align: center; color: #a0aec0;">Sin registros en esta sección</td></tr>'
                
            html_tabla += "</tbody></table>"
            st.markdown(html_tabla, unsafe_allow_html=True)
            
            # Bloque de Subtotal Físico de la Sección
            st.markdown(f'<div class="subtotal-row">SUB TOTAL {sec["titulo"]}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;${int(subtotal_seccion) if subtotal_seccion.is_integer() else f"{subtotal_seccion:,.2f}"}</div>', unsafe_allow_html=True)
            total_general += subtotal_seccion
            
        # 5. Barra del Total General Homologada
        st.markdown(f"""
            <div class="banner-total">
                <span>TOTAL A CANCELAR</span>
                <span>${int(total_general) if total_general.is_integer() else f"{total_general:,.2f}"}</span>
            </div>
        """, unsafe_allow_html=True)
        
        # 6. Pie de Página Legal (Cláusulas) Estables
        st.markdown("""
            <div class="clausulas-box">
                <div class="clausulas-titulo">CLAUSULAS:</div>
                <b>Las condiciones generales de nuestra oferta son las siguientes:</b><br>
                * Precios se entienden en: Dólares netos. El costo debe ser pagado el 50% a la aceptación del contrato y el otro 50% 2 días antes del evento.<br>
                * Si el pago lo realizará en Bs la tasa que manejamos es Euro indicado por el Banco Central de Venezuela.<br>
                * Validez de la Oferta: 3 días continuos.<br>
                * Si el cliente cancela el servicio (es decir no va a querer el servicio) 2 días antes del evento le será devuelto un 30% del monto pagado.<br>
                * Si el cliente cancela el servicio (es decir no va a querer el servicio) 1 día antes ó el día del evento no se le devolverá nada del monto pagado.<br>
                * El cliente es enteramente responsable de todo el material suministrado para el evento y cancelara cualquier daño al mismo.<br><br>
                Sin más a que hacer referencia, a la espera de vuestra consideración, nos despedimos de Ud.,<br>
                Atentamente,<br><br>
                <b>Paletapapelytijera</b>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)