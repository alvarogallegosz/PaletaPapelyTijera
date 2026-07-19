# view_presupuestos_creacion.py
import streamlit as st
import pandas as pd

def render_creacion_presupuestos(rol_simulado):
    # --- 🎨 ESTILOS CSS INYECTADOS PARA EMULACIÓN EXACTA DE IMPRESIÓN ---
    st.markdown("""
        <style>
            @media print {
                section[data-testid="stSidebar"], 
                div[data-testid="stSegmentedControl"],
                .no-print,
                .stButton,
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

            /* Estructura Base de la Hoja de Impresión */
            .documento-hoja {
                font-family: 'Arial', sans-serif;
                color: #000000;
                background-color: #ffffff;
                padding: 10px;
            }

            /* Metadata Superior Separada */
            .meta-contenedor {
                display: flex;
                justify-content: space-between;
                font-size: 13px;
                line-height: 1.5;
                margin-top: 8px;
                margin-bottom: 5px;
            }
            .meta-izquierda {
                font-weight: normal;
            }
            .meta-derecha {
                text-align: right;
                font-weight: bold;
            }

            /* Banner Principal Verde Suave */
            .banner-verde-principal {
                background-color: #b8d7a3 !important;
                color: #ffffff !important;
                text-align: center;
                font-weight: bold;
                padding: 6px 0px;
                font-size: 14px;
                letter-spacing: 0.5px;
                text-transform: uppercase;
                margin-top: 5px;
                margin-bottom: 10px;
            }

            /* Tablas de Presupuesto */
            .tabla-remastered {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 0px;
            }
            .tabla-remastered th {
                background-color: #fffdeb !important; /* Color Crema para cabeceras */
                border-bottom: 1px solid #cbd5e1;
                color: #000000;
                font-weight: bold;
                font-size: 12px;
                padding: 5px 8px;
            }
            .tabla-remastered td {
                padding: 6px 8px;
                font-size: 12px;
                border-bottom: 1px solid #e2e8f0;
                vertical-align: top;
            }

            /* Subtotales Dinámicos */
            .fila-subtotal-seccion {
                background-color: #ffffff;
                font-weight: bold;
                font-size: 13px;
                text-align: right;
                padding: 6px 8px;
                margin-bottom: 12px;
                border-bottom: 1px solid #cbd5e1;
            }

            /* Banner de Total Final */
            .banner-total-general {
                background-color: #b8d7a3 !important;
                color: #000000 !important;
                font-weight: bold;
                font-size: 22px;
                padding: 6px 15px;
                margin-top: 10px;
                margin-bottom: 15px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            /* Cláusulas Comerciales */
            .clausulas-container {
                font-size: 11px;
                margin-top: 15px;
                color: #1a202c;
                line-height: 1.4;
            }
            .clausulas-header {
                color: #d53f8c;
                font-weight: bold;
                font-size: 12px;
                margin-bottom: 3px;
            }
        </style>
    """, unsafe_allow_html=True)

    # --- 🔄 INTERRUPTOR DE VISTA MEDIANTE SESSION STATE ---
    if "modo_vista" not in st.session_state:
        st.session_state.modo_vista = "edicion"  # Opciones: 'edicion' o 'previa'

    # --- INITIALIZACIÓN CON CAMPOS EN BLANCO (MUESTRAN SUGERENCIAS) ---
    if "meta_presupuesto" not in st.session_state:
        st.session_state.meta_presupuesto = {
            "cliente": "",
            "nombre": "",
            "fecha_evento": "",
            "lugar": "",
            "fecha_larga": ""
        }

    if "secciones_presupuesto" not in st.session_state:
        st.session_state.secciones_presupuesto = [
            {"titulo": "DECORACIÓN PRINCIPAL (ALQUILER)", "df": pd.DataFrame(columns=["descripción", "medidas", "juegos/kits", "cantidad", "precio_unitario"])},
            {"titulo": "ZONA DE CENTRO DE MESA", "df": pd.DataFrame(columns=["descripción", "medidas", "juegos/kits", "cantidad", "precio_unitario"])}
        ]

    # ===================================================
    # 📝 FLUJO A: MODO DE EDICIÓN Y CARGA
    # ===================================================
    if st.session_state.modo_vista == "edicion":
        st.markdown("## 📝 Maquetación de Presupuesto")
        
        # Formulario de Metadata con Sugerencias (Placeholders)
        with st.container(border=True):
            st.markdown("#### 🏛️ Configuración de Cabecera")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.session_state.meta_presupuesto["nombre"] = st.text_input("Nombre del Presupuesto:", value=st.session_state.meta_presupuesto["nombre"], placeholder="Ej. MOD 2 DECORACIÓN COMUNIÓN")
                st.session_state.meta_presupuesto["cliente"] = st.text_input("Cliente / Razón Social:", value=st.session_state.meta_presupuesto["cliente"], placeholder="Ej. REST. LA CASONA")
            with c2:
                st.session_state.meta_presupuesto["fecha_evento"] = st.text_input("Fecha del Evento:", value=st.session_state.meta_presupuesto["fecha_evento"], placeholder="Ej. SÁBADO 25 DE JULIO DE 2026")
                st.session_state.meta_presupuesto["lugar"] = st.text_input("Lugar del Evento:", value=st.session_state.meta_presupuesto["lugar"], placeholder="Ej. LECHERÍA, ESTADO ANZOATEGUI")
            with c3:
                st.session_state.meta_presupuesto["fecha_larga"] = st.text_input("Fecha de Emisión (Tope Der.):", value=st.session_state.meta_presupuesto["fecha_larga"], placeholder="Ej. 17 de julio de 2026")
                categoria_filtro = st.selectbox("Categoría Indexación (Filtro):", ["Decoración", "Fiesta", "Alquiler", "Suministro", "Otro"])

        # Control Dinámico de Secciones (Tope Máximo 5)
        st.markdown("#### 📦 Bloques del Presupuesto")
        if st.button("➕ Añadir Nueva Sección Física", disabled=len(st.session_state.secciones_presupuesto) >= 5):
            st.session_state.secciones_presupuesto.append({
                "titulo": f"NUEVA SECCIÓN {len(st.session_state.secciones_presupuesto) + 1}",
                "df": pd.DataFrame(columns=["descripción", "medidas", "juegos/kits", "cantidad", "precio_unitario"])
            })
            st.rerun()

        # Renderizado de Tablas Dinámicas Limpias
        for idx, sec in enumerate(st.session_state.secciones_presupuesto):
            with st.container(border=True):
                col_t1, col_t2 = st.columns([5, 1])
                with col_t1:
                    tit_sec = st.text_input(f"Título de la Sección {idx+1}:", value=sec["titulo"], key=f"sec_tit_{idx}", placeholder="Ej. ZONA DE CENTRO DE MESA")
                    st.session_state.secciones_presupuesto[idx]["titulo"] = tit_sec.upper() if tit_sec else f"SECCIÓN {idx+1}"
                with col_t2:
                    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                    if st.button("🗑️", key=f"del_sec_{idx}", use_container_width=True) and len(st.session_state.secciones_presupuesto) > 1:
                        st.session_state.secciones_presupuesto.pop(idx)
                        st.rerun()

                # Editor de datos sin indexación basura de pandas
                df_editado = st.data_editor(
                    sec["df"],
                    key=f"editor_clean_{idx}",
                    num_rows="dynamic",
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "descripción": st.column_config.TextColumn("Descripción / Detalle", required=True, placeholder="Describa el artículo..."),
                        "medidas": st.column_config.TextColumn("Medidas / Notas", placeholder="Ej. 2,20 m x 1,70 m"),
                        "juegos/kits": st.column_config.NumberColumn("Juegos/Kits (Dejar vacío si es Null)", min_value=1),
                        "cantidad": st.column_config.NumberColumn("Cantidad", min_value=1, default=1),
                        "precio_unitario": st.column_config.NumberColumn("Precio Unitario ($)", min_value=0.0, format="$%.2f")
                    }
                )
                st.session_state.secciones_presupuesto[idx]["df"] = df_editado

        # --- BOTONERA INFERIOR DE ACCIÓN ---
        st.markdown("---")
        col_acc1, col_acc2 = st.columns(2)
        with col_acc1:
            if st.button("👁️ Generar Vista Previa de Impresión", type="secondary", use_container_width=True):
                st.session_state.modo_vista = "previa"
                st.rerun()
        with col_acc2:
            permite_escritura = rol_simulado in ["administrador", "gerente"]
            if st.button("💾 Guardar Directamente en Base de Datos", disabled=not permite_escritura, type="primary", use_container_width=True):
                st.success("🎉 Estructura multi-sección JSON almacenada exitosamente en la base de datos.")

    # ===================================================
    # 🖨️ FLUJO B: MODAL DE VISTA PREVIA DE IMPRESIÓN
    # ===================================================
    else:
        meta = st.session_state.meta_presupuesto
        
        # Botonera de Control de la Vista Previa (No se imprime)
        st.markdown("### 👁️ Vista Previa del Documento")
        col_pv1, col_pv2 = st.columns(2)
        with col_pv1:
            if st.button("✏️ Regresar a Modo Edición", type="secondary", use_container_width=True):
                st.session_state.modo_vista = "edicion"
                st.rerun()
        with col_pv2:
            permite_escritura = rol_simulado in ["administrador", "gerente"]
            if st.button("💾 Confirmar y Guardar Cambios en BD", disabled=not permite_escritura, type="primary", use_container_width=True):
                st.success("🎉 Presupuesto consolidado y guardado con éxito.")
        
        st.info("💡 Presiona **Ctrl + P** en tu teclado para mandar a imprimir o guardar como PDF limpio.")
        st.markdown("---")
        
        # --- LIENZO DE IMPRESIÓN ---
        st.markdown('<div class="documento-hoja">', unsafe_allow_html=True)
        
        # 1. Encabezado Corporativo
        st.image("encabezado_paleta.png", use_container_width=True)
        
        # 2. Bloques de Metadata con Orientación Exacta
        st.markdown(f"""
            <div class="meta-contenedor">
                <div class="meta-izquierda">
                    <b>{meta['nombre'] if meta['nombre'] else '[NOMBRE DEL PRESUPUESTO]'}</b><br>
                    FECHA {meta['fecha_evento'] if meta['fecha_evento'] else '[FECHA DEL EVENTO]'}<br>
                    {meta['cliente'] if meta['cliente'] else '[CLIENTE]'}, {meta['lugar'] if meta['lugar'] else '[LUGAR]'}
                </div>
                <div class="meta-derecha">
                    {meta['fecha_larga'] if meta['fecha_larga'] else '[FECHA DE EMISIÓN]'}
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # 3. Franja Verde Principal
        st.markdown(f'<div class="banner-verde-principal">PRESUPUESTO {meta["nombre"] if meta["nombre"] else ""}</div>', unsafe_allow_html=True)
        
        # 4. Tablas Físicas y Lógica del Multiplicador
        total_general = 0.0
        
        for idx_sec, sec in enumerate(st.session_state.secciones_presupuesto):
            df_sec = sec["df"]
            
            # Sombreado gris alterno de columnas si es la sección 2 o posterior
            th_style = 'style="background-color: #f2f2f2 !important;"' if idx_sec > 0 else ''
            
            html_tabla = f"""
            <table class="tabla-remastered">
                <thead>
                    <tr>
                        <th style="width: 6%; text-align: center;" {th_style}>ITEM</th>
                        <th style="text-align: left;" {th_style}>{sec['titulo']}</th>
                        <th style="width: 25%; text-align: left;" {th_style}>MEDIDAS</th>
                        <th style="width: 12%; text-align: center;" {th_style}>JUEGOS/KITS</th>
                        <th style="width: 10%; text-align: center;" {th_style}>CANTIDAD</th>
                        <th style="width: 12%; text-align: right;" {th_style}>PRECIO</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            subtotal_seccion = 0.0
            
            if not df_sec.empty:
                for i, row in enumerate(df_sec.itertuples(), start=1):
                    jk = getattr(row, 'juegos_kits', None)
                    cant = getattr(row, 'cantidad', 1)
                    pu = getattr(row, 'precio_unitario', 0.0)
                    
                    cant = cant if pd.notna(cant) else 1
                    pu = pu if pd.notna(pu) else 0.0
                    
                    # LÓGICA: Si juegos_kits es nulo/NaN/0, no multiplica en la ecuación
                    if pd.isna(jk) or jk is None or jk == 0:
                        total_fila = cant * pu
                        jk_str = ""
                    else:
                        total_fila = jk * cant * pu
                        jk_str = f"{int(jk)}"
                        
                    subtotal_seccion += total_fila
                    
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
                html_tabla += '<tr><td colspan="6" style="text-align: center; color: #a0aec0; padding: 10px;">Sección sin registros</td></tr>'
                
            html_tabla += "</tbody></table>"
            st.markdown(html_tabla, unsafe_allow_html=True)
            
            # Subtotal Vincular por Sección
            st.markdown(f"""
                <div class="fila-subtotal-seccion">
                    <span>SUB TOTAL {sec['titulo']}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span>
                    <span>${int(subtotal_seccion) if subtotal_seccion.is_integer() else f"{subtotal_seccion:,.2f}"}</span>
                </div>
            """, unsafe_allow_html=True)
            
            total_general += subtotal_seccion
            
        # 5. Franja de Gran Total
        st.markdown(f"""
            <div class="banner-total-general">
                <span>TOTAL A CANCELAR</span>
                <span>${int(total_general) if total_general.is_integer() else f"{total_general:,.2f}"}</span>
            </div>
        """, unsafe_allow_html=True)
        
        # 6. Cláusulas Fijas
        st.markdown("""
            <div class="clausulas-container">
                <div class="clausulas-header">CLAUSULAS:</div>
                <b>Las condiciones generales de nuestra oferta son las siguientes:</b><br>
                * Precios se entienden en: Dólares netos. El costo debe ser pagado el 50% a la aceptación del contrato y el otro 50% 2 días antes del evento.<br>
                * Si el pago lo realizará en bs la tasa que manejamos es Euro indicado por el Banco Central de Venezuela.<br>
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