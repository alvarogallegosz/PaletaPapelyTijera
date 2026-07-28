import streamlit as st
import pandas as pd
import os
import time
import base64
import re
import datetime

from print_pdf_utility import generar_pdf_presupuesto_nativo
from db_connection import guardar_presupuesto_db, obtener_presupuesto_por_id_db
from core_finance_engine import fecha_a_larga
# ===================================================
# 📦 FUNCIONES DE PERSISTENCIA Y REHIDRATACIÓN JSONB
# ===================================================

def empaquetar_presupuesto_para_bd(usuario_activo: str):
    """Convierte el estado de la sesión en el diccionario adaptado a las columnas exactas de Supabase."""
    meta = st.session_state.get("meta_presupuesto", {})
    clausulas_txt = st.session_state.get("clausulas_presupuesto", "")
    secciones_activas = st.session_state.get("lista_secciones", [])

    secciones_exportar = []
    monto_total_calculado = 0.0

    for sec in secciones_activas:
        sec_id = sec.get("id", "")
        sec_titulo = sec.get("titulo", "")
        # FIX 1: Se restauró st.session_state
        df_sec = st.session_state.get(f"res_{sec_id}", st.session_state.get(f"df_{sec_id}", pd.DataFrame()))

        items_list = []
        if not df_sec.empty:
            for row in df_sec.to_dict("records"):
                desc = str(row.get("descripción", "") or "").strip()
                det = str(row.get("detalles", "") or "").strip()
                
                try:
                    jk_val = float(row.get("dias")) if pd.notna(row.get("dias")) and str(row.get("dias")).strip() != "" else 0.0
                except Exception:
                    jk_val = 0.0
                    
                try:
                    cant_val = float(row.get("cantidad")) if pd.notna(row.get("cantidad")) and str(row.get("cantidad")).strip() != "" else 0.0
                except Exception:
                    cant_val = 0.0
                    
                try:
                    pu_val = float(row.get("precio_unitario")) if pd.notna(row.get("precio_unitario")) and str(row.get("precio_unitario")).strip() != "" else 0.0
                except Exception:
                    pu_val = 0.0

                if desc or det or jk_val or cant_val or pu_val:
                    total_fila = (jk_val * cant_val * pu_val) if jk_val > 0 else (cant_val * pu_val)
                    monto_total_calculado += total_fila
                    items_list.append({
                        "descripción": desc,
                        "detalles": det,
                        "dias": jk_val,
                        "cantidad": cant_val,
                        "precio_unitario": pu_val
                    })

        secciones_exportar.append({
            "id": sec_id,
            "titulo": sec_titulo,
            "items": items_list
        })

    f_evt = meta.get("fecha_evento")
    fecha_evt_db = f_evt.strftime("%Y-%m-%d") if isinstance(f_evt, (datetime.date, datetime.datetime)) else str(f_evt or "")

    # Mapeo idéntico al esquema de la tabla 'presupuestos'
    return {
        "nombre": meta.get("nombre", "PRESUPUESTO SIN NOMBRE").strip().upper(),
        "cliente": meta.get("cliente", "CLIENTE").strip().upper(),
        "fecha_evento": fecha_evt_db,
        "lugar_evento": meta.get("lugar", "").strip(),
        "fecha_emision": datetime.date.today().strftime("%Y-%m-%d"),
        "tipo_presupuesto": meta.get("tipo_presupuesto", "Decoración"),
        "monto_total": round(monto_total_calculado, 2),
        "clausulas": clausulas_txt,
        "secciones": secciones_exportar,  # Columna jsonb directa
        "estado": "Borrador",
        "es_plantilla": False
    }


