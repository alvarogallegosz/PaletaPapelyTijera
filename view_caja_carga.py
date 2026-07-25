# view_caja_carga.py
import datetime
import pandas as pd
import streamlit as st
from db_connection import insertar_movimiento_db, obtener_movimientos_locales


def _obtener_meses_cerrados(df_datos) -> set:
    """Devuelve un set de strings 'YYYY-MM' que están bloqueados."""
    if df_datos is None or df_datos.empty or "consolidado" not in df_datos.columns:
        return set()
    df_temp = df_datos.copy()
    df_temp["ym"] = pd.to_datetime(df_temp["fecha"], errors="coerce").dt.strftime("%Y-%m")
    meses_bloqueados = df_temp[df_temp["consolidado"] == True]["ym"].unique()
    return set(meses_bloqueados)


def _es_mes_anterior_al_inicio(df_datos, ym_evaluar) -> bool:
    """Verifica si el mes evaluado es estrictamente anterior al primer mes registrado en la BD."""
    if df_datos is None or df_datos.empty:
        return False
    fecha_minima = pd.to_datetime(df_datos["fecha"]).min()
    ym_minimo = fecha_minima.strftime("%Y-%m")
    return ym_evaluar < ym_minimo


def _calcular_saldos_globales(df):
    """Calcula la disponibilidad neta global de las 5 cuentas en todo el histórico."""
    saldos = {'Bs': 0.0, 'Ze': 0.0, 'Ch': 0.0, 'AhZe': 0.0, 'AhCh': 0.0}
    if df is None or df.empty:
        return saldos
    for _, row in df.iterrows():
        try:
            monto = float(row["monto"]) if pd.notnull(row["monto"]) else 0.0
        except (ValueError, TypeError):
            monto = 0.0
        tipo = str(row.get("tipo", "")).strip()
        
        if tipo == "IN-Bs":
            saldos['Bs'] += monto
        elif tipo == "EG-Bs":
            saldos['Bs'] -= monto
        elif tipo == "IN-$Ze":
            saldos['Ze'] += monto
        elif tipo == "EG-$Ze":
            saldos['Ze'] -= monto
        elif tipo == "IN-$Ch":
            saldos['Ch'] += monto
        elif tipo == "EG-$Ch":
            saldos['Ch'] -= monto
        elif tipo == "IN-$AhZe":
            saldos['AhZe'] += monto
        elif tipo == "EG-$AhZe":
            saldos['AhZe'] -= monto
        elif tipo == "IN-$AhCh":
            saldos['AhCh'] += monto
        elif tipo == "EG-$AhCh":
            saldos['AhCh'] -= monto
    return saldos


def render_banner_saldos(saldos_dict):
    """Renderiza el bloque HTML superior con la disponibilidad de las 5 cuentas con idéntica estética."""
    val_bs = float(saldos_dict.get('Bs', 0.0))
    val_ze = float(saldos_dict.get('Ze', 0.0))
    val_ch = float(saldos_dict.get('Ch', 0.0))
    val_ah_ze = float(saldos_dict.get('AhZe', 0.0))
    val_ah_ch = float(saldos_dict.get('AhCh', 0.0))
    
    st.markdown(f"""
        <div style="font-size: 12px; background-color: #f8f9fa; padding: 10px 14px; border-radius: 6px; border-left: 4px solid #3b82f6; margin-top: 5px; margin-bottom: 12px; line-height: 1.8;">
            <strong>Saldos netos actuales en caja:</strong> <br>
            <span style="color: #111827;">🟢 <b>Bs:</b> {val_bs:,.2f}</span> &nbsp;|&nbsp;
            <span style="color: #111827;">🔵 <b>Zelle Operativo:</b> ${val_ze:,.2f}</span> &nbsp;|&nbsp;
            <span style="color: #111827;">💵 <b>Cash Operativo:</b> ${val_ch:,.2f}</span> &nbsp;|&nbsp;
            <span style="color: #0d9488;">🏦 <b>Ahorro Zelle:</b> ${val_ah_ze:,.2f}</span> &nbsp;|&nbsp;
            <span style="color: #0d9488;">🐷 <b>Ahorro Cash:</b> ${val_ah_ch:,.2f}</span>
        </div>
    """, unsafe_allow_html=True)


