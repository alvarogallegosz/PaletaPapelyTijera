import os
import pandas as pd
import streamlit as st
from print_pdf_utility import generar_pdf_presupuesto_nativo

def render_creacion_presupuestos(rol_simulado):
    # Inicialización del modo de vista si no existe
    if "modo_vista" not in st.session_state:
        st.session_state.modo_vista = "edicion"

    # ===================================================
    # ✏️ MODO EDICIÓN
    # ===================================================
    if st.session_state.modo_vista == "edicion":
        st.title("📝 Creación de Presupuesto")
        st.write("Diligencie los campos y agregue los ítems requeridos para generar la propuesta.")

        # ... (Tu código existente del formulario de edición, dataframes por sección, etc.) ...
        
        st.markdown("---")
        if st.button("👁️ Generar Vista Previa del Documento", type="primary", use_container_width=True):
            st.session_state.modo_vista = "vista_previa"
            st.rerun()

    # ===================================================
    # 🖨️ MODO VISTA PREVIA Y DESCARGA
    # ===================================================
    else:
        meta = st.session_state.get("meta_presupuesto", {})
        clausulas_txt = st.session_state.get("clausulas_presupuesto", "")
        secciones_activas = st.session_state.get("lista_secciones", [])
        
        st.markdown("### 👁️ Vista Previa del Documento")
        
        # 🎛️ SELECTOR DINÁMICO DE PRECIOS
        incluir_precios_pdf = st.toggle(
            "📊 Incluir columna de Precios Unitarios en el PDF y Pantalla", 
            value=False,
            help="Activa para mostrar el precio individual de cada ítem, o desactiva para mostrar solo los subtotales de sección."
        )
        
        # Generación nativa del binario PDF pasando el estado del selector
        pdf_bytes = generar_pdf_presupuesto_nativo(incluir_precios=incluir_precios_pdf)
        nombre_cliente = str(meta.get("cliente", "cliente")).strip().replace(" ", "_").lower()
        
        # Fila de Botones de Acción
        col_pv1, col_pv2, col_pv3 = st.columns(3)
        with col_pv1:
            if st.button("✏️ Regresar a Edición", type="secondary", use_container_width=True):
                st.session_state.modo_vista = "edicion"
                st.rerun()
                
        with col_pv2:
            st.download_button(
                label="📥 Descargar Presupuesto PDF",
                data=pdf_bytes,
                file_name=f"presupuesto_{nombre_cliente}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            
        with col_pv3:
            if st.button("💾 Guardar en Base de Datos", type="primary", use_container_width=True):
                st.success("¡Presupuesto guardado exitosamente en la base de datos!")
        
        st.markdown("---")

        # CSS para la simulación perfecta en pantalla
        st.markdown("""
            <style>
                .documento-hoja {
                    font-family: 'Arial', sans-serif;
                    color: #000000;
                    background-color: #ffffff;
                    width: 100%;
                    max-width: 8.5in;
                    min-height: 11in;
                    box-sizing: border-box;
                    padding: 0.5in;
                    margin: 10px auto;
                    border: 1px solid #cbd5e1;
                    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
                }

                .meta-contenedor {
                    display: flex;
                    justify-content: space-between;
                    font-size: 12px;
                    line-height: 1.4;
                    margin-top: 10px;
                    margin-bottom: 5px;
                }
                .meta-izquierda { flex: 1; font-weight: normal; }
                .meta-derecha { 
                    text-align: right; 
                    font-weight: bold; 
                    white-space: nowrap; 
                    margin-left: 20px;
                }

                .banner-verde-principal {
                    background-color: #b8d7a3 !important;
                    color: #ffffff !important;
                    text-align: center;
                    font-weight: bold;
                    padding: 6px 0px;
                    font-size: 13px;
                    letter-spacing: 0.5px;
                    text-transform: uppercase;
                    margin-bottom: 12px;
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
                    font-size: 11px;
                    padding: 6px 8px;
                }
                .tabla-remastered td {
                    padding: 6px 8px;
                    font-size: 11px;
                    border-bottom: 1px solid #e2e8f0;
                    vertical-align: top;
                    word-wrap: break-word;
                }

                .contenedor-subtotal {
                    background-color: #ffffff;
                    font-weight: bold;
                    font-size: 12px;
                    text-align: right;
                    padding: 6px 8px;
                    margin-bottom: 15px;
                    border-bottom: 1px solid #cbd5e1;
                }

                .banner-total-general {
                    background-color: #b8d7a3 !important;
                    color: #000000 !important;
                    font-weight: bold;
                    font-size: 20px;
                    padding: 8px 15px;
                    margin-top: 15px;
                    margin-bottom: 20px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }

                .clausulas-container {
                    font-size: 11px;
                    margin-top: 20px;
                    color: #1a202c;
                    line-height: 1.4;
                }
                .clausulas-header {
                    color: #d53f8c;
                    font-weight: bold;
                    font-size: 12px;
                    margin-bottom: 5px;
                }
            </style>
        """, unsafe_allow_html=True)

        # Carga del Logo al 80% centrado
        ancho_logo_deseado = "80%"
        logo_nombre = "encabezado_paleta.png"
        ruta_script = os.path.join(os.path.dirname(__file__), logo_nombre)
        ruta_raiz = os.path.join(os.getcwd(), logo_nombre)
        ruta_final = ruta_script if os.path.exists(ruta_script) else (ruta_raiz if os.path.exists(ruta_raiz) else None)
        
        if ruta_final:
            import base64
            with open(ruta_final, "rb") as f:
                data_img = base64.b64encode(f.read()).decode("utf-8")
            html_logo = f'<img src="data:image/png;base64,{data_img}" style="width:{ancho_logo_deseado}; height:auto; display:block; margin:0 auto 15px auto;">'
        else:
            html_logo = f'<div style="background-color:#f2f2f2; border:2px dashed #cbd5e1; padding:20px; text-align:center; font-weight:bold; color:#64748b; margin:0 auto 15px auto; width:{ancho_logo_deseado};">[ LOGO: {logo_nombre} NO DETECTADO ]</div>'

        # Textos sanitizados
        p_nombre = str(meta.get('nombre', '') or '').upper() or 'PRESUPUESTO'
        p_fecha_evt = str(meta.get('fecha_evento', '') or '').upper() or 'N/A'
        p_cliente = str(meta.get('cliente', '') or '').upper() or 'N/A'
        p_lugar = str(meta.get('lugar', '') or '').upper() or 'N/A'
        p_emision = str(meta.get('fecha_larga', '') or '').upper() or 'N/A'
        clausulas_html = str(clausulas_txt or '').replace("\n", "<br>")

        # Construcción HTML
        html_cuerpo = f"""
        <div class="documento-hoja">
            {html_logo}
            <div class="meta-contenedor">
                <div class="meta-izquierda">
                    <b>{p_nombre}</b><br>
                    FECHA DEL EVENTO: {p_fecha_evt}<br>
                    CLIENTE: {p_cliente} | LUGAR: {p_lugar}
                </div>
                <div class="meta-derecha">
                    EMISIÓN: {p_emision}
                </div>
            </div>
            <div class="banner-verde-principal">PRESUPUESTO DETALLADO</div>
        """
        
        total_general = 0.0
        
        for idx_sec, sec in enumerate(secciones_activas):
            sec_id = sec.get('id', '')
            sec_titulo = sec.get('titulo', f'SECCIÓN {idx_sec+1}').upper()
            df_sec = st.session_state.get(f"df_{sec_id}", pd.DataFrame())
            
            # Formato de columnas dinámico en pantalla
            if incluir_precios_pdf:
                th_encabezados = f"""
                    <th style="width: 6%; text-align: center; white-space: nowrap;">ITEM</th>
                    <th style="width: 42%; text-align: left;">{sec_titulo}</th>
                    <th style="width: 22%; text-align: left;">MEDIDAS</th>
                    <th style="width: 12%; text-align: center;">JUEGOS/KITS</th>
                    <th style="width: 8%; text-align: center; white-space: nowrap;">CANT.</th>
                    <th style="width: 10%; text-align: right; white-space: nowrap;">PRECIO</th>
                """
            else:
                th_encabezados = f"""
                    <th style="width: 6%; text-align: center; white-space: nowrap;">ITEM</th>
                    <th style="width: 48%; text-align: left;">{sec_titulo}</th>
                    <th style="width: 26%; text-align: left;">MEDIDAS</th>
                    <th style="width: 12%; text-align: center;">JUEGOS/KITS</th>
                    <th style="width: 8%; text-align: center; white-space: nowrap;">CANT.</th>
                """

            html_cuerpo += f"""
            <table class="tabla-remastered">
                <thead>
                    <tr>{th_encabezados}</tr>
                </thead>
                <tbody>
            """
            
            subtotal_seccion = 0.0
            item_numeral = 1
            
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
                        subtotal_seccion += total_fila
                        
                        precio_str = f"{total_fila:,.2f}"
                        jk_str = f"{int(jk_val) if jk_val.is_integer() else jk_val}" if jk_val > 0 else ""
                        cant_str = f"{int(cant_val) if cant_val.is_integer() else cant_val}" if cant_val > 0 else ""
                        
                        td_precio = f'<td style="text-align: right;">{precio_str}</td>' if incluir_precios_pdf else ''
                        
                        html_cuerpo += f"""
                        <tr>
                            <td style="text-align: center;">{item_numeral}</td>
                            <td style="text-align: left;">{desc}</td>
                            <td style="text-align: left;">{med}</td>
                            <td style="text-align: center;">{jk_str}</td>
                            <td style="text-align: center;">{cant_str}</td>
                            {td_precio}
                        </tr>
                        """
                        item_numeral += 1
            
            if item_numeral == 1:
                colspan_val = 6 if incluir_precios_pdf else 5
                html_cuerpo += f'<tr><td colspan="{colspan_val}" style="text-align: center; color: #a0aec0; padding: 8px;">Sección sin registros activos</td></tr>'
                
            html_cuerpo += f"""
                </tbody>
            </table>
            <div class="contenedor-subtotal">
                <span>SUB TOTAL {sec_titulo}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span>
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
                <div style="font-weight: normal;">{clausulas_html}</div>
            </div>
        </div>
        """
        
        html_compreso = " ".join([line.strip() for line in html_cuerpo.splitlines()])
        st.markdown(html_compreso, unsafe_allow_html=True)