def cargar_presupuesto_en_session_state(id_presupuesto: int):
    """Lee la fila desde Supabase y reconstruye los dataframes interactivos."""
    data = obtener_presupuesto_por_id_db(id_presupuesto)
    if not data:
        return False

    raw_fecha = data.get("fecha_evento", "")
    fecha_obj = datetime.date.today()
    if raw_fecha:
        try:
            fecha_obj = datetime.datetime.strptime(str(raw_fecha), "%Y-%m-%d").date()
        except ValueError:
            pass

    # FIX 2: Se restauró st.session_state
    st.session_state.meta_presupuesto = {
        "nombre": data.get("nombre", ""),
        "cliente": data.get("cliente", ""),
        "fecha_evento": fecha_obj,
        "lugar": data.get("lugar_evento", ""),
        "fecha_larga": data.get("fecha_emision", ""),
        "tipo_presupuesto": data.get("tipo_presupuesto", "Decoración")
    }
    # FIX 3 y 4: Se restauró st.session_state
    st.session_state.clausulas_presupuesto = data.get("clausulas", "")
    st.session_state.presupuesto_id_activo = data.get("id")

    # Lectura directa desde la columna 'secciones'
    secciones_guardadas = data.get("secciones", [])
    if isinstance(secciones_guardadas, dict) and "secciones" in secciones_guardadas:
        secciones_guardadas = secciones_guardadas["secciones"]

    # FIX 5: Se restauró st.session_state
    st.session_state.lista_secciones = []

    for sec in secciones_guardadas:
        sec_id = sec.get("id")
        sec_titulo = sec.get("titulo")
        items_list = sec.get("items", [])

        # FIX 6: Se restauró st.session_state
        st.session_state.lista_secciones.append({"id": sec_id, "titulo": sec_titulo})

        if items_list:
            df_sec = pd.DataFrame(items_list)
        else:
            df_sec = pd.DataFrame(columns=["descripción", "detalles", "dias", "cantidad", "precio_unitario"])
                    
        # FIX 7: Se restauró st.session_state
        st.session_state[f"df_{sec_id}"] = df_sec

    st.session_state.modo_vista = "edicion"
    return True

def resetear_formulario_presupuesto():
    """Carga la plantilla fija ID=1 si existe; si no, realiza el reseteo limpio en memoria."""
    cargado = cargar_presupuesto_en_session_state(1)
    
    if cargado:
        st.session_state.meta_presupuesto.update({
            "cliente": "", 
            "nombre": "", 
            "fecha_evento": datetime.date.today(), 
            "lugar": "", 
            "fecha_larga": ""
        })
        st.session_state.presupuesto_id_activo = None
    else:
        # Fallback si la plantilla ID=1 aún no existe en la BD
        st.session_state.meta_presupuesto = {
            "cliente": "", 
            "nombre": "", 
            "fecha_evento": datetime.date.today(), 
            "lugar": "", 
            "fecha_larga": "",
            "tipo_presupuesto": "Decoración"
        }
        
        if "presupuesto_id_activo" in st.session_state:
            st.session_state.presupuesto_id_activo = None

        secciones_actuales = st.session_state.get("lista_secciones", [])
        for sec in secciones_actuales:
            sec_id = sec.get("id")
            st.session_state.pop(f"df_{sec_id}", None)
            st.session_state.pop(f"res_{sec_id}", None)
            st.session_state.pop(f"editor_widget_{sec_id}", None)
            st.session_state.pop(f"tit_input_{sec_id}", None)

        nuevo_id = f"sec_{int(time.time() * 1000)}"
        st.session_state.lista_secciones = [
            {"id": nuevo_id, "titulo": "DECORACIÓN PRINCIPAL"}
        ]
        st.session_state[f"df_{nuevo_id}"] = pd.DataFrame(
            columns=["descripción", "detalles", "dias", "cantidad", "precio_unitario"]
        )

        st.session_state.clausulas_presupuesto = ""

def calcular_subtotal_df(df_input):
    """
    Calcula el subtotal dinámico (Días * Cantidad * PU) para los
    indicadores de pantalla sin alterar la estructura del data_editor.
    """
    if df_input is None or df_input.empty:
        return 0.0

    subtotal = 0.0
    for _, row in df_input.iterrows():
        # Procesar Días
        jk_raw = row.get('dias')
        try:
            if pd.notna(jk_raw) and str(jk_raw).strip() != '':
                jk_str = str(jk_raw).strip().replace('.', '').replace(',', '.')
                jk_val = float(jk_str)
            else:
                jk_val = 0.0
        except Exception:
            jk_val = 0.0
            
        # Procesar Cantidad
        cant_raw = row.get('cantidad')
        try:
            if pd.notna(cant_raw) and str(cant_raw).strip() != '':
                cant_str = str(cant_raw).strip().replace('.', '').replace(',', '.')
                cant_val = float(cant_str)
            else:
                cant_val = 0.0
        except Exception:
            cant_val = 0.0
            
        # Procesar Precio Unitario (con soporte robusto para formato LATAM)
        pu_raw = row.get('precio_unitario')
        try:
            if pd.notna(pu_raw) and str(pu_raw).strip() != '':
                pu_str = str(pu_raw).strip()
                if ',' in pu_str and '.' in pu_str:
                    if pu_str.rfind(',') > pu_str.rfind('.'):
                        pu_str = pu_str.replace('.', '').replace(',', '.')
                    else:
                        pu_str = pu_str.replace(',', '')
                elif ',' in pu_str:
                    pu_str = pu_str.replace(',', '.')
                pu_val = float(pu_str)
            else:
                pu_val = 0.0
        except Exception:
            pu_val = 0.0

        total_fila = (jk_val * cant_val * pu_val) if jk_val > 0 else (cant_val * pu_val)
        subtotal += total_fila
        
    return round(subtotal, 2)


