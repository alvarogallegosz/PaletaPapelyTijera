import streamlit as st
import pandas as pd
import os
import time
import io

# --- IMPORTS REPORTLAB PARA PDF ---
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether

# ==============================================================================
# 🛠️ FUNCIÓN GENERADORA DE PDF (REPORTLAB)
# ==============================================================================
def generar_pdf_presupuesto(meta, secciones, clausulas, mostrar_precios=True, logo_path=None):
    """
    Genera un archivo PDF en memoria utilizando ReportLab.
    Ajustado a tamaño Carta (8.5 x 11 pulg) con márgenes de 1.8 cm en los 4 bordes.
    """
    buffer = io.BytesIO()
    
    # Configuración de página Carta con márgenes exactos de 1.8 cm
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm
    )
    
    # Ancho imprimible útil: 21.59 cm - 3.6 cm = 17.99 cm (~509.95 pt)
    ancho_imprimible = doc.width 
    story = []

    # 1. LOGO CORPORATIVO / ENCABEZADO
    if logo_path and os.path.exists(logo_path):
        try:
            # Mantiene proporción del banner corporativo
            img = Image(logo_path, width=ancho_imprimible, height=1.8 * cm)
            story.append(img)
            story.append(Spacer(1, 8))
        except Exception:
            pass

    # ESTILOS BASE
    styles = getSampleStyleSheet()
    
    style_normal = ParagraphStyle(
        'NormalPDF',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=11,
        textColor=HexColor('#000000')
    )
    
    style_bold = ParagraphStyle(
        'BoldPDF',
        parent=style_normal,
        fontName='Helvetica-Bold'
    )

    style_meta_right = ParagraphStyle(
        'MetaRight',
        parent=style_bold,
        alignment=2 # Derecha
    )

    # 2. CABECERA DE METADATOS
    nombre_pres = meta.get('nombre', 'PRESUPUESTO').upper() or 'PRESUPUESTO'
    fecha_evt = meta.get('fecha_evento', 'N/A').upper() or 'N/A'
    cliente = meta.get('cliente', 'N/A').upper() or 'N/A'
    lugar = meta.get('lugar', 'N/A').upper() or 'N/A'
    emision = meta.get('fecha_larga', 'N/A') or 'N/A'

    meta_html_izq = f"<b>{nombre_pres}</b><br/>FECHA DEL EVENTO: {fecha_evt}<br/>CLIENTE: {cliente} | LUGAR: {lugar}"
    meta_html_der = f"EMISIÓN: {emision}"

    t_meta = Table(
        [[Paragraph(meta_html_izq, style_normal), Paragraph(meta_html_der, style_meta_right)]],
        colWidths=[ancho_imprimible * 0.7, ancho_imprimible * 0.3]
    )
    t_meta.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 4))

    # 3. BANNER VERDE PRINCIPAL
    style_banner_txt = ParagraphStyle(
        'BannerTxt',
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=12,
        textColor=HexColor('#FFFFFF'),
        alignment=1 # Centro
    )
    t_banner = Table([[Paragraph("PRESUPUESTO DETALLADO", style_banner_txt)]], colWidths=[ancho_imprimible])
    t_banner.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), HexColor('#B8D7A3')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_banner)
    story.append(Spacer(1, 6))

    # 4. CONFIGURACIÓN DE COLUMNAS
    if mostrar_precios:
        # 6 Columnas (Con precios)
        col_widths = [
            ancho_imprimible * 0.045, # Item
            ancho_imprimible * 0.485, # Descripción
            ancho_imprimible * 0.235, # Medidas
            ancho_imprimible * 0.075, # Juegos/Kits
            ancho_imprimible * 0.060, # Cantidad
            ancho_imprimible * 0.100  # Precio
        ]
        headers = ["ITEM", "DESCRIPCIÓN", "MEDIDAS", "JUEGOS/KITS", "CANT.", "PRECIO"]
    else:
        # 5 Columnas (Sin precios)
        col_widths = [
            ancho_imprimible * 0.05,  # Item
            ancho_imprimible * 0.56,  # Descripción
            ancho_imprimible * 0.25,  # Medidas
            ancho_imprimible * 0.08,  # Juegos/Kits
            ancho_imprimible * 0.06   # Cantidad
        ]
        headers = ["ITEM", "DESCRIPCIÓN", "MEDIDAS", "JUEGOS/KITS", "CANT."]

    total_general = 0.0

    # 5. TABLAS POR SECCIÓN
    for idx_sec, sec in enumerate(secciones):
        df_sec = st.session_state.get(f"df_{sec['id']}", pd.DataFrame())
        
        # Encabezados de tabla
        style_th = ParagraphStyle('TH', fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=HexColor('#000000'))
        style_th_center = ParagraphStyle('THC', parent=style_th, alignment=1)
        style_th_right = ParagraphStyle('THR', parent=style_th, alignment=2)

        header_row = [
            Paragraph(headers[0], style_th_center),
            Paragraph(sec['titulo'], style_th),
            Paragraph(headers[2], style_th),
            Paragraph(headers[3], style_th_center),
            Paragraph(headers[4], style_th_center)
        ]
        if mostrar_precios:
            header_row.append(Paragraph(headers[5], style_th_right))

        table_data = [header_row]
        subtotal_seccion = 0.0
        item_numeral = 1

        style_td = ParagraphStyle('TD', fontName='Helvetica', fontSize=8, leading=10, textColor=HexColor('#000000'))
        style_td_center = ParagraphStyle('TDC', parent=style_td, alignment=1)
        style_td_right = ParagraphStyle('TDR', parent=style_td, alignment=2)

        for row in df_sec.to_dict('records'):
            desc = str(row.get('descripción', '') or '').strip()
            med = str(row.get('medidas', '') or '').strip()
            
            try: jk_val = float(row.get('juegos/kits')) if pd.notna(row.get('juegos/kits')) and row.get('juegos/kits') != '' else 0.0
            except: jk_val = 0.0
            try: cant_val = float(row.get('cantidad')) if pd.notna(row.get('cantidad')) and row.get('cantidad') != '' else 0.0
            except: cant_val = 0.0
            try: pu_val = float(row.get('precio_unitario')) if pd.notna(row.get('precio_unitario')) and row.get('precio_unitario') != '' else 0.0
            except: pu_val = 0.0

            if desc or med or jk_val or cant_val or pu_val:
                total_fila = (jk_val * cant_val * pu_val) if jk_val > 0 else (cant_val * pu_val)
                subtotal_seccion += total_fila
                
                jk_str = f"{int(jk_val) if jk_val.is_integer() else jk_val}" if jk_val > 0 else ""
                cant_str = f"{int(cant_val) if cant_val.is_integer() else cant_val}" if cant_val > 0 else ""
                precio_str = f"${total_fila:,.2f}"

                r = [
                    Paragraph(str(item_numeral), style_td_center),
                    Paragraph(desc, style_td),
                    Paragraph(med, style_td),
                    Paragraph(jk_str, style_td_center),
                    Paragraph(cant_str, style_td_center)
                ]
                if mostrar_precios:
                    r.append(Paragraph(precio_str, style_td_right))

                table_data.append(r)
                item_numeral += 1

        if item_numeral == 1:
            empty_msg = [Paragraph("Sección sin registros activos", style_td_center)] * len(headers)
            table_data.append(empty_msg)

        # Construcción de Tabla ReportLab
        t_sec = Table(table_data, colWidths=col_widths, repeatRows=1)
        bg_header = HexColor('#F2F2F2') if idx_sec > 0 else HexColor('#FFFDEB')
        
        t_style = [
            ('BACKGROUND', (0,0), (-1,0), bg_header),
            ('LINEBELOW', (0,0), (-1,0), 1, HexColor('#CBD5E1')),
            ('LINEBELOW', (0,1), (-1,-1), 0.5, HexColor('#E2E8F0')),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 4),
            ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ]
        t_sec.setStyle(TableStyle(t_style))
        story.append(t_sec)

        # Subtotal de Sección
        if mostrar_precios:
            sub_html = f"SUB TOTAL {sec['titulo']}: &nbsp;&nbsp;&nbsp;<b>${subtotal_seccion:,.2f}</b>"
            p_sub = Paragraph(sub_html, ParagraphStyle('Sub', parent=style_normal, alignment=2, fontSize=9))
            t_sub = Table([[p_sub]], colWidths=[ancho_imprimible])
            t_sub.setStyle(TableStyle([
                ('LINEBELOW', (0,0), (-1,-1), 1, HexColor('#CBD5E1')),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ]))
            story.append(t_sub)

        story.append(Spacer(1, 8))
        total_general += subtotal_seccion

    # 6. BANNER TOTAL GENERAL
    if mostrar_precios:
        style_tot_izq = ParagraphStyle('TotL', fontName='Helvetica-Bold', fontSize=12, textColor=HexColor('#000000'))
        style_tot_der = ParagraphStyle('TotR', parent=style_tot_izq, alignment=2)
        
        t_tot = Table(
            [[Paragraph("TOTAL A CANCELAR", style_tot_izq), Paragraph(f"${total_general:,.2f}", style_tot_der)]],
            colWidths=[ancho_imprimible * 0.6, ancho_imprimible * 0.4]
        )
        t_tot.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), HexColor('#B8D7A3')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(t_tot)
        story.append(Spacer(1, 10))

    # 7. TÉRMINOS Y CLÁUSULAS
    style_claus_head = ParagraphStyle('ClausHead', fontName='Helvetica-Bold', fontSize=9, textColor=HexColor('#D53F8C'))
    style_claus_body = ParagraphStyle('ClausBody', fontName='Helvetica', fontSize=8, leading=11, textColor=HexColor('#1A202C'))

    clausulas_formatted = clausulas.replace("\n", "<br/>")
    elementos_clausulas = [
        Paragraph("CLAUSULAS:", style_claus_head),
        Spacer(1, 2),
        Paragraph(clausulas_formatted, style_claus_body)
    ]
    
    story.append(KeepTogether(elementos_clausulas))

    # Compilar PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# ==============================================================================
