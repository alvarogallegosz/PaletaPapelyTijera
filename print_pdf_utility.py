import io
import os
import pandas as pd
import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generar_pdf_presupuesto_nativo():
    buffer = io.BytesIO()
    
    # Configuración de página Carta física (612 x 792 puntos) con márgenes de 0.5 pulgadas (36 pt)
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    # --- 🎨 ESTILOS TIPOGRÁFICOS ---
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
        alignment=1 # Centrado
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
    
    # --- 🖼️ CARGA E INCRUSTACIÓN DEL LOGO ---
    logo_nombre = "encabezado_paleta.png"
    ruta_script = os.path.join(os.path.dirname(__file__), logo_nombre)
    ruta_raiz = os.path.join(os.getcwd(), logo_nombre)
    ruta_final = ruta_script if os.path.exists(ruta_script) else (ruta_raiz if os.path.exists(ruta_raiz) else None)
    
    if ruta_final:
        # Forzar el ancho al área imprimible total (540 puntos)
        story.append(Image(ruta_final, width=540, height=95))
        story.append(Spacer(1, 10))
        
    # --- 📄 BLOQUE METADATA ---
    meta = st.session_state.get("meta_presupuesto", {})
    p_nombre = str(meta.get('nombre', '') or '').upper() or 'PRESUPUESTO'
    p_fecha_evt = str(meta.get('fecha_evento', '') or '').upper() or 'N/A'
    p_cliente = str(meta.get('cliente', '') or '').upper() or 'N/A'
    p_lugar = str(meta.get('lugar', '') or '').upper() or 'N/A'
    p_emision = str(meta.get('fecha_larga', '') or '').upper() or 'N/A'
    
    meta_izq = f"<b>{p_nombre}</b><br/>FECHA DEL EVENTO: {p_fecha_evt}<br/>CLIENTE: {p_cliente} | LUGAR: {p_lugar}"
    meta_der = f"<br/><br/>EMISIÓN: {p_emision}"
    
    meta_tabla = Table(
        [[Paragraph(meta_izq, style_normal), Paragraph(meta_der, ParagraphStyle('R', parent=style_normal, alignment=2))]], 
        colWidths=[390, 150]
    )
    meta_tabla.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(meta_tabla)
    story.append(Spacer(1, 8))
    
    # --- 🟢 BANNER SUBTÍTULO ---
    style_banner = ParagraphStyle('BStyle', fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#FFFFFF'), alignment=1)
    banner_tabla = Table([[Paragraph("PRESUPUESTO DETALLADO", style_banner)]], colWidths=[540])
    banner_tabla.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#b8d7a3')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(banner_tabla)
    story.append(Spacer(1, 10))
    
    # --- 📊 CONSTRUCCIÓN DE TABLAS ---
    secciones_activas = st.session_state.get("lista_secciones", [])
    total_general = 0.0
    
    # Distribución fija milimétrica de anchos (Suma exactamente 540 puntos del área imprimible)
    anchos_columnas = [25, 245, 140, 45, 35, 50] 
    
    for idx_sec, sec in enumerate(secciones_activas):
        sec_id = sec.get('id', '')
        sec_titulo = sec.get('titulo', f'SECCIÓN {idx_sec+1}').upper()
        df_sec = st.session_state.get(f"df_{sec_id}", pd.DataFrame())
        
        # Estructura de cabecera de la sección
        tabla_datos = [[
            Paragraph("<b>ITEM</b>", style_header_center),
            Paragraph(f"<b>{sec_titulo}</b>", style_header_left),
            Paragraph("<b>MEDIDAS</b>", style_header_left),
            Paragraph("<b>JUEGOS<br/>/KITS</b>", style_header_center),
            Paragraph("<b>CANT.</b>", style_header_center),
            Paragraph("<b>PRECIO</b>", style_header_center)
        ]]
        
        subtotal_seccion = 0.0
        item_numeral = 1
        
        if not df_sec.empty:
            for row in df_sec.to_dict('records'):
                desc = str(row.get('descripción', '') or '').strip().replace("\n", "<br/>")
                med = str(row.get('medidas', '') or '').strip().replace("\n", "<br/>")
                
                try: jk_val = float(row.get('juegos/kits')) if pd.notna(row.get('juegos/kits')) and row.get('juegos/kits') != '' else 0.0
                except: jk_val = 0.0
                try: cant_val = float(row.get('cantidad')) if pd.notna(row.get('cantidad')) and row.get('cantidad') != '' else 0.0
                except: cant_val = 0.0
                try: pu_val = float(row.get('precio_unitario')) if pd.notna(row.get('precio_unitario')) and row.get('precio_unitario') != '' else 0.0
                except: pu_val = 0.0

                if desc or med or jk_val or cant_val or pu_val:
                    total_fila = (jk_val * cant_val * pu_val) if jk_val > 0 else (cant_val * pu_val)
                    subtotal_seccion += total_fila
                    
                    # 🌟 CAMBIO SOLICITADO: Filas sin $, solo el valor numérico formateado
                    precio_str = f"{total_fila:,.2f}"
                    jk_str = f"{int(jk_val) if jk_val.is_integer() else jk_val}" if jk_val > 0 else ""
                    cant_str = f"{int(cant_val) if cant_val.is_integer() else cant_val}" if cant_val > 0 else ""
                    
                    tabla_datos.append([
                        Paragraph(str(item_numeral), style_header_center),
                        Paragraph(desc, style_normal),
                        Paragraph(med, style_normal),
                        Paragraph(jk_str, style_header_center),
                        Paragraph(cant_str, style_header_center),
                        Paragraph(precio_str, ParagraphStyle('P', parent=style_normal, alignment=2))
                    ])
                    item_numeral += 1
        
        if item_numeral == 1:
            tabla_datos.append([Paragraph("Sección sin registros activos", style_header_center), "", "", "", "", ""])
            
        # Instanciar tabla con anchos físicos estrictos
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
            t_style.append(('SPAN', (0,1), (5,1)))
            
        t.setStyle(TableStyle(t_style))
        story.append(t)
        
        # Subtotal de la sección (Lleva $)
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
    story.append(total_table)
    story.append(Spacer(1, 14))
    
    # --- 📝 CLÁUSULAS ---
    clausulas_txt = st.session_state.get("clausulas_presupuesto", "")
    clausulas_html = str(clausulas_txt or '').replace("\n", "<br/>")
    
    story.append(Paragraph("CLAUSULAS:", ParagraphStyle('CT', fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#d53f8c'))))
    story.append(Spacer(1, 4))
    story.append(Paragraph(clausulas_html, ParagraphStyle('CB', fontName='Helvetica', fontSize=8.5, textColor=colors.HexColor('#1a202c'), leading=12)))
    
    # Compilar PDF en memoria
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()