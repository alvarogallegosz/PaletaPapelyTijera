# print_pdf_utility.py
import html
import io
import os
import pandas as pd
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    Image,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

class NumberedCanvas(canvas.Canvas):
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
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor('#64748b'))
        
        texto_pagina = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(612 - 36, 20, texto_pagina)
        self.drawString(36, 20, "Paletapapelytijera • Presupuesto Detallado")
        
        self.setStrokeColor(colors.HexColor('#e2e8f0'))
        self.setLineWidth(0.5)
        self.line(36, 30, 612 - 36, 30)
        self.restoreState()


def _escapar_texto(texto: str) -> str:
    """Sanea caracteres especiales XML (&, <, >) para evitar fallos de parseo en ReportLab."""
    if not texto:
        return ""
    return html.escape(str(texto).strip())


def generar_pdf_presupuesto_nativo(modo_interno=False):
    """
    Genera el PDF del presupuesto.
    
    :param modo_interno: 
        - False (Cliente): Oculta el desglose de precio unitario por partida, pero conserva los Subtotales y Total General.
        - True (Control Interno): Incluye la columna de precio unitario por partida para análisis de Gerencia/Administración.
    """
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=45
    )
    
    styles = getSampleStyleSheet()
    
    style_normal = ParagraphStyle(
        'DocNormal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#000000')
    )
    
    style_header_center = ParagraphStyle(
        'DocHeaderCenter',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.HexColor('#000000'),
        alignment=1
    )
    
    style_header_left = ParagraphStyle(
        'DocHeaderLeft',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.HexColor('#000000')
    )

    story = []
    
    # --- ENCABEZADO Y LOGO ---
    logo_nombre = "encabezado_paleta.png"
    ruta_script = os.path.join(os.path.dirname(__file__), logo_nombre)
    ruta_raiz = os.path.join(os.getcwd(), logo_nombre)
    ruta_final = ruta_script if os.path.exists(ruta_script) else (ruta_raiz if os.path.exists(ruta_raiz) else None)
    
    if ruta_final:
        ancho_pdf = 432
        altura_pdf = 76  
        story.append(Image(ruta_final, width=ancho_pdf, height=altura_pdf, hAlign='CENTER'))
        story.append(Spacer(1, 10))        

    # --- BLOQUE METADATA ---
    meta = st.session_state.get("meta_presupuesto", {})
    p_nombre = _escapar_texto(meta.get('nombre', '')).upper() or 'PRESUPUESTO'
    p_fecha_evt = _escapar_texto(meta.get('fecha_evento', '')).upper() or 'N/A'
    p_cliente = _escapar_texto(meta.get('cliente', '')).upper() or 'N/A'
    p_lugar = _escapar_texto(meta.get('lugar', '')).upper() or 'N/A'
    p_emision = _escapar_texto(meta.get('fecha_larga', '')).upper() or 'N/A'
    
    meta_izq = f"<b>{p_nombre}</b><br/>FECHA DEL EVENTO: {p_fecha_evt}<br/>CLIENTE: {p_cliente} | LUGAR: {p_lugar}"
    meta_der = f"<b>EMISIÓN: {p_emision}</b>"
    
    meta_tabla = Table(
        [[Paragraph(meta_izq, style_normal), Paragraph(meta_der, ParagraphStyle('R', parent=style_normal, alignment=2))]], 
        colWidths=[380, 160]
    )
    meta_tabla.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(meta_tabla)
    story.append(Spacer(1, 8))
    
    # --- BANNER SUBTÍTULO ---
    titulo_banner = "DESGLOSE DE COSTOS (CONTROL INTERNO)" if modo_interno else "PRESUPUESTO DETALLADO"
    style_banner = ParagraphStyle('BStyle', fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#FFFFFF'), alignment=1)
    banner_tabla = Table([[Paragraph(titulo_banner, style_banner)]], colWidths=[540])
    banner_tabla.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#b8d7a3')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(banner_tabla)
    story.append(Spacer(1, 10))
    
    # --- TABLAS DINÁMICAS SECCIONADAS ---
    secciones_activas = st.session_state.get("lista_secciones", [])
    total_general = 0.0
    
    if modo_interno:
        anchos_columnas = [35, 225, 120, 65, 40, 55]  # 6 columnas (Control Interno)
    else:
        anchos_columnas = [35, 260, 140, 65, 40]      # 5 columnas (Cliente)
    
    for idx_sec, sec in enumerate(secciones_activas):
        sec_id = sec.get('id', '')
        sec_titulo = _escapar_texto(sec.get('titulo', f'SECCIÓN {idx_sec+1}')).upper()
        df_sec = st.session_state.get(f"df_{sec_id}", pd.DataFrame())
        
        if modo_interno:
            tabla_datos = [[
                Paragraph("<b>ITEM</b>", style_header_center),
                Paragraph(f"<b>{sec_titulo}</b>", style_header_left),
                Paragraph("<b>MEDIDAS</b>", style_header_left),
                Paragraph("<b>JUEGOS<br/>/KITS</b>", style_header_center),
                Paragraph("<b>CANT.</b>", style_header_center),
                Paragraph("<b>PRECIO</b>", style_header_center)
            ]]
        else:
            tabla_datos = [[
                Paragraph("<b>ITEM</b>", style_header_center),
                Paragraph(f"<b>{sec_titulo}</b>", style_header_left),
                Paragraph("<b>MEDIDAS</b>", style_header_left),
                Paragraph("<b>JUEGOS<br/>/KITS</b>", style_header_center),
                Paragraph("<b>CANT.</b>", style_header_center)
            ]]
        
        subtotal_seccion = 0.0
        item_numeral = 1
        
        if not df_sec.empty:
            for row in df_sec.to_dict('records'):
                desc_raw = str(row.get('descripción', '') or '').strip()
                med_raw = str(row.get('medidas', '') or '').strip()
                
                desc = _escapar_texto(desc_raw).replace("\n", "<br/>")
                med = _escapar_texto(med_raw).replace("\n", "<br/>")
                
                try:
                    jk_val = float(row.get('juegos/kits')) if pd.notna(row.get('juegos/kits')) and row.get('juegos/kits') != '' else 0.0
                except Exception:
                    jk_val = 0.0
                    
                try:
                    cant_val = float(row.get('cantidad')) if pd.notna(row.get('cantidad')) and row.get('cantidad') != '' else 0.0
                except Exception:
                    cant_val = 0.0
                    
                try:
                    pu_val = float(row.get('precio_unitario')) if pd.notna(row.get('precio_unitario')) and row.get('precio_unitario') != '' else 0.0
                except Exception:
                    pu_val = 0.0

                if desc or med or jk_val or cant_val or pu_val:
                    factor = ((jk_val if jk_val > 0 else 1.0) * (cant_val if cant_val > 0 else 1.0)) if (jk_val > 0 or cant_val > 0) else 0.0
                    total_fila = factor * pu_val
                    subtotal_seccion += total_fila
                    
                    jk_str = f"{int(jk_val) if jk_val.is_integer() else jk_val}" if jk_val > 0 else ""
                    cant_str = f"{int(cant_val) if cant_val.is_integer() else cant_val}" if cant_val > 0 else ""
                    
                    if modo_interno:
                        precio_str = f"${total_fila:,.2f}"
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
        
        if item_numeral == 1:
            colspan_val = 6 if modo_interno else 5
            tabla_datos.append([Paragraph("Sección sin registros activos", style_header_center)] + [""] * (colspan_val - 1))
            
        t = Table(tabla_datos, colWidths=anchos_columnas, repeatRows=1)
        t_style = [
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#fffdeb')),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('LINEBELOW', (0,0), (-1,0), 1, colors.HexColor('#cbd5e1')),
        ]
        if item_numeral == 1:
            span_limit = 5 if modo_interno else 4
            t_style.append(('SPAN', (0,1), (span_limit, 1)))
            
        t.setStyle(TableStyle(t_style))
        story.append(t)
        
        # Subtotal de la sección
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
        
    # --- TOTAL GENERAL ---
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
    
    # --- CLÁUSULAS ---
    clausulas_txt = st.session_state.get("clausulas_presupuesto", "")
    if clausulas_txt and str(clausulas_txt).strip():
        clausulas_html = _escapar_texto(clausulas_txt).replace("\n", "<br/>")
        
        bloque_clausulas = [
            Paragraph("CLAUSULAS:", ParagraphStyle('CT', fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#d53f8c'))),
            Spacer(1, 4),
            Paragraph(clausulas_html, ParagraphStyle('CB', fontName='Helvetica', fontSize=8.5, textColor=colors.HexColor('#1a202c'), leading=12))
        ]
        story.append(KeepTogether(bloque_clausulas))
    
    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer.getvalue()