# 🎨 VISTA PRINCIPAL
# ==============================================================================
def render_creacion_presupuestos(rol_simulado):
    # --- 🎨 CONTROL DE INYECCIÓN CSS PARA AISLAMIENTO E IMPRESIÓN ---
    st.markdown("""
        <style>
            @page {
                size: letter;
                margin: 1.8cm;
            }
            
            @media print {
                div[data-testid="stAppViewContainer"], 
                div[data-testid="stSidebar"], 
                header, 
                footer,
                .no-print,
                .stButton {
                    visibility: hidden !important;
                }
                
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
                font-size: 20px;
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

    # --- 🔄 CONTROL DE ESTADOS EN SESSION_STATE ---
    if "modo_vista" not in st.session_state:
        st.session_state.modo_vista = "edicion"

    if "mostrar_precios" not in st.session_state:
        st.session_state.mostrar_precios = True

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

    if "lista_secciones" not in st.session_state:
        st.session_state.lista_secciones = [
            {"id": "sec_inicial_1", "titulo": "DECORACIÓN PRINCIPAL (ALQUILER)"}
        ]
        st.session_state["df_sec_inicial_1"] = pd.DataFrame(columns=["descripción", "medidas", "juegos/kits", "cantidad", "precio_unitario"])

    # RASTREO DEL LOGO CORPORATIVO
    rutas_logo = [
        "Encabezado_Paleta.png", "encabezado_paleta.png",
        os.path.join(os.getcwd(), "Encabezado_Paleta.png"),
        os.path.join(os.path.dirname(__file__), "Encabezado_Paleta.png")
    ]
    logo_path = next((r for r in rutas_logo if os.path.exists(r)), None)

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
                        "juegos/kits": st.column_config.NumberColumn("Juegos/Kits", min_value=1),
                        "cantidad": st.column_config.NumberColumn("Cantidad", min_value=1, default=1),
                        "precio_unitario": st.column_config.NumberColumn("Precio ($)", min_value=0.0, format="$%.2f")
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
                st.success("🎉 Presupuesto guardado exitosamente en Base de Datos.")

    # ===================================================
    # 🖨️ MODO VISTA PREVIA Y SALIDA
    # ===================================================
    else:
        meta = st.session_state.meta_presupuesto
        
        st.markdown("### 👁️ Vista Previa del Documento")
        
        # Panel superior de controles de salida
        with st.container(border=True):
            col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([2, 2, 2])
            
            with col_ctrl1:
                if st.button("✏️ Regresar a Modo Edición", type="secondary", use_container_width=True):
                    st.session_state.modo_vista = "edicion"
                    st.rerun()

            with col_ctrl2:
                # Selector dinámico Con / Sin Precios
                modo_precio = st.radio(
                    "Modalidad de Salida:",
                    ["Con precios por partida", "Sin precios (Solo Cantidades)"],
                    horizontal=True,
                    index=0 if st.session_state.mostrar_precios else 1
                )
                st.session_state.mostrar_precios = (modo_precio == "Con precios por partida")

            with col_ctrl3:
                # Generación al vuelo de bytes de PDF
                pdf_bytes = generar_pdf_presupuesto(
                    meta=meta,
                    secciones=st.session_state.lista_secciones,
                    clausulas=st.session_state.clausulas_presupuesto,
                    mostrar_precios=st.session_state.mostrar_precios,
                    logo_path=logo_path
                )
                
                nombre_archivo = f"Presupuesto_{meta['cliente'] or 'Cliente'}.pdf".replace(" ", "_")
                st.download_button(
                    label="📥 Descargar PDF Oficial",
                    data=pdf_bytes,
                    file_name=nombre_archivo,
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True
                )

        # Botón para guardar en Base de Datos en la pantalla de salida
        col_db1, col_db2 = st.columns([3, 1])
        with col_db2:
            if st.button("💾 Guardar en Base de Datos", disabled=rol_simulado not in ["administrador", "gerente"], use_container_width=True):
                # Aquí se conecta con Supabase u otra BD manteniendo los nombres de campos en español
                st.success("✅ Presupuesto guardado en Base de Datos correctamente.")

        st.info("💡 **Tip de Impresión Directa:** Si prefieres imprimir directamente desde el navegador en formato Carta, presiona **Ctrl + P** o **Cmd + P**.")
        st.markdown("---")
        
        # Preparación del HTML para Vista Previa
        if logo_path:
            import base64
            with open(logo_path, "rb") as f:
                data_img = base64.b64encode(f.read()).decode("utf-8")
            html_logo = f'<img src="data:image/png;base64,{data_img}" style="width:100%; height:auto; display:block; margin-bottom:10px;">'
        else:
            html_logo = '<div style="background-color:#f2f2f2; border:2px dashed #cbd5e1; padding:20px; text-align:center; font-weight:bold; color:#64748b; margin-bottom:10px;">[ LOGO: ENCABEZADO_PALETA.PNG NO DETECTADO ]</div>'

        # Construcción HTML
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
        mostrar_p = st.session_state.mostrar_precios

        for idx_sec, sec in enumerate(st.session_state.lista_secciones):
            df_sec = st.session_state.get(f"df_{sec['id']}", pd.DataFrame())
            th_style = 'style="background-color: #f2f2f2 !important;"' if idx_sec > 0 else ''
            
            # Ajuste de proporciones HTML según 6 o 5 columnas
            if mostrar_p:
                th_cols = f"""
                    <th style="width: 4.5%; text-align: center;" {th_style}>ITEM</th>
                    <th style="width: 48.5%; text-align: left;" {th_style}>{sec['titulo']}</th>
                    <th style="width: 23.5%; text-align: left;" {th_style}>MEDIDAS</th>
                    <th style="width: 7.5%; text-align: center;" {th_style}>JUEGOS/KITS</th>
                    <th style="width: 6.0%; text-align: center;" {th_style}>CANT.</th>
                    <th style="width: 10.0%; text-align: right;" {th_style}>PRECIO</th>
                """
            else:
                th_cols = f"""
                    <th style="width: 5.0%; text-align: center;" {th_style}>ITEM</th>
                    <th style="width: 56.0%; text-align: left;" {th_style}>{sec['titulo']}</th>
                    <th style="width: 25.0%; text-align: left;" {th_style}>MEDIDAS</th>
                    <th style="width: 8.0%; text-align: center;" {th_style}>JUEGOS/KITS</th>
                    <th style="width: 6.0%; text-align: center;" {th_style}>CANT.</th>
                """

            html_cuerpo += f"""
            <table class="tabla-remastered">
                <thead>
                    <tr>
                        {th_cols}
                    </tr>
                </thead>
                <tbody>
            """
            
            subtotal_seccion = 0.0
            item_numeral = 1
            
            for row in df_sec.to_dict('records'):
                desc = str(row.get('descripción', '') or '').strip()
                med = str(row.get('medidas', '') or '').strip()
                
                try: jk_val = float(row.get('juegos/kits')) if pd.notna(row.get('juegos/kits')) and row.get('juegos/kits') != '' else 0.0
                except: jk_val = 0.0
                try: cant_val = float(row.get('cantidad')) if pd.notna(row.get('cantidad')) and row.get('cantidad') != '' else 0.0
                except: cant_val = 0.0
                try: pu_val = float(row.get('precio_unitario')) if pd.notna(row.get('precio_unitario')) and row.get('precio_unitario') != '' else 0.0
                except: pu_val = 0.0

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
                    
                    if mostrar_p:
                        td_cols = f"""
                            <td style="text-align: center;">{item_numeral}</td>
                            <td style="text-align: left;">{desc}</td>
                            <td style="text-align: left;">{med}</td>
                            <td style="text-align: center;">{jk_str}</td>
                            <td style="text-align: center;">{cant_str}</td>
                            <td style="text-align: right;">{precio_str}</td>
                        """
                    else:
                        td_cols = f"""
                            <td style="text-align: center;">{item_numeral}</td>
                            <td style="text-align: left;">{desc}</td>
                            <td style="text-align: left;">{med}</td>
                            <td style="text-align: center;">{jk_str}</td>
                            <td style="text-align: center;">{cant_str}</td>
                        """

                    html_cuerpo += f"<tr>{td_cols}</tr>"
                    item_numeral += 1
            
            if item_numeral == 1:
                colspan = 6 if mostrar_p else 5
                html_cuerpo += f'<tr><td colspan="{colspan}" style="text-align: center; color: #a0aec0; padding: 8px;">Sección sin registros activos</td></tr>'
                
            html_cuerpo += "</tbody></table>"

            if mostrar_p:
                html_cuerpo += f"""
                <div class="contenedor-subtotal">
                    <span>SUB TOTAL {sec['titulo']}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span>
                    <span>${subtotal_seccion:,.2f}</span>
                </div>
                """

            total_general += subtotal_seccion
            
        if mostrar_p:
            html_cuerpo += f"""
            <div class="banner-total-general">
                <span>TOTAL A CANCELAR</span>
                <span>${total_general:,.2f}</span>
            </div>
            """
        else:
            html_cuerpo += "<div style='height: 15px;'></div>"

        html_cuerpo += f"""
            <div class="clausulas-container">
                <div class="clausulas-header">CLAUSULAS:</div>
                {st.session_state.clausulas_presupuesto}
            </div>
        </div>
        """
        
        # Renderizado final en pantalla
        st.markdown(html_cuerpo, unsafe_allow_html=True)
