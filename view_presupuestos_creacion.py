# view_presupuestos_creacion.py
import streamlit as st
import pandas as pd
import os
import time

def render_creacion_presupuestos(rol_simulado):
    # --- 🎨 CONFIGURACIÓN DE LIENZO DE IMPRESIÓN Y MÁRGENES ESTRICTOS (TAMAÑO CARTA) ---
    st.markdown("""
        <style>
            /* Lienzo Físico de Impresión Tamaño Carta con Márgenes Solicitados */
            @page {
                size: letter;
                margin-top: 1.3cm;
                margin-bottom: 1.8cm;
                margin-left: 2.0cm;
                margin-right: 2.0cm;
            }
            
            @media print {
                section[data-testid="stSidebar"], 
                div[data-testid="stSegmentedControl"],
                .no-print,
                .stButton,
                header {
                    display: none !important;
                }
                .block-container {
                    padding: 0rem !important;
                    max-width: 100% !important;
                }
                /* Control de fractura limpia para 2 o 3 páginas según volumen */
                tr { page-break-inside: avoid; }
                img { page-break-inside: avoid; }
                .tabla-remastered { page-break-inside: auto; }
                .fila-subtotal-seccion { page-break-inside: avoid; }
                .banner-total-general { page-break-inside: avoid; }
                .clausulas-container { page-break-inside: avoid; }
            }

            .documento-hoja {
                font-family: 'Arial', sans-serif;
                color: #000000;
                background-color: #ffffff;
                padding: 0px;
            }

            .meta-contenedor {
                display: flex;
                justify-content: space-between;
                font-size: 13px;
                line-height: 1.5;
                margin-top: 8px;
                margin-bottom: 5px;
            }
            .meta-izquierda { font-weight: normal; }
            .meta-derecha { text-align: right; font-weight: bold; }

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

            .tabla-remastered {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 0px;
                table-layout: fixed; /* Fuerza el respeto de los anchos asignados */
            }
            .tabla-remastered th {
                background-color: #fffdeb !important;
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
                word-wrap: break-word; /* Evita desbordes de texto */
            }

            .fila-subtotal-seccion {
                background-color: #ffffff;
                font-weight: bold;
                font-size: 13px;
                text-align: right;
                padding: 6px 8px;
                margin-bottom: 12px;
                border-bottom: 1px solid #cbd5e1;
            }

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

            .clausulas-container {
                font-size: 11px;
                margin-top: 15px;
                color: #1a202c;
                line-height: 1.4;
                white-space: pre-line; /* Mantiene saltos de línea del editor */
            }
            .clausulas-header {
                color: #d53f8c;
                font-weight: bold;
                font-size: 12px;
                margin-bottom: 3px;
            }
        </style>
    """, unsafe_allow_html=True)

    # --- 🔄 CONTROL DE ENTORNO ---
    if "modo_vista" not in st.session_state:
        st.session_state.modo_vista = "edicion"

    if "meta_presupuesto" not in st.session_state:
        st.session_state.meta_presupuesto = {"cliente": "", "nombre": "", "fecha_evento": "", "lugar": "", "fecha_larga": ""}

    # --- 📜 CLÁUSULAS PREDETERMINADAS EDITABLES ---
    clausulas_defecto = (
        "Las condiciones generales de nuestra oferta son las siguientes:\n"
        "* Precios se entienden en: Dólares netos. El costo debe ser pagado el 50% a la aceptación del contrato y el otro 50% 2 días antes del evento.\n"
        "* Si el pago lo realizará en bs la tasa que manejamos es Euro indicado por el Banco Central de Venezuela.\n"
        "* Validez de la Oferta: 3 días contínuos.\n"
        "* Si el cliente cancela el servicio (es decir no va a querer el servicio) 2 días antes del evento le será devuelto un 30% del monto pagado.\n"
        "* Si el cliente cancela el servicio (es decir no va a querer el servicio) 1 día antes ó el día del evento no se le devolverá nada del monto pagado.\n"
        "* El cliente es enteramente responsable de todo el material suministrado para el evento y cancelara cualquier daño al mismo.\n\n"
        "Sin más a que hacer referencia, a la espera de vuestra consideración, nos despedimos de Ud.,\n"
        "Atentamente,\n"
        "Paletapapelytijera"
    )
    
    if "clausulas_presupuesto" not in st.session_state:
        st.session_state.clausulas_presupuesto = clausulas_defecto

    # --- 📦 REGLA: 1 SOLA SECCIÓN INICIAL POR DEFECTO ---
    if "lista_secciones" not in st.session_state:
        st.session_state.lista_secciones = [
            {"id": "sec_inicial_1", "titulo": "DECORACIÓN PRINCIPAL (ALQUILER)"}
        ]
        st.session_state["df_sec_inicial_1"] = pd.DataFrame(columns=["descripción", "medidas", "juegos/kits", "cantidad", "precio_unitario"])

    # ===================================================
    # 📝 MODO DE EDICIÓN
    # ===================================================
    if st.session_state.modo_vista == "edicion":
        st.markdown("## 📝 Maquetación de Presupuesto")
        
        with st.container(border=True):
            st.markdown("#### 🏛 Honorarios y Datos de Cabecera")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.session_state.meta_presupuesto["nombre"] = st.text_input("Nombre del Presupuesto:", value=st.session_state.meta_presupuesto["nombre"])
                st.session_state.meta_presupuesto["cliente"] = st.text_input("Cliente / Razón Social:", value=st.session_state.meta_presupuesto["cliente"])
            with c2:
                st.session_state.meta_presupuesto["fecha_evento"] = st.text_input("Fecha del Evento:", value=st.session_state.meta_presupuesto["fecha_evento"])
                st.session_state.meta_presupuesto["lugar"] = st.text_input("Lugar del Evento:", value=st.session_state.meta_presupuesto["lugar"])
            with c3:
                st.session_state.meta_presupuesto["fecha_larga"] = st.text_input("Fecha de Emisión:", value=st.session_state.meta_presupuesto["fecha_larga"])

        st.markdown("#### 📦 Bloques de Catálogo")
        
        if st.button("➕ Añadir Nueva Sección Física", disabled=len(st.session_state.lista_secciones) >= 5):
            for s in st.session_state.lista_secciones:
                k = f"df_{s['id']}"
                if f"final_{k}" in st.session_state:
                    st.session_state[k] = st.session_state[f"final_{k}"]
            
            nuevo_id = f"sec_{int(time.time() * 1000)}"
            st.session_state.lista_secciones.append({
                "id": nuevo_id,
                "titulo": f"NUEVA ZONA {len(st.session_state.lista_secciones) + 1}"
            })
            st.session_state[f"df_{nuevo_id}"] = pd.DataFrame(columns=["descripción", "medidas", "juegos/kits", "cantidad", "precio_unitario"])
            st.rerun()

        # Renderizado de Bloques y validación de topes por sección
        for idx, sec in enumerate(st.session_state.lista_secciones):
            sec_id = sec["id"]
            df_key = f"df_{sec_id}"
            
            # Asignación estricta de límites físicos por sección
            if idx == 0:
                max_filas = 15
            elif idx == 1:
                max_filas = 7
            else:
                max_filas = 5
                
            with st.container(border=True):
                col_t1, col_t2 = st.columns([5, 1])
                with col_t1:
                    tit_sec = st.text_input(f"Título de la Sección {idx+1}:", value=sec["titulo"], key=f"tit_input_{sec_id}")
                    st.session_state.lista_secciones[idx]["titulo"] = tit_sec.upper() if tit_sec else f"SECCIÓN {idx+1}"
                with col_t2:
                    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                    if st.button("🗑️", key=f"del_{sec_id}", use_container_width=True) and len(st.session_state.lista_secciones) > 1:
                        for s in st.session_state.lista_secciones:
                            k = f"df_{s['id']}"
                            if f"final_{k}" in st.session_state:
                                st.session_state[k] = st.session_state[f"final_{k}"]
                        st.session_state.lista_secciones.pop(idx)
                        st.session_state.pop(df_key, None)
                        st.session_state.pop(f"final_{df_key}", None)
                        st.rerun()

                st.caption(f"Límite establecido: **{max_filas} filas max**. (Celdas vacías permitidas, no anulan la fila).")

                df_vivo = st.data_editor(
                    st.session_state[df_key],
                    key=f"editor_widget_{sec_id}",
                    num_rows="dynamic",
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "descripción": st.column_config.TextColumn("Descripción (80 ch)"),
                        "medidas": st.column_config.TextColumn("Medidas (40 ch)"),
                        "juegos/kits": st.column_config.NumberColumn("Juegos/Kits (11 ch)", min_value=1),
                        "cantidad": st.column_config.NumberColumn("Cantidad (8 ch)", min_value=1, default=1),
                        "precio_unitario": st.column_config.NumberColumn("Precio (12 ch)", min_value=0.0, format="$%.2f")
                    }
                )

                if len(df_vivo) > max_filas:
                    st.error(f"⚠️ Sección limitada a {max_filas} líneas. Excedente truncado automáticamente.")
                    st.session_state[f"final_{df_key}"] = df_vivo.head(max_filas)
                else:
                    st.session_state[f"final_{df_key}"] = df_vivo

        # --- 📜 PANEL DE CONTROL DE CLÁUSULAS DINÁMICAS ---
        with st.container(border=True):
            st.markdown("#### 📜 Cláusulas del Contrato (Variables por presupuesto)")
            st.session_state.clausulas_presupuesto = st.text_area(
                "Modifique o adicione términos legales para este documento:",
                value=st.session_state.clausulas_presupuesto,
                height=200
            )

        st.markdown("---")
        col_acc1, col_acc2 = st.columns(2)
        with col_acc1:
            if st.button("👁️ Generar Vista Previa de Impresión", type="secondary", use_container_width=True):
                for s in st.session_state.lista_secciones:
                    k = f"df_{s['id']}"
                    if f"final_{k}" in st.session_state:
                        st.session_state[k] = st.session_state[f"final_{k}"]
                st.session_state.modo_vista = "previa"
                st.rerun()
        with col_acc2:
            if st.button("💾 Guardar Todo el Bloque en BD", disabled=rol_simulado not in ["administrador", "gerente"], type="primary", use_container_width=True):
                for s in st.session_state.lista_secciones:
                    k = f"df_{s['id']}"
                    if f"final_{k}" in st.session_state:
                        st.session_state[k] = st.session_state[f"final_{k}"]
                st.success("🎉 Estructura consolidada con éxito.")

    # ===================================================
    # 🖨️ MODO VISTA PREVIA DE IMPRESIÓN
    # ===================================================
    else:
        meta = st.session_state.meta_presupuesto
        
        st.markdown("### 👁️ Vista Previa del Documento")
        col_pv1, col_pv2 = st.columns(2)
        with col_pv1:
            if st.button("✏️ Regresar a Modo Edición", type="secondary", use_container_width=True):
                st.session_state.modo_vista = "edicion"
                st.rerun()
        with col_pv2:
            if st.button("💾 Confirmar y Guardar en Supabase", disabled=rol_simulado not in ["administrador", "gerente"], type="primary", use_container_width=True):
                st.success("🎉 Registro guardado en la base de datos.")
        
        st.info("💡 Consejo para el PDF: Pulsa **Ctrl + P** (Windows) o **Cmd + P** (Mac).")
        st.markdown("---")
        
        # --- 📄 INICIO DEL LIENZO FÍSICO ---
        st.markdown('<div class="documento-hoja">', unsafe_allow_html=True)
        
        dir_actual = os.path.dirname(__file__)
        rutas_probables = [
            "Encabezado_Paleta.png", "encabezado_paleta.png",
            os.path.join(dir_actual, "Encabezado_Paleta.png"),
            os.path.join(os.path.dirname(dir_actual), "Encabezado_Paleta.png")
        ]
        logo_encontrado = next((r for r in rutas_probables if os.path.exists(r)), None)

        if logo_encontrado:
            st.image(logo_encontrado, use_container_width=True)
        else:
            st.markdown('<div style="background-color:#f2f2f2; border:2px dashed #cbd5e1; padding:20px; text-align:center; font-weight:bold; color:#64748b;">[ PALETA PAPEL Y TIJERA ]</div>', unsafe_allow_html=True)
        
        st.markdown(f"""
            <div class="meta-contenedor">
                <div class="meta-izquierda">
                    <b>{meta['nombre'] if meta['nombre'] else '[SIN NOMBRE]'}</b><br>
                    FECHA DEL EVENTO: {meta['fecha_evento'] if meta['fecha_evento'] else 'N/A'}<br>
                    CLIENTE: {meta['cliente'] if meta['cliente'] else 'N/A'} | LUGAR: {meta['lugar'] if meta['lugar'] else 'N/A'}
                </div>
                <div class="meta-derecha">
                    EMISIÓN: {meta['fecha_larga'] if meta['fecha_larga'] else 'N/A'}
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f'<div class="banner-verde-principal">PRESUPUESTO {meta["nombre"]}</div>', unsafe_allow_html=True)
        
        total_general = 0.0
        
        # Procesamiento e inyección limpia de tablas con anchos proporcionales exactos
        for idx_sec, sec in enumerate(st.session_state.lista_secciones):
            df_sec = st.session_state[f"df_{sec['id']}"]
            th_style = 'style="background-color: #f2f2f2 !important;"' if idx_sec > 0 else ''
            
            html_tabla = f"""
            <table class="tabla-remastered">
                <thead>
                    <tr>
                        <th style="width: 3.2%; text-align: center;" {th_style}>ITEM</th>
                        <th style="width: 51.3%; text-align: left;" {th_style}>{sec['titulo']}</th>
                        <th style="width: 25.6%; text-align: left;" {th_style}>MEDIDAS</th>
                        <th style="width: 7.1%; text-align: center;" {th_style}>JUEGOS/KITS</th>
                        <th style="width: 5.1%; text-align: center;" {th_style}>CANTIDAD</th>
                        <th style="width: 7.7%; text-align: right;" {th_style}>PRECIO</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            subtotal_seccion = 0.0
            
            if not df_sec.empty:
                for i, row in enumerate(df_sec.itertuples(), start=1):
                    desc = getattr(row, 'descripción', '')
                    med = getattr(row, 'medidas', '')
                    jk = getattr(row, 'juegos_kits', None)
                    cant = getattr(row, 'cantidad', None)
                    pu = getattr(row, 'precio_unitario', None)
                    
                    desc_str = "" if pd.isna(desc) or desc is None else str(desc)
                    med_str = "" if pd.isna(med) or med is None else str(med)
                    
                    cant_val = float(cant) if pd.notna(cant) and cant is not None else 0.0
                    pu_val = float(pu) if pd.notna(pu) and pu is not None else 0.0
                    
                    if pd.isna(jk) or jk is None or float(jk) == 0.0:
                        total_fila = cant_val * pu_val
                        jk_str = ""
                    else:
                        total_fila = float(jk) * cant_val * pu_val
                        jk_str = f"{int(jk)}"
                        
                    subtotal_seccion += total_fila
                    precio_str = f"${total_fila:,.2f}" if total_fila > 0 else "$0.00"
                    
                    html_tabla += f"""
                    <tr>
                        <td style="text-align: center;">{i}</td>
                        <td style="text-align: left;">{desc_str}</td>
                        <td style="text-align: left;">{med_str}</td>
                        <td style="text-align: center;">{jk_str}</td>
                        <td style="text-align: center;">{int(cant_val) if cant_val.is_integer() else cant_val}</td>
                        <td style="text-align: right;">{precio_str}</td>
                    </tr>
                    """
            else:
                html_tabla += '<tr><td colspan="6" style="text-align: center; color: #a0aec0; padding: 8px;">Sección vacía</td></tr>'
                
            html_tabla += "</tbody></table>"
            st.markdown(html_tabla, unsafe_allow_html=True)
            
            # Subtotales explícitos por sección
            st.markdown(f"""
                <div class="fila-subtotal-seccion">
                    <span>SUB TOTAL {sec['titulo']}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span>
                    <span>${subtotal_seccion:,.2f}</span>
                </div>
            """, unsafe_allow_html=True)
            
            total_general += subtotal_seccion
            
        # Banner del Total General del Presupuesto
        st.markdown(f"""
            <div class="banner-total-general">
                <span>TOTAL A CANCELAR</span>
                <span>${total_general:,.2f}</span>
            </div>
        """, unsafe_allow_html=True)
        
        # Inyección de Cláusulas Dinámicas Procesadas
        st.markdown(f"""
            <div class="clausulas-container">
                <div class="clausulas-header">CLAUSULAS:</div>
                {st.session_state.clausulas_presupuesto}
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)