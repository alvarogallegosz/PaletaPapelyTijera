import datetime
import os
import time
import base64
import re
import pandas as pd
import streamlit as st

from print_pdf_utility import generar_pdf_presupuesto_nativo
from db_connection import guardar_presupuesto_db, obtener_presupuesto_por_id_db
from core_finance_engine import fecha_a_larga

# ===================================================
# 🛠️ HELPER PARSER NUMÉRICO SEGURO
# ===================================================

def a_flotante(val) -> float:
    """Convierte de forma segura cualquier valor (int, float, str con formato ES/EN) a float."""
    if pd.isna(val) or val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    
    s = str(val).strip()
    if not s:
        return 0.0
        
    try:
        if ',' in s and '.' in s:
            if s.rfind(',') > s.rfind('.'):
                s = s.replace('.', '').replace(',', '.')
            else:
                s = s.replace(',', '')
        elif ',' in s:
            s = s.replace(',', '.')
        
        return float(s)
    except Exception:
        return 0.0

# ===================================================
# 📦 FUNCIONES DE PERSISTENCIA Y REHIDRATACIÓN JSONB
# ===================================================
CLAUSULAS_POR_DEFECTO = """Las condiciones generales de nuestra oferta son las siguientes:
* Precios se entienden en: Dólares netos. El costo debe ser pagado el 50% a la aceptación del contrato y el otro 50% 2 días antes del evento.
* Si el pago lo realizará en bs la tasa que manejamos es Euro indicado por el Banco Central de Venezuela.
* Validez de la Oferta: 3 días contínuos.
* Si el cliente cancela el servicio (es decir no va a querer el servicio) 2 días antes del evento le será devuelto un 30% del monto pagado.
* Si el cliente cancela el servicio (es decir no va a querer el servicio) 1 día antes ó el día del evento no se le devolverá nada del monto pagado.
* El cliente es enteramente responsable de todo el material suministrado para el evento y cancelara cualquier daño al mismo.
Sin más a que hacer referencia, a la espera de vuestra consideración, nos despedimos de Ud.,
Atentamente,
Paletapapelytijera"""

def empaquetar_presupuesto_para_bd(usuario_activo: str):
    """Convierte el estado de la sesión en el diccionario adaptado a las columnas exactas de Supabase."""
    meta = st.session_state.get("meta_presupuesto", {})
    
    # 🛡️ TRIPLE PROTECCIÓN DE CLÁUSULAS: Garantizar que NUNCA viajen vacías a la BD
    clausulas_txt = st.session_state.get("clausulas_presupuesto")
    if not clausulas_txt or not str(clausulas_txt).strip():
        clausulas_txt = st.session_state.get("input_widget_clausulas")
    if not clausulas_txt or not str(clausulas_txt).strip():
        clausulas_txt = CLAUSULAS_POR_DEFECTO

    secciones_activas = st.session_state.get("lista_secciones", [])
    secciones_exportar = []
    monto_total_calculado = 0.0

    for sec in secciones_activas:
        sec_id = sec.get("id", "")
        sec_titulo = sec.get("titulo", "")
        df_sec = st.session_state.get(f"res_{sec_id}", st.session_state.get(f"df_{sec_id}", pd.DataFrame()))

        items_list = []
        if not df_sec.empty:
            for row in df_sec.to_dict("records"):
                desc = str(row.get("descripción", "") or "").strip()
                det = str(row.get("detalles", "") or "").strip()
                
                jk_val = a_flotante(row.get("dias"))
                cant_val = a_flotante(row.get("cantidad"))
                pu_val = a_flotante(row.get("precio_unitario"))

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

    # Inyectar metadata del descuento en el JSONB de secciones
    descuento_activado = meta.get("descuento_activado", False)
    descuento_porcentaje = float(meta.get("descuento_porcentaje", 0.0))
    
    secciones_exportar.append({
        "id": "meta_config_adicional",
        "titulo": "META_CONFIG",
        "items": [],
        "descuento_activado": descuento_activado,
        "descuento_porcentaje": descuento_porcentaje
    })

    if descuento_activado and descuento_porcentaje > 0:
        monto_descuento = monto_total_calculado * (descuento_porcentaje / 100)
        total_final = monto_total_calculado - monto_descuento
    else:
        total_final = monto_total_calculado

    f_evt = meta.get("fecha_evento")
    fecha_evt_db = f_evt.strftime("%Y-%m-%d") if isinstance(f_evt, (datetime.date, datetime.datetime)) else str(f_evt or "")

    return {
        "nombre": meta.get("nombre", "PRESUPUESTO SIN NOMBRE").strip().upper(),
        "cliente": meta.get("cliente", "CLIENTE").strip().upper(),
        "fecha_evento": fecha_evt_db,
        "lugar_evento": meta.get("lugar", "").strip(),
        "fecha_emision": datetime.date.today().strftime("%Y-%m-%d"),
        "tipo_presupuesto": meta.get("tipo_presupuesto", "Decoración"),
        "monto_total": round(total_final, 2),
        "clausulas": clausulas_txt,
        "secciones": secciones_exportar,
        "estado": "Borrador",
        "es_plantilla": False,
        "creado_por": usuario_activo
    }