def _formatear_monto_callback():
    """Formatea la cadena ingresada con separadores de miles y 2 decimales al presionar Enter o Tab."""
    val_str = st.session_state.get("carga_monto_texto", "").strip()

    if not val_str:
        st.session_state["monto_real_float"] = 0.0
        st.session_state["carga_monto_texto"] = ""
        return

    try:
        # Limpieza inteligente para soportar tanto coma ',' como punto '.' como decimales
        if "," in val_str and "." not in val_str:
            # Solo tiene coma (ej: "1500,50" o "50,5") -> la convertimos en punto decimal
            val_limpio = val_str.replace(",", ".")
        elif "," in val_str and "." in val_str:
            # Tiene ambos: verificamos cuál está más a la derecha para saber cuál es el decimal
            if val_str.rfind(",") > val_str.rfind("."):
                # Formato europeo (ej: "1.500,50") -> quitamos puntos de miles y cambiamos coma por punto
                val_limpio = val_str.replace(".", "").replace(",", ".")
            else:
                # Formato anglosajón (ej: "1,500.50") -> solo quitamos las comas de miles
                val_limpio = val_str.replace(",", "")
        else:
            # Solo tiene puntos o ningún separador (ej: "1500.50" o "1500")
            val_limpio = val_str

        monto_flt = float(val_limpio)

        # 1. Guardamos el número flotante puro para insertar en Base de Datos
        st.session_state["monto_real_float"] = abs(monto_flt)

        # 2. Mostramos en pantalla el texto formateado bonito con separadores de miles
        st.session_state["carga_monto_texto"] = f"{abs(monto_flt):,.2f}"

    except ValueError:
        st.session_state["monto_real_float"] = 0.0
        st.session_state["carga_monto_texto"] = "0.00"


