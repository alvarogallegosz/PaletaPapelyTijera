import io
import os
import pandas as pd
import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas

# ==============================================================================
# 🎨 LIENZO MULTIPÁGINA: Dibuja Encabezado Permanente y Contador "Página X de Y"
# ==============================================================================
def crear_numbered_canvas(meta, ruta_logo):
    class CustomNumberedCanvas(canvas.Canvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._saved_page_states = []

        def showPage(self):
            self._saved_page_states.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            num_pages = len(self._saved_page_states)
            for state in self._saved_page_states:
                self.__dict__.update(state)
                self.draw_decorations(num_pages)
                super().showPage()
            super().save()

        def draw_decorations(self, page_count):
            self.saveState()
            
            # --- 🖼️ 1. LOGO CENTRADO (80%) ---
            if ruta_logo and os.path.exists(ruta_logo):
                self.drawImage(ruta_logo, 90, 715, width=432, height=62, preserveAspectRatio=True, mask='auto')
            
            # --- 📄 2. METADATA DE CABECERA ---
            p_nombre = str(meta.get('nombre', '') or '').upper() or 'PRESUPUESTO'
            p_fecha_evt = str(meta.get('fecha_evento', '') or '').upper() or 'N/A'
            p_cliente = str(meta.get('cliente', '') or '').upper() or 'N/A'
            p_lugar = str(meta.get('lugar', '') or '').upper() or 'N/A'
            p_emision = str(meta.get('fecha_larga', '') or '').upper() or 'N/A'

            self.setFont("Helvetica-Bold", 8.5)
            self.setFillColor(colors.HexColor("#000000"))
            self.drawString(36, 700, p_nombre)
            
            self.setFont("Helvetica", 8)
            self.drawString(36, 689, f"FECHA DEL EVENTO: {p_fecha_evt}")
            self.drawString(36, 678, f"CLIENTE: {p_cliente} | LUGAR: {p_lugar}")
            
            self.setFont("Helvetica-Bold", 8)
            self.drawRightString(576, 678, f"EMISIÓN: {p_emision}")

            # --- 🟢 3. BANNER VERDE PRINCIPAL ---
            self.setFillColor(colors.HexColor("#b8d7a3"))
            self.rect(36, 652, 540, 18, fill=1, stroke=0)
            self.setFillColor(colors.HexColor("#ffffff"))
            self.setFont("Helvetica-Bold", 9.5)
            self.drawCentredString(306, 657, "PRESUPUESTO DETALLADO")

            # --- 🔢 4. PIE DE PÁGINA (PÁGINA X DE Y) ---
            self.setFont("Helvetica", 8.5)
            self.setFillColor(colors.HexColor("#475569"))
            self.drawRightString(576, 18, f"Página {self._pageNumber} de {page_count}")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(36, 30, 576, 30)
            
            self.restoreState()

    return CustomNumberedCanvas


# ==============================================================================
# 📑 FUNCIÓN PRINCIPAL DE GENERACIÓN DE PDF
# ==============================================================================
def generar_pdf_presupuesto(incluir_precios=False):
    buffer = io.BytesIO()
    
    # topMargin=150 reserva el espacio exacto para la cabecera fija
    # bottomMargin=45 reserva el espacio para el pie de página
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=150,
        bottomMargin=45
    )
    
    styles = getSampleStyleSheet()
    
    # Estilos Tipográficos
    style_normal = ParagraphStyle(
        'DocNormal', parent=styles['Normal'],
        fontName='Helvetica', fontSize=9, leading=12, textColor=colors.HexColor('#000000')
    )
    style_header_center = ParagraphStyle(
        'DocHeaderCenter', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=9, leading=11, textColor=colors.HexColor('#000000'), alignment=1
    )
    style_header_left = ParagraphStyle(
        'DocHeaderLeft', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=9, leading=11, textColor=colors.HexColor('#000000')
    )

    # Identificación del Logo y Metadatos
    logo_nombre = "encabezado_paleta.png"
    ruta_script = os.path.join(os.path.dirname(__file__), logo_nombre)
    ruta_raiz = os.path.join(os.getcwd(), logo_nombre)
    ruta_final = ruta_script if os.path.exists(ruta_script) else (ruta_raiz if os.path.exists(ruta_raiz) else None)
    meta = st.session_state.get("meta_presupuesto", {})

    story = []
    
    # Anchos según modalidad de precios
    if incluir_precios:
        anchos_columnas = [35, 225, 120, 65, 40, 55]  # 6 columnas
    else:
        anchos_columnas = [35, 260, 140, 65, 40]      # 5 columnas

    secciones_activas = st.session_state.get("lista_secciones", [])
    total_general = 0.0
    pagina_estimada = 1

    # --- 📊 PROCESAMIENTO DE SECCIONES CON TOPES DE LÍNEAS ---
    for idx_sec, sec in enumerate(secciones_activas):
        sec_id = sec.get('id', '')
        sec_titulo = sec.get('titulo', f'SECCIÓN {idx_sec+1}').upper()
        df_sec = st.session_state.get(f"df_{sec_id}", pd.DataFrame())
        
        # Regla del Usuario: Sección 1 = Máx 24 líneas; Secciones 2+ = Máx 15 líneas
        limite_primero = 24 if idx_sec == 0 else 15
        limite_siguientes = 15

        # Filtrar registros válidos de la sección
        filas_validas = []
        if not df_sec.empty:
            for row in df_sec.to_dict('records'):
                desc = str(row.get('descripción', '') or '').strip().replace("\n", " ").replace("\r", "").replace("  ", " ")
                med = str(row.get('medidas', '') or '').strip().replace("\n", " ").replace("\r", "").replace("  ", " ")
                try: jk_val = float(row.get('juegos/kits')) if pd.notna(row.get('juegos/kits')) and row.get('juegos/kits') != '' else 0.0
                except: jk_val = 0.0
                try: cant_val = float(row.get('cantidad')) if pd.notna(row.get('cantidad')) and row.get('cantidad') != '' else 0.0
                except: cant_val = 0.0
                try: pu_val = float(row.get('precio_unitario')) if pd.notna(row.get('precio_unitario')) and row.get('precio_unitario') != '' else 0.0
                except: pu_val = 0.0

                if desc or med or jk_val or cant_val or pu_val:
                    total_fila = (jk_val * cant_val * pu_val) if jk_val > 0 else (cant_val * pu_val)
                    filas_validas.append((desc, med, jk_val, cant_val, pu_val, total_fila))

        # Fragmentar filas de la sección en bloques que respeten los límites de líneas
        bloques = []
        if filas_validas:
            inicio = 0
            tamano_actual = limite_primero
            while inicio < len(filas_validas):
                bloques.append(filas_validas[inicio:inicio + tamano_actual])
                inicio += tamano_actual
                tamano_actual = limite_siguientes
        else:
            bloques = [[]]  # Bloque vacío para mostrar mensaje de sección vacía

        subtotal_seccion = 0.0
        item_numeral = 1

        for idx_bloque, bloque in enumerate(bloques):
            # Manejo de saltos de página y títulos de continuación
            if idx_bloque > 0:
                story.append(PageBreak())
                pag_anterior = pagina_estimada
                pagina_estimada += 1
                titulo_tabla = f"<b>{sec_titulo} <font color='#64748b' size=7.5>(VIENE DE LA PÁGINA {pag_anterior})</font></b>"
            else:
                if idx_sec > 0:
                    story.append(PageBreak())
                    pagina_estimada += 1
                titulo_tabla = f"<b>{sec_titulo}</b>"

            # Construcción de encabezados de la tabla
            if incluir_precios:
                tabla_datos = [[
                    Paragraph("<b>ITEM</b>", style_header_center),
                    Paragraph(titulo_tabla, style_header_left),
                    Paragraph("<b>MEDIDAS</b>", style_header_left),
                    Paragraph("<b>JUEGOS<br/>/KITS</b>", style_header_center),
                    Paragraph("<b>CANT.</b>", style_header_center),
                    Paragraph("<b>PRECIO</b>", style_header_center)
                ]]
            else:
                tabla_datos = [[
                    Paragraph("<b>ITEM</b>", style_header_center),
                    Paragraph(titulo_tabla, style_header_left),
                    Paragraph("<b>MEDIDAS</b>", style_header_left),
                    Paragraph("<b>JUEGOS<br/>/KITS</b>", style_header_center),
                    Paragraph("<b>CANT.</b>", style_header_center)
                ]]

            # Rellenar filas del bloque
            if bloque:
                for desc, med, jk_val, cant_val, pu_val, total_fila in bloque:
                    subtotal_seccion += total_fila
                    jk_str = f"{int(jk_val) if jk_val.is_integer() else jk_val}" if jk_val > 0 else ""
                    cant_str = f"{int(cant_val) if cant_val.is_integer() else cant_val}" if cant_val > 0 else ""
                    
                    if incluir_precios:
                        precio_str = f"{total_fila:,.2f}"
                        tabla_datos.append([
                            Paragraph(str(item_numeral), style_header_center),
                            Paragraph(desc, style_normal),
                            Paragraph(med, style_normal),
                            Paragraph(jk_str, style_header_center),
                            Paragraph(cant_str, style_header_center),
                            Paragraph(precio_str, ParagraphStyle('P', parent=style_normal, alignment=2))
                        ])
                    else:
                        tabla_datos.append([
                            Paragraph(str(item_numeral), style_header_center),
                            Paragraph(desc, style_normal),
                            Paragraph(med, style_normal),
                            Paragraph(jk_str, style_header_center),
                            Paragraph(cant_str, style_header_center)
                        ])
                    item_numeral += 1
            else:
                colspan_val = 6 if incluir_precios else 5
                tabla_datos.append([Paragraph("Sección sin registros activos", style_header_center)] + [""] * (colspan_val - 1))

            # Renders de la tabla
            t = Table(tabla_datos, colWidths=anchos_columnas, repeatRows=1)
            t_style = [
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#fffdeb')),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
                ('LINEBELOW', (0,0), (-1,0), 1, colors.HexColor('#cbd5e1')),
            ]
            if not bloque:
                span_limit = 5 if incluir_precios else 4
                t_style.append(('SPAN', (0,1), (span_limit, 1)))
                
            t.setStyle(TableStyle(t_style))
            story.append(t)

            # Si es el último bloque de la sección, renderizar el Subtotal de la Sección
            if idx_bloque == len(bloques) - 1:
                txt_subtotal = f"<b>SUB TOTAL {sec_titulo}:&nbsp;&nbsp;&nbsp;&nbsp;${subtotal_seccion:,.2f}</b>"
                sub_p = Paragraph(txt_subtotal, ParagraphStyle('Sub', parent=style_normal, alignment=2, fontSize=9.5))
                sub_tabla = Table([[sub_p]], colWidths=[540])
                sub_tabla.setStyle(TableStyle([
                    ('TOPPADDING', (0,0), (-1,-1), 5),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                    ('LINEBELOW', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
                ]))
                story.append(sub_tabla)
                story.append(Spacer(1, 10))

        total_general += subtotal_seccion

    # --- 🟢 BANNER DE TOTAL GENERAL ---
    tot_izq = Paragraph("TOTAL A CANCELAR", ParagraphStyle('TL', fontName='Helvetica-Bold', fontSize=13))
    tot_der = Paragraph(f"${total_general:,.2f}", ParagraphStyle('TR', fontName='Helvetica-Bold', fontSize=13, alignment=2))
    
    total_tabla = Table([[tot_izq, tot_der]], colWidths=[270, 270])
    total_tabla.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#b8d7a3')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(Spacer(1, 5))
    story.append(total_tabla)
    story.append(Spacer(1, 14))

    # --- 📝 CLÁUSULAS ---
    clausulas_txt = st.session_state.get("clausulas_presupuesto", "")
    clausulas_html = str(clausulas_txt or '').replace("\n", "<br/>")
    
    story.append(Paragraph("CLAUSULAS:", ParagraphStyle('CT', fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#d53f8c'))))
    story.append(Spacer(1, 4))
    story.append(Paragraph(clausulas_html, ParagraphStyle('CB', fontName='Helvetica', fontSize=8.5, textColor=colors.HexColor('#1a202c'), leading=12)))

    # Compilación final del documento asociando el lienzo dinámico
    canvas_maker = crear_numbered_canvas(meta, ruta_final)
    doc.build(story, canvasmaker=canvas_maker)
    
    buffer.seek(0)
    return buffer.getvalue()