def cargar_presupuesto_en_session_state(id_presupuesto: int):
    """Lee la fila desde Supabase y reconstruye los dataframes interactivos, descuentos y cláusulas sin truncamiento."""
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

    st.session_state.meta_presupuesto = {
        "nombre": data.get("nombre", ""),
        "cliente": data.get("cliente", ""),
        "fecha_evento": fecha_obj,
        "lugar": data.get("lugar_evento", ""),
        "fecha_larga": data.get("fecha_emision", ""),
        "tipo_presupuesto": data.get("tipo_presupuesto", "Decoración"),
        "descuento_activado": False,
        "descuento_porcentaje": 0.0
    }
    
    raw_clausulas = data.get("clausulas")
    if not raw_clausulas or not str(raw_clausulas).strip():
        st.session_state.clausulas_presupuesto = CLAUSULAS_POR_DEFECTO
        st.toast("⚠️ Presupuesto sin cláusulas registradas. Se cargaron las cláusulas base por defecto.", icon="🔔")
    else:
        st.session_state.clausulas_presupuesto = str(raw_clausulas)
    
    # Purgar el widget en memoria para que fuerce la relectura de 'clausulas_presupuesto'
    st.session_state.pop("input_widget_clausulas", None)
    st.session_state.presupuesto_id_activo = data.get("id")

    secciones_guardadas = data.get("secciones", [])
    if isinstance(secciones_guardadas, dict) and "secciones" in secciones_guardadas:
        secciones_guardadas = secciones_guardadas["secciones"]

    st.session_state.lista_secciones = []

    for sec in secciones_guardadas:
        sec_id = sec.get("id")
        
        if sec_id == "meta_config_adicional":
            st.session_state.meta_presupuesto["descuento_activado"] = sec.get("descuento_activado", False)
            st.session_state.meta_presupuesto["descuento_porcentaje"] = float(sec.get("descuento_porcentaje", 0.0))
            continue
            
        sec_titulo = sec.get("titulo")
        items_list = sec.get("items", [])

        st.session_state.lista_secciones.append({"id": sec_id, "titulo": sec_titulo})

        if items_list:
            df_sec = pd.DataFrame(items_list)
        else:
            df_sec = pd.DataFrame(columns=["descripción", "detalles", "dias", "cantidad", "precio_unitario"])
                    
        st.session_state[f"df_{sec_id}"] = df_sec
        st.session_state[f"res_{sec_id}"] = df_sec

    st.session_state.modo_vista = "edicion"
    return True

    
def resetear_formulario_presupuesto():
    """Restablece los campos a cero e inyecta las cláusulas por defecto."""
    st.session_state.meta_presupuesto = {
        "cliente": "", 
        "nombre": "", 
        "fecha_evento": datetime.date.today(), 
        "lugar": "", 
        "fecha_larga": "",
        "tipo_presupuesto": "Decoración",
        "descuento_activado": False,
        "descuento_porcentaje": 0.0
    }
    
    st.session_state.presupuesto_id_activo = None
    st.session_state.clausulas_presupuesto = CLAUSULAS_POR_DEFECTO
    st.session_state.pop("input_widget_clausulas", None)

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


def calcular_subtotal_df(df_input):
    """Calcula el subtotal dinámico para los indicadores de pantalla."""
    if df_input is None or df_input.empty:
        return 0.0

    subtotal = 0.0
    for _, row in df_input.iterrows():
        jk_val = a_flotante(row.get('dias'))
        cant_val = a_flotante(row.get('cantidad'))
        pu_val = a_flotante(row.get('precio_unitario'))

        total_fila = (jk_val * cant_val * pu_val) if jk_val > 0 else (cant_val * pu_val)
        subtotal += total_fila
        
    return round(subtotal, 2)


