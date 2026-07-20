# view_presupuestos_creacion.py
import streamlit as st
import pandas as pd
import os
import time

def render_creacion_presupuestos(rol_simulado):
    # --- 🎨 CONTROL DE INYECCIÓN CSS PARA AISLAMIENTO DE IMPRESIÓN ---
    st.markdown("""
        <style>
            @page {
                size: letter;
                margin-top: 1.3cm;
                margin-bottom: 1.8cm;
                margin-left: 2.0cm;
                margin-right: 2.0cm;
            }
            
            @media print {
                /* Ocultar la app completa de Streamlit (Barras, menús, botones, pie de página 'Manage app') */
                div[data-testid="stAppViewContainer"], 
                div[data-testid="stSidebar"], 
                header, 
                footer,
                .no-print,
                .stButton {
                    visibility: hidden !important;
                }
                
                /* Forzar que ÚNICAMENTE el contenedor del presupuesto sea visible en el PDF */
                .documento-hoja, .documento-hoja * {
                    visibility: visible !important;
                }
                
                .documento-hoja {
                    position: absolute;
                    left: 0;
                    top: 0;
                    width: 100%;
                    background-color: #ffffff !important;
                }
                
                tr { page-break-inside: avoid; }
                .contenedor-subtotal { page-break-inside: avoid; }
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
                table-layout: fixed;
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
                word-wrap: break-word;
            }

            .contenedor-subtotal {
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
                white-space: pre-line;
            }
            .clausulas-header {
                color: #d53f8c;
                font-weight: bold;
                font-size: 12px;
                margin-bottom: 3px;
            }
        </style>
    """, unsafe_allow_html=True)

    # --- 🔄 CONTROL DE ESTADOS ---
    if "modo_vista" not in st.session_state:
        st.session_state.modo_vista = "edicion"

    if "meta_presupuesto" not in st.session_state:
        st.session_state.meta_presupuesto = {"cliente": "", "nombre": "", "fecha_evento": "", "lugar": "", "fecha_larga": ""}

    if "clausulas_presupuesto" not in st.session_state:
        st.session_state.clausulas_presupuesto = (
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

    # REGLA: 1 Sola sección inicial por defecto
    if "lista_secciones" not in st.session_state:
        st.session_state.lista_secciones = [
            {"id": "sec_inicial_1", "titulo": "DECORACIÓN PRINCIPAL (ALQUILER)"}
        ]
        st.session_state["df_sec_inicial_1"] = pd.DataFrame(columns=["descripción", "medidas", "juegos/kits", "cantidad", "precio_unitario"])

    # ===================================================
    # 📝 MODO EDICIÓN
    # ===================================================
    if st.session_state.modo_vista == "edicion":
        st.markdown("## 📝 Maquetación de Presupuesto")
        
        with st.container(border=True):
            st.markdown("#### 🏛️ Datos de Cabecera")
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

        for idx, sec in enumerate(st.session_state.lista_secciones):
            sec_id = sec["id"]
            df_key = f"df_{sec_id}"
            
            max_filas = 15 if idx == 0 else (7 if idx == 1 else 5)
                
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
                    st.error(f"⚠️ Sección limitada a {max_filas} líneas.")
                    st.session_state[f"final_{df_key}"] = df_vivo.head(max_filas)
                else:
                    st.session_state[f"final_{df_key}"] = df_vivo

        with st.container(border=True):
            st.markdown("#### 📜 Términos y Cláusulas")
            st.session_state.clausulas_presupuesto = st.text_area("Modifique cláusulas si es necesario:", value=st.session_state.clausulas_presupuesto, height=150)

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
            if st.button("💾 Guardar en BD", disabled=rol_simulado not in ["administrador", "gerente"], type="primary", use_container_width=True):
                st.success("🎉 Guardado.")

    # ===================================================
    # 🖨️ MODO VISTA PREVIA (CONSOLIDACIÓN DE CADENA HTML)
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
            st.button("💾 Confirmar y Guardar en Supabase", disabled=True, type="primary", use_container_width=True)
        
        st.info("💡 Para guardar el PDF limpio: Presiona **Ctrl + P** o **Cmd + P**.")
        st.markdown("---")
        
# --- 🏗️ CONSTRUCCIÓN CONSOLIDADA DEL HTML DE IMPRESIÓN ---
        ruta_logo = os.path.join(os.path.dirname(__file__), "encabezado_paleta.png")
        
        if os.path.exists(ruta_logo):
            import base64
            with open(ruta_logo, "rb") as f:
                data_img = base64.b64encode(f.read()).decode("utf-8")
            html_logo = f'<img src="data:image/png;base64,{data_img}" style="width:100%; height:auto; display:block; margin-bottom:10px;">'
        else:
            html_logo = '<div style="background-color:#f2f2f2; border:2px dashed #cbd5e1; padding:20px; text-align:center; font-weight:bold; color:#64748b; margin-bottom:10px;">[ LOGO: encabezado_paleta.png NO DETECTADO ]</div>'

        # Construcción limpia de la cabecera
        html_cuerpo = f"""
        <div class="documento-hoja">
            {html_logo}
            <div class="meta-contenedor">
                <div class="meta-izquierda">
                    <b>{meta['nombre'].upper() if meta['nombre'] else 'PRESUPUESTO'}</b><br>
                    FECHA DEL EVENTO: {meta['fecha_evento'].upper() if meta['fecha_evento'] else 'N/A'}<br>
                    CLIENTE: {meta['cliente'].upper() if meta['cliente'] else 'N/A'} | LUGAR: {meta['lugar'].upper() if meta['lugar'] else 'N/A'}
                </div>
                <div class="meta-derecha">
                    EMISIÓN: {meta['fecha_larga'] if meta['fecha_larga'] else 'N/A'}
                </div>
            </div>
            <div class="banner-verde-principal">PRESUPUESTO DETALLADO</div>
        """
        
        total_general = 0.0
        
        for idx_sec, sec in enumerate(st.session_state.lista_secciones):
            df_sec = st.session_state[f"df_{sec['id']}"]
            th_style = 'style="background-color: #f2f2f2 !important;"' if idx_sec > 0 else ''
            
            html_cuerpo += f"""
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
            item_numeral = 1
            
            # Iteración blindada basada en diccionarios para evitar el bug de indices cruzados
            for row in df_sec.to_dict('records'):
                desc = str(row.get('descripción', '') or '').strip()
                med = str(row.get('medidas', '') or '').strip()
                
                try: jk_val = float(row.get('juegos/kits')) if pd.notna(row.get('juegos/kits')) and row.get('juegos/kits') != '' else 0.0
                except: jk_val = 0.0
                try: cant_val = float(row.get('cantidad')) if pd.notna(row.get('cantidad')) and row.get('cantidad') != '' else 0.0
                except: cant_val = 0.0
                try: pu_val = float(row.get('precio_unitario')) if pd.notna(row.get('precio_unitario')) and row.get('precio_unitario') != '' else 0.0
                except: pu_val = 0.0

                # Auto-numera solo si la fila tiene alguna actividad real o precio válido
                if desc or med or jk_val or cant_val or pu_val:
                    if jk_val == 0.0:
                        total_fila = cant_val * pu_val
                        jk_str = ""
                    else:
                        total_fila = jk_val * cant_val * pu_val
                        jk_str = f"{int(jk_val) if jk_val.is_integer() else jk_val}"
                        
                    subtotal_seccion += total_fila
                    precio_str = f"${total_fila:,.2f}"
                    cant_str = f"{int(cant_val) if cant_val.is_integer() else cant_val}" if cant_val > 0 else ""
                    
                    html_cuerpo += f"""
                    <tr>
                        <td style="text-align: center;">{item_numeral}</td>
                        <td style="text-align: left;">{desc}</td>
                        <td style="text-align: left;">{med}</td>
                        <td style="text-align: center;">{jk_str}</td>
                        <td style="text-align: center;">{cant_str}</td>
                        <td style="text-align: right;">{precio_str}</td>
                    </tr>
                    """
                    item_numeral += 1
            
            if item_numeral == 1:
                html_cuerpo += '<tr><td colspan="6" style="text-align: center; color: #a0aec0; padding: 8px;">Sección sin registros activos</td></tr>'
                
            html_cuerpo += f"""
                </tbody>
            </table>
            <div class="contenedor-subtotal">
                <span>SUB TOTAL {sec['titulo']}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span>
                <span>${subtotal_seccion:,.2f}</span>
            </div>
            """
            total_general += subtotal_seccion
            
        html_cuerpo += f"""
            <div class="banner-total-general">
                <span>TOTAL A CANCELAR</span>
                <span>${total_general:,.2f}</span>
            </div>
            <div class="clausulas-container">
                <div class="clausulas-header">CLAUSULAS:</div>
                {st.session_state.clausulas_presupuesto}
            </div>
        </div>
        """
        
        # Renderizado final absoluto y limpio
        st.markdown(html_cuerpo, unsafe_allow_html=True)