def render_creacion_presupuestos(rol_actual):
    # --- 🎨 CONTROL DE INYECCIÓN CSS PARA AISLAMIENTO DE IMPRESIÓN Y VISTA PREVIA ---
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
                align-items: flex-start;
                font-size: 13px;
                line-height: 1.5;
                margin-top: 10px;
                margin-bottom: 12px;
            }
            .meta-izquierda { flex: 1; font-weight: normal; }
            .meta-derecha { text-align: right; font-weight: bold; white-space: nowrap; padding-left: 15px; }

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

            div[data-testid="stMarkdownContainer"] h2,
            div[data-testid="stMarkdownContainer"] h3,
            div[data-testid="stMarkdownContainer"] h4 {
                margin-top: 2px !important;
                margin-bottom: 4px !important;
                padding-top: 0px !important;
                padding-bottom: 0px !important;
            }
            
            div[data-testid="stTabs"] {
                margin-bottom: -10px !important;
            }
            
            div[data-testid="stToggle"] {
                margin-top: -6px !important;
                margin-bottom: -6px !important;
                padding-top: 0px !important;
                padding-bottom: 0px !important;
            }
            
            div[data-testid="stVerticalBlock"] {
                gap: 0.5rem !important;
            }
            
            hr {
                margin-top: 8px !important;
                margin-bottom: 12px !important;
            }
        </style>
    """, unsafe_allow_html=True)

    # --- 🔄 CONTROL DE ESTADOS Y AUTOGUARDADO ---
    if "modo_vista" not in st.session_state:
        st.session_state.modo_vista = "edicion"

    if "ultimo_guardado" not in st.session_state:
        st.session_state.ultimo_guardado = time.time()

    if "meta_presupuesto" not in st.session_state:
        resetear_formulario_presupuesto()

    if "clausulas_presupuesto" not in st.session_state:
        st.session_state.clausulas_presupuesto = ""

    if "lista_secciones" not in st.session_state:
        st.session_state.lista_secciones = [
            {"id": "sec_inicial_1", "titulo": "DECORACIÓN PRINCIPAL"}
        ]

    sugerencias_titulos = [
        "DECORACIÓN PRINCIPAL",
        "ZONA DE CENTRO DE MESA",
        "ZONA DE DULCES / TORTA",
        "MONTAJE Y LOGÍSTICA",
        "OTROS SERVICIOS",
        "ÁREA DE BIENVENIDA / ENTRADA",
        "ILUMINACIÓN Y EFECTOS",
        "ESTRUCTURA Y TOLDOS",
        "MOBILIARIO COMPLEMENTARIO",
        "PERSONAL Y PROTOCOLO",
        "SERVICIOS ADICIONALES"
    ]

    # ===================================================
    # 📝 MODO EDICIÓN (PANTALLA DE CARGA)
    # ===================================================
    if st.session_state.modo_vista == "edicion":
        col_tit, col_btn = st.columns([3, 1])
        with col_tit:
            st.markdown("# 📝 Creación de Presupuesto Nuevo")
        with col_btn:
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            if st.button("🧹 Limpiar datos / Comenzar desde Cero", use_container_width=True, help="Borra todos los campos y restablece el formulario"):
                resetear_formulario_presupuesto()
                st.toast("✨ Formulario limpiado correctamente.", icon="🧹")
                st.rerun()
        
        with st.container(border=True):
            st.markdown("## 🏛️ Datos de Encabezado")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.session_state.meta_presupuesto["nombre"] = st.text_input(
                    "Nombre del Presupuesto:", 
                    value=st.session_state.meta_presupuesto.get("nombre", ""),
                    placeholder="Ej: MOD 2 DECORACIÓN COMUNIÓN"
                )
                st.session_state.meta_presupuesto["cliente"] = st.text_input(
                    "Cliente / Razón Social:", 
                    value=st.session_state.meta_presupuesto.get("cliente", ""),
                    placeholder="Ej: Sra. María Pérez"
                )
            with c2:
                val_fecha = st.session_state.meta_presupuesto.get("fecha_evento")
                if not isinstance(val_fecha, (datetime.date, datetime.datetime)):
                    val_fecha = datetime.date.today()

                fecha_sel = st.date_input(
                    "Fecha del Evento:", 
                    value=val_fecha,
                    format="DD/MM/YYYY"
                )
                st.session_state.meta_presupuesto["fecha_evento"] = fecha_sel
                st.caption(f"🗓️ **Vista larga:** {fecha_a_larga(fecha_sel)}")

                st.session_state.meta_presupuesto["lugar"] = st.text_input(
                    "Lugar del Evento:", 
                    value=st.session_state.meta_presupuesto.get("lugar", ""),
                    placeholder="Ej: REST. LA CASONA, LECHERÍA"
                )
            with c3:
                st.session_state.meta_presupuesto["fecha_larga"] = st.text_input(
                    "Fecha de Emisión:", 
                    value=st.session_state.meta_presupuesto.get("fecha_larga", ""),
                    placeholder="Ej: 17 de julio de 2026"
                )
                opciones_tipo = ["Decoración", "Alquiler", "Fiesta", "Cajas", "Otros"]
                idx_sel = opciones_tipo.index(st.session_state.meta_presupuesto.get("tipo_presupuesto", "Decoración")) if st.session_state.meta_presupuesto.get("tipo_presupuesto") in opciones_tipo else 0
                st.session_state.meta_presupuesto["tipo_presupuesto"] = st.selectbox(
                    "Tipo de Presupuesto (solo para BD):",
                    options=opciones_tipo,
                    index=idx_sel
                )

        st.markdown("## 📦 Bloques de Catálogo")
        
        if st.button("➕ Añadir Nueva Sección Física", disabled=len(st.session_state.lista_secciones) >= 11):
            nuevo_id = f"sec_{int(time.time() * 1000)}"
            idx_nuevo = len(st.session_state.lista_secciones)
            sug_titulo = sugerencias_titulos[idx_nuevo] if idx_nuevo < len(sugerencias_titulos) else f"NUEVA ZONA {idx_nuevo + 1}"
            
            st.session_state.lista_secciones.append({
                "id": nuevo_id,
                "titulo": sug_titulo
            })
            st.session_state[f"df_{nuevo_id}"] = pd.DataFrame(columns=["descripción", "detalles", "dias", "cantidad", "precio_unitario"])
            st.rerun()

        total_acumulado_presupuesto = 0.0

        for idx, sec in enumerate(st.session_state.lista_secciones):
            sec_id = sec["id"]
            df_key = f"df_{sec_id}"
            res_key = f"res_{sec_id}"
            
            if df_key not in st.session_state:
                st.session_state[df_key] = pd.DataFrame(columns=["descripción", "detalles", "dias", "cantidad", "precio_unitario"])
            
            max_filas = 24 if idx == 0 else 15
            sug_placeholder = sugerencias_titulos[idx] if idx < len(sugerencias_titulos) else f"Ej: ZONA {idx+1}"
                
            with st.container(border=True):
                col_t1, col_t2 = st.columns([5, 1])
                with col_t1:
                    tit_sec = st.text_input(
                        f"Título de la Sección {idx+1}:", 
                        value=sec["titulo"], 
                        placeholder=f"Ej: {sug_placeholder}",
                        key=f"tit_input_{sec_id}"
                    )
                    st.session_state.lista_secciones[idx]["titulo"] = tit_sec.upper() if tit_sec else f"SECCIÓN {idx+1}"
                with col_t2:
                    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                    if st.button("🗑️", key=f"del_{sec_id}", use_container_width=True) and len(st.session_state.lista_secciones) > 1:
                        st.session_state.lista_secciones.pop(idx)
                        st.session_state.pop(df_key, None)
                        st.session_state.pop(res_key, None)
                        st.rerun()

                # APLICACIÓN DE MANTENIMIENTO PREVENTIVO
                df_vivo = st.data_editor(
                    st.session_state[df_key],
                    key=f"editor_widget_{sec_id}",
                    num_rows="dynamic",
                    width="stretch", # Corrección: Reemplaza a use_container_width=True
                    hide_index=True,
                    column_config={
                        "descripción": st.column_config.TextColumn("Descripción (80 ch)"),
                        "detalles": st.column_config.TextColumn("Detalles (40 ch)"),
                        "dias": st.column_config.NumberColumn("Días (11 ch)", min_value=1),
                        "cantidad": st.column_config.NumberColumn("Cantidad (8 ch)", min_value=1, default=1),
                        "precio_unitario": st.column_config.NumberColumn("Precio ($)", min_value=0.0, format="$%.2f")
                    }
                )
# --- 🔍 VALIDACIÓN DE DUPLICADOS Y BORRADO LÓGICO ---
                registros_vivos = df_vivo.to_dict("records")
                duplicados_encontrados = False
                vistos = set()
                
                for r in registros_vivos:
                    clave = (
                        str(r.get("descripción", "")).strip().lower(),
                        str(r.get("detalles", "")).strip().lower(),
                        float(r.get("dias") or 0) if pd.notna(r.get("dias")) else 0.0,
                        float(r.get("cantidad") or 0) if pd.notna(r.get("cantidad")) else 0.0,
                        float(r.get("precio_unitario") or 0) if pd.notna(r.get("precio_unitario")) else 0.0
                    )
                    if not any(clave): # Omitir filas vacías
                        continue
                    if clave in vistos:
                        duplicados_encontrados = True
                        break
                    vistos.add(clave)

                key_dup_confirm = f"confirmar_dup_{sec_id}"
                if duplicados_encontrados and not st.session_state.get(key_dup_confirm, False):
                    st.warning("⚠️ Se han detectado asientos idénticos con los mismos datos exactos en esta sección.")
                    if st.button("Confirmar y aceptar asientos idénticos", key=f"btn_conf_dup_{sec_id}", type="secondary"):
                        st.session_state[key_dup_confirm] = True
                        st.rerun()
                    else:
                        st.stop()
                elif not duplicados_encontrados:
                    st.session_state[key_dup_confirm] = False
                    
                if len(df_vivo) > max_filas:
                    st.error(f"⚠️ Sección {idx+1} limitada a {max_filas} líneas máximas.")
                    df_guardar = df_vivo.head(max_filas)
                else:
                    df_guardar = df_vivo

                st.session_state[res_key] = df_guardar

                subtotal_seccion = calcular_subtotal_df(df_guardar)
                total_acumulado_presupuesto += subtotal_seccion

                col_sub_l, col_sub_r = st.columns([2, 2])
                with col_sub_r:
                    st.markdown(
                        f"""
                        <div style="text-align: right; font-size: 14px; font-weight: bold; background-color: #f8fafc; padding: 6px 12px; border-radius: 6px; border: 1px solid #e2e8f0; margin-top: 4px;">
                            SUB TOTAL {st.session_state.lista_secciones[idx]['titulo']}: <span style="color: #059669;">${subtotal_seccion:,.2f}</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

        st.markdown(
            f"""
            <div style="background-color: #b8d7a3; padding: 10px 18px; border-radius: 6px; margin-top: 15px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; border: 1px solid #86efac;">
                <span style="font-size: 16px; font-weight: bold; color: #000000;">TOTAL GENERAL ESTIMADO</span>
                <span style="font-size: 22px; font-weight: bold; color: #000000;">${total_acumulado_presupuesto:,.2f}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

        with st.container(border=True):
            st.markdown("## 📜 Términos y Cláusulas")
            st.session_state.clausulas_presupuesto = st.text_area("Modifique cláusulas si es necesario:", value=st.session_state.clausulas_presupuesto, height=150)

        # --- LÓGICA DE AUTOGUARDADO TEMPORAL ---
        tiempo_actual = time.time()
        if tiempo_actual - st.session_state.ultimo_guardado >= 300: # 300 segundos = 5 minutos
            usuario_activo = st.session_state.get("usuario_logueado", "Usuario")
            datos_payload = empaquetar_presupuesto_para_bd(usuario_activo)
            id_edicion = st.session_state.get("presupuesto_id_activo", None)
            
            # Solo guardamos si el presupuesto tiene al menos un item costeado
            if total_acumulado_presupuesto > 0:
                try:
                    guardar_presupuesto_db(datos_payload, id_presupuesto=id_edicion)
                    st.toast("💾 Borrador guardado automáticamente en la base de datos.", icon="☁️")
                except Exception:
                    pass # Se omite la interrupción visual en caso de fallo de conexión temporal
            
            # Se resetea el reloj independientemente del resultado para no saturar la red
            st.session_state.ultimo_guardado = tiempo_actual

        st.markdown("---")
        if st.button("👁️ Generar Vista Previa del Documento", type="primary", use_container_width=True):
            st.session_state.modo_vista = "previa"
            st.rerun()

    # ===================================================
    # 🖨️ MODO VISTA PREVIA
    # ===================================================
    else:
        meta = st.session_state.get("meta_presupuesto", {})
        clausulas_txt = st.session_state.get("clausulas_presupuesto", "")
        secciones_activas = st.session_state.get("lista_secciones", [])

        for sec in secciones_activas:
            sec_id = sec.get('id', '')
            res_key = f"res_{sec_id}"
            df_key = f"df_{sec_id}"
            if res_key in st.session_state:
                st.session_state[df_key] = st.session_state[res_key]

        st.markdown("### 👁️ Vista Previa del Documento")
        
        incluir_precios_pdf = st.toggle(
            "📊 Incluir columna de Precios Unitarios en el PDF y Vista Previa", 
            value=False,
            help="Activa para mostrar el precio individual de cada ítem, o desactiva para mostrar solo los subtotales."
        )
        
        # --- Generar PDF y Nombrado Dinámico ---
        pdf_bytes = generar_pdf_presupuesto_nativo(incluir_precios=incluir_precios_pdf)
        
        p_nombre = str(meta.get("nombre", "PRESUPUESTO")).strip().upper() or "PRESUPUESTO"
        p_fecha_larga = fecha_a_larga(meta.get("fecha_evento"))

        nombre_clean = re.sub(r'[^\w\s-]', '', p_nombre).strip().replace(" ", "_")
        fecha_clean = re.sub(r'[^\w\s-]', '', p_fecha_larga).strip().replace(" ", "_")

        nombre_archivo_pdf = f"Presupuesto_{nombre_clean}_{fecha_clean}.pdf"
        
        col_pv1, col_pv2, col_pv3 = st.columns(3)
                
        with col_pv1:
            if st.button("✏️ Regresar a Edición", type="secondary", use_container_width=True):
                st.session_state.modo_vista = "edicion"
                st.rerun()
                
        with col_pv2:
            st.download_button(
                label="📥 Descargar Presupuesto PDF",
                data=pdf_bytes,
                file_name=nombre_archivo_pdf,
                mime="application/pdf",
                use_container_width=True
            )
            
        with col_pv3:
            puede_guardar = rol_actual in ["administrador", "gerente"]
            if st.button("💾 Guardar en Base de Datos", disabled=not puede_guardar, type="primary", use_container_width=True):
                usuario_activo = st.session_state.get("usuario_logueado", "Usuario")
                datos_payload = empaquetar_presupuesto_para_bd(usuario_activo)
                id_edicion = st.session_state.get("presupuesto_id_activo", None)
                
                exito, msj = guardar_presupuesto_db(datos_payload, id_presupuesto=id_edicion)
                if exito:
                    st.success(f"🎉 {msj}")
                else:
                    st.error(f"❌ {msj}")
        
        st.markdown("---")

        ancho_logo_deseado = "80%"
        logo_nombre = "encabezado_paleta.png"
        ruta_script = os.path.join(os.path.dirname(__file__), logo_nombre)
        ruta_raiz = os.path.join(os.getcwd(), logo_nombre)
        ruta_final = ruta_script if os.path.exists(ruta_script) else (ruta_raiz if os.path.exists(ruta_raiz) else None)
        
        if ruta_final:
            with open(ruta_final, "rb") as f:
                data_img = base64.b64encode(f.read()).decode("utf-8")
            
            html_logo = f"""
            <img src="data:image/png;base64,{data_img}" 
                 style="width: {ancho_logo_deseado}; 
                        height: auto; 
                        display: block; 
                        margin: 0 auto 15px auto;">
            """
        else:
            html_logo = f"""
            <div style="background-color: #f2f2f2; 
                        border: 2px dashed #cbd5e1; 
                        padding: 20px; 
                        text-align: center; 
                        font-weight: bold; 
                        color: #64748b; 
                        margin: 0 auto 15px auto; 
                        width: {ancho_logo_deseado};">
                [ LOGO: {logo_nombre} NO DETECTADO ]
            </div>
            """
        
        p_nombre = str(meta.get('nombre', '') or '').upper() or 'PRESUPUESTO'
        p_fecha_evt = fecha_a_larga(meta.get('fecha_evento'))
        p_cliente = str(meta.get('cliente', '') or '').upper() or 'N/A'
        p_lugar = str(meta.get('lugar', '') or '').upper() or 'N/A'
        p_emision = str(meta.get('fecha_larga', '') or '').upper() or 'N/A'

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
            df_sec = st.session_state.get(f"res_{sec_id}", st.session_state.get(f"df_{sec_id}", pd.DataFrame()))
            
            if incluir_precios_pdf:
                th_cols = f"""
                    <th style="width: 8%; text-align: center; white-space: nowrap;">ITEM</th>
                    <th style="width: 44%; text-align: left;">{sec_titulo}</th>
                    <th style="width: 20%; text-align: left;">DETALLES</th>
                    <th style="width: 9%; text-align: center;">DÍAS</th>
                    <th style="width: 8%; text-align: center; white-space: nowrap;">CANT.</th>
                    <th style="width: 11%; text-align: right; white-space: nowrap;">PRECIO</th>
                """
            else:
                th_cols = f"""
                    <th style="width: 8%; text-align: center; white-space: nowrap;">ITEM</th>
                    <th style="width: 52%; text-align: left;">{sec_titulo}</th>
                    <th style="width: 23%; text-align: left;">DETALLES</th>
                    <th style="width: 9%; text-align: center;">DÍAS</th>
                    <th style="width: 8%; text-align: center; white-space: nowrap;">CANT.</th>
                """

            html_cuerpo += f"""
            <table class="tabla-remastered">
                <thead>
                    <tr>{th_cols}</tr>
                </thead>
                <tbody>
            """
            
            subtotal_seccion = 0.0
            item_numeral = 1
            
            if not df_sec.empty:
                for row in df_sec.to_dict('records'):
                    desc = str(row.get('descripción', '') or '').strip().replace("\n", " ").replace("\r", "").replace("  ", " ")
                    det = str(row.get('detalles', '') or '').strip().replace("\n", " ").replace("\r", "").replace("  ", " ")
                    
                    try:
                        jk_val = float(row.get('dias')) if pd.notna(row.get('dias')) and row.get('dias') != '' else 0.0
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

                    if desc or det or jk_val or cant_val or pu_val:
                        total_fila = (jk_val * cant_val * pu_val) if jk_val > 0 else (cant_val * pu_val)
                        subtotal_seccion += total_fila
                        
                        jk_str = f"{int(jk_val) if jk_val.is_integer() else jk_val}" if jk_val > 0 else ""
                        cant_str = f"{int(cant_val) if cant_val.is_integer() else cant_val}" if cant_val > 0 else ""
                        
                        if incluir_precios_pdf:
                            precio_str = f"{total_fila:,.2f}"
                            td_cols = f"""
                                <td style="text-align: center;">{item_numeral}</td>
                                <td style="text-align: left;">{desc}</td>
                                <td style="text-align: left;">{det}</td>
                                <td style="text-align: center;">{jk_str}</td>
                                <td style="text-align: center;">{cant_str}</td>
                                <td style="text-align: right;">{precio_str}</td>
                            """
                        else:
                            td_cols = f"""
                                <td style="text-align: center;">{item_numeral}</td>
                                <td style="text-align: left;">{desc}</td>
                                <td style="text-align: left;">{det}</td>
                                <td style="text-align: center;">{jk_str}</td>
                                <td style="text-align: center;">{cant_str}</td>
                            """

                        html_cuerpo += f"<tr>{td_cols}</tr>"
                        item_numeral += 1
            
            if item_numeral == 1:
                colspan_val = 6 if incluir_precios_pdf else 5
                html_cuerpo += f'<tr><td colspan="{colspan_val}" style="text-align: center; color: #a0aec0; padding: 8px;">Sección sin registros activos</td></tr>'
                
            html_cuerpo += f"""
                </tbody>
            </table>
            <div class="contenedor-subtotal">
                <span>SUB TOTAL {sec_titulo}:&nbsp;&nbsp;&nbsp;&nbsp;</span>
                <span>${subtotal_seccion:,.2f}</span>
            </div>
            """
            total_general += subtotal_seccion
            
        clausulas_html = str(clausulas_txt or '').replace("\n", "<br/>")

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