def render_creacion_presupuestos(rol_actual):
    st.markdown("""
        <style>
            ::-webkit-scrollbar {
                -webkit-appearance: none;
                width: 16px !important;
                height: 16px !important;
            }
            ::-webkit-scrollbar-thumb {
                background-color: #94a3b8 !important;
                border-radius: 8px !important;
                border: 3px solid #ffffff !important;
            }
            ::-webkit-scrollbar-track {
                background-color: #f1f5f9 !important;
                border-radius: 8px !important;
            }
            ::-webkit-scrollbar-thumb:hover {
                background-color: #64748b !important;
            }

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
        </style>
    """, unsafe_allow_html=True)

    if "modo_vista" not in st.session_state:
        st.session_state.modo_vista = "edicion"

    if "ultimo_guardado" not in st.session_state:
        st.session_state.ultimo_guardado = time.time()

    if "meta_presupuesto" not in st.session_state:
        resetear_formulario_presupuesto()

    if "clausulas_presupuesto" not in st.session_state or not str(st.session_state.clausulas_presupuesto).strip():
        st.session_state.clausulas_presupuesto = CLAUSULAS_POR_DEFECTO

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
    # 📝 MODO EDICIÓN
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

                df_vivo = st.data_editor(
                    st.session_state[df_key],
                    key=f"editor_widget_{sec_id}",
                    num_rows="dynamic",
                    width="stretch",
                    hide_index=True,
                    column_config={
                        "descripción": st.column_config.TextColumn("Descripción (80 ch)"),
                        "detalles": st.column_config.TextColumn("Detalles (40 ch)"),
                        "dias": st.column_config.NumberColumn("Días (11 ch)", min_value=1),
                        "cantidad": st.column_config.NumberColumn("Cantidad (8 ch)", min_value=1, default=1),
                        "precio_unitario": st.column_config.NumberColumn("Precio ($)", min_value=0.0, format="$%.2f")
                    }
                )

                registros_vivos = df_vivo.to_dict("records")
                duplicados_encontrados = False
                vistos = set()
                
                for r in registros_vivos:
                    clave = (
                        str(r.get("descripción", "")).strip().lower(),
                        str(r.get("detalles", "")).strip().lower(),
                        a_flotante(r.get("dias")),
                        a_flotante(r.get("cantidad")),
                        a_flotante(r.get("precio_unitario"))
                    )
                    if not any(clave):
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
        
        # --- 🏷️ MÓDULO DE DESCUENTOS ---
        st.markdown("---")
        st.markdown("### 🏷️ Opciones de Descuento")
        col_d1, col_d2 = st.columns([1, 2])
        
        with col_d1:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            st.session_state.meta_presupuesto["descuento_activado"] = st.toggle(
                "Aplicar descuento al Total", 
                value=st.session_state.meta_presupuesto.get("descuento_activado", False)
            )
            
        with col_d2:
            if st.session_state.meta_presupuesto["descuento_activado"]:
                st.session_state.meta_presupuesto["descuento_porcentaje"] = st.number_input(
                    "Porcentaje a descontar (%)", 
                    min_value=0.0, 
                    max_value=100.0, 
                    value=float(st.session_state.meta_presupuesto.get("descuento_porcentaje", 0.0)),
                    step=1.0,
                    format="%.2f"
                )
            else:
                st.session_state.meta_presupuesto["descuento_porcentaje"] = 0.0

        # --- 💵 RENDERIZADO DEL TOTAL GENERAL ---
        descuento_activado = st.session_state.meta_presupuesto.get("descuento_activado", False)
        descuento_porcentaje = float(st.session_state.meta_presupuesto.get("descuento_porcentaje", 0.0))

        if descuento_activado and descuento_porcentaje > 0:
            monto_descuento = total_acumulado_presupuesto * (descuento_porcentaje / 100)
            total_final = total_acumulado_presupuesto - monto_descuento
            
            st.markdown(f"""
            <div style="background-color: #f8fafc; padding: 10px 18px; border-radius: 6px; margin-top: 15px; margin-bottom: 5px; display: flex; justify-content: space-between; align-items: center; border: 1px solid #cbd5e1;">
                <span style="font-size: 14px; font-weight: bold; color: #64748b;">SUBTOTAL ANTES DE DESCUENTO</span>
                <span style="font-size: 16px; font-weight: bold; color: #64748b;">${total_acumulado_presupuesto:,.2f}</span>
            </div>
            <div style="background-color: #fee2e2; padding: 10px 18px; border-radius: 6px; margin-bottom: 5px; display: flex; justify-content: space-between; align-items: center; border: 1px solid #fca5a5;">
                <span style="font-size: 14px; font-weight: bold; color: #b91c1c;">DESCUENTO APLICADO ({descuento_porcentaje:,.2f}%)</span>
                <span style="font-size: 16px; font-weight: bold; color: #b91c1c;">- ${monto_descuento:,.2f}</span>
            </div>
            <div style="background-color: #b8d7a3; padding: 10px 18px; border-radius: 6px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; border: 1px solid #86efac;">
                <span style="font-size: 16px; font-weight: bold; color: #000000;">TOTAL GENERAL</span>
                <span style="font-size: 22px; font-weight: bold; color: #000000;">${total_final:,.2f}</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background-color: #b8d7a3; padding: 10px 18px; border-radius: 6px; margin-top: 15px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; border: 1px solid #86efac;">
                <span style="font-size: 16px; font-weight: bold; color: #000000;">TOTAL GENERAL ESTIMADO</span>
                <span style="font-size: 22px; font-weight: bold; color: #000000;">${total_acumulado_presupuesto:,.2f}</span>
            </div>
            """, unsafe_allow_html=True)

        # --- 📜 TÉRMINOS Y CLÁUSULAS CON CLAVE DESACOPLADA ---
        with st.container(border=True):
            st.markdown("## 📜 Términos y Cláusulas")
        
            if "clausulas_presupuesto" not in st.session_state or not str(st.session_state.clausulas_presupuesto).strip():
                st.session_state.clausulas_presupuesto = CLAUSULAS_POR_DEFECTO
        
            val_clausulas = st.text_area(
                "Modifique cláusulas si es necesario:",
                value=st.session_state.clausulas_presupuesto,
                key="input_widget_clausulas",
                height=150
            )
            # 🔑 Sincronización continua en la clave no-widget independiente
            st.session_state.clausulas_presupuesto = val_clausulas

        # Guardado Automático de Borrador
        tiempo_actual = time.time()
        if tiempo_actual - st.session_state.ultimo_guardado >= 300:
            usuario_activo = st.session_state.get("usuario_logueado", "Usuario")
            datos_payload = empaquetar_presupuesto_para_bd(usuario_activo)
            id_edicion = st.session_state.get("presupuesto_id_activo", None)
            
            if total_acumulado_presupuesto > 0:
                try:
                    guardar_presupuesto_db(datos_payload, id_presupuesto=id_edicion)
                    st.toast("💾 Borrador guardado automáticamente en la base de datos.", icon="☁️")
                except Exception:
                    pass
            
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
        
        # 🔑 Rescatar cláusulas persistentes
        clausulas_txt = st.session_state.get("clausulas_presupuesto") or CLAUSULAS_POR_DEFECTO
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
                    st.toast(f"🎉 {msj}", icon="💾")
                    st.rerun()
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

        total_general_pre_descuento = 0.0
        
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
                    
                    jk_val = a_flotante(row.get('dias'))
                    cant_val = a_flotante(row.get('cantidad'))
                    pu_val = a_flotante(row.get('precio_unitario'))

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
            total_general_pre_descuento += subtotal_seccion
            
        clausulas_html = str(clausulas_txt or '').replace("\n", "<br/>")

        descuento_activado = meta.get("descuento_activado", False)
        descuento_porcentaje = float(meta.get("descuento_porcentaje", 0.0))

        if descuento_activado and descuento_porcentaje > 0:
            monto_descuento_pdf = total_general_pre_descuento * (descuento_porcentaje / 100)
            total_final_pdf = total_general_pre_descuento - monto_descuento_pdf
            
            html_cuerpo += f"""
                <div style="background-color: #fee2e2; color: #b91c1c; font-weight: bold; font-size: 14px; text-align: right; padding: 6px 15px; margin-top: 10px; border-bottom: 1px solid #fca5a5;">
                    SUBTOTAL BASE: ${total_general_pre_descuento:,.2f} <br>
                    DESCUENTO ({descuento_porcentaje:,.2f}%): - ${monto_descuento_pdf:,.2f}
                </div>
                <div class="banner-total-general">
                    <span>TOTAL A CANCELAR</span>
                    <span>${total_final_pdf:,.2f}</span>
                </div>
            """
        else:
            html_cuerpo += f"""
                <div class="banner-total-general">
                    <span>TOTAL A CANCELAR</span>
                    <span>${total_general_pre_descuento:,.2f}</span>
                </div>
            """

        html_cuerpo += f"""
            <div class="clausulas-container">
                <div class="clausulas-header">CLAUSULAS:</div>
                <div style="font-weight: normal;">{clausulas_html}</div>
            </div>
        </div>
        """
        
        html_compreso = " ".join([line.strip() for line in html_cuerpo.splitlines()])
        st.markdown(html_compreso, unsafe_allow_html=True)