def render_carga(rol_actual, es_consolidado=False):
    # --- INICIALIZACIÓN DE VARIABLES DE ESTADO PARA EL MONTO ---
    if "carga_monto_texto" not in st.session_state:
        st.session_state["carga_monto_texto"] = ""
    if "monto_real_float" not in st.session_state:
        st.session_state["monto_real_float"] = 0.0

    # --- SISTEMA DE NOTIFICACIONES POST-RECARGA ---
    if "msg_carga" in st.session_state:
        tipo, texto = st.session_state["msg_carga"]
        if tipo == "success":
            st.success(texto)
        elif tipo == "error":
            st.error(texto)
        del st.session_state["msg_carga"] # Limpiamos para que no salga siempre

    # --- OBTENCIÓN Y RENDERIZADO DEL BANNER DE SALDOS EN EL TOPE ---
    df_actual = st.session_state.get("df_movimientos", pd.DataFrame())
    if df_actual.empty:
        df_actual = obtener_movimientos_locales()
        
    saldos_globales = _calcular_saldos_globales(df_actual)
    render_banner_saldos(saldos_globales)

    st.markdown("### 📝 Carga de Nuevos Movimientos de Caja")

    col1, col2 = st.columns(2)

    with col1:
        fecha_input = st.date_input(
            "Fecha de la transacción:",
            value=datetime.date.today(),
            help="Puedes seleccionar cualquier fecha de cualquier mes/año.",
            key="carga_fecha",
        )
        categoria_input = st.text_input(
            "Categoría (*):",
            placeholder="Ej: IMPRENTA, VENTA, ALQUILER...",
            key="carga_categoria",
        )
        detalle_input = st.text_input(
            "Descripción / Detalle (*):",
            placeholder="Ej: Pago de franelas cliente Marivet",
            key="carga_detalle",
        )

    with col2:
        tipo_input = st.selectbox(
            "Tipo de Cuenta (*):",
            options=[
                "IN-Bs", "EG-Bs", "IN-$Ze", "EG-$Ze", "IN-$Ch",
                "EG-$Ch", "IN-$AhZe", "EG-$AhZe", "IN-$AhCh", "EG-$AhCh",
            ],
            key="carga_tipo",
        )
        
        # 🟢 CAMBIO PRINCIPAL: Campo de texto dinámico con callback al dar Enter/Tab
        st.text_input(
            "Monto (*):",
            key="carga_monto_texto",
            on_change=_formatear_monto_callback,
            placeholder="0.00",
            help="Escribe el monto. Al presionar Enter o Tab se agregará el formato de miles.",
        )
        
        tasa_input = st.number_input(
            "Tasa de Cambio Monitor:", min_value=0.0, value=1.0, step=0.01, format="%.2f", key="carga_tasa",
        )

    comentarios_input = st.text_area(
        "Comentarios adicionales (Opcional):", key="carga_comentarios"
    )

    st.divider()

    # --- VALIDACIÓN VISUAL PREVIA ---
    meses_cerrados = _obtener_meses_cerrados(df_actual)
    ym_input = pd.to_datetime(fecha_input).strftime("%Y-%m")
    
    es_anterior = _es_mes_anterior_al_inicio(df_actual, ym_input)

    if ym_input in meses_cerrados:
        st.error(
            f"🔒 **CARGA SUSPENDIDA:** El mes ({ym_input}) se encuentra "
            "**CONSOLIDADO y BLOQUEADO**. No se admiten nuevos asientos."
        )
    elif es_anterior:
        st.error(
            f"🔒 **CARGA SUSPENDIDA:** El mes ({ym_input}) es anterior al inicio de "
            "operaciones registrado. Se encuentra cerrado predeterminadamente."
        )
    else:
        btn_registrar = st.button(
            "💾 Registrar Transacción en Base de Datos",
            type="primary",
            use_container_width=True,
        )

        if btn_registrar:
            # --- CANDADO ESTRICTO CONTRA LA BASE DE DATOS EN TIEMPO REAL ---
            with st.spinner("Validando auditoría en tiempo real..."):
                df_fresco = obtener_movimientos_locales()
                meses_cerrados_real = _obtener_meses_cerrados(df_fresco)
                
                if ym_input in meses_cerrados_real:
                    st.error("❌ **BLOQUEO:** El mes seleccionado acaba de ser bloqueado por otro administrador.")
                    return
                if _es_mes_anterior_al_inicio(df_fresco, ym_input):
                    st.error("❌ **BLOQUEO:** El mes seleccionado es anterior al inicio histórico de operaciones.")
                    return

            # Obtenemos el monto numérico limpio procesado por el callback
            monto_real = st.session_state.get("monto_real_float", 0.0)

            # Validaciones de formulario
            errores_validacion = []
            if not categoria_input.strip():
                errores_validacion.append("La **Categoría** es obligatoria.")
            if not detalle_input.strip():
                errores_validacion.append("La **Descripción / Detalle** es obligatoria.")
            if monto_real <= 0:
                errores_validacion.append("El **Monto** debe ser mayor a 0,00.")
            if "Bs" in tipo_input and tasa_input <= 0:
                errores_validacion.append("La **Tasa Monitor** debe ser mayor a 0.")

            if errores_validacion:
                for err in errores_validacion:
                    st.warning(f"⚠️ {err}")
                return

            nuevo_asiento = {
                "fecha": fecha_input.strftime("%Y-%m-%d"),
                "categoria": categoria_input.strip().upper(),
                "detalle": detalle_input.strip(),
                "tipo": tipo_input,
                "monto": float(monto_real),
                "tasa": float(tasa_input) if tasa_input > 0 else 1.0,
                "comentarios": comentarios_input.strip(),
                "activo": True,
                "consolidado": False,
                "creado_por": str(rol_actual),
            }

            exito, mensaje = insertar_movimiento_db(nuevo_asiento)

            if exito:
                st.session_state["df_movimientos"] = obtener_movimientos_locales()
                # Reseteamos los campos de monto para la siguiente carga
                st.session_state["carga_monto_texto"] = ""
                st.session_state["monto_real_float"] = 0.0
                
                # Guardamos el mensaje en memoria para que sobreviva al rerun
                st.session_state["msg_carga"] = ("success", f"🎉 {mensaje}")
                st.rerun()
            else:
                st.session_state["msg_carga"] = ("error", f"❌ FALLO EN BASE DE DATOS: {mensaje}")
                st.rerun()
