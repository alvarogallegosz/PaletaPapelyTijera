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
    """Renderiza el bloque HTML superior con la disponibilidad de las 5 cuentas."""
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
    """Formatea la cadena ingresada con puntos para miles y coma para decimales (estilo LATAM)."""
    val_str = st.session_state.get("carga_monto_texto", "").strip()

    if not val_str:
        st.session_state["monto_real_float"] = 0.0
        st.session_state["carga_monto_texto"] = ""
        return

    try:
        if "," in val_str and "." not in val_str:
            val_limpio = val_str.replace(",", ".")
        elif "," in val_str and "." in val_str:
            if val_str.rfind(",") > val_str.rfind("."):
                val_limpio = val_str.replace(".", "").replace(",", ".")
            else:
                val_limpio = val_str.replace(",", "")
        else:
            val_limpio = val_str

        monto_flt = float(val_limpio)
        st.session_state["monto_real_float"] = abs(monto_flt)

        s_aux = f"{abs(monto_flt):,.2f}"
        s_latam = s_aux.replace(",", "X").replace(".", ",").replace("X", ".")
        st.session_state["carga_monto_texto"] = s_latam

    except ValueError:
        st.session_state["monto_real_float"] = 0.0
        st.session_state["carga_monto_texto"] = "0,00"


def _procesar_registro_callback(rol_actual):
    """
    Callback que se ejecuta ANTES de redibujar la pantalla.
    Aquí es 100% seguro guardar en BD y limpiar las variables de sesión.
    """
    fecha_val = st.session_state.get("carga_fecha", datetime.date.today())
    categoria_val = str(st.session_state.get("carga_categoria", "")).strip()
    detalle_val = str(st.session_state.get("carga_detalle", "")).strip()
    tipo_val = st.session_state.get("carga_tipo", "IN-Bs")
    tasa_val = float(st.session_state.get("carga_tasa", 1.0))
    comentarios_val = str(st.session_state.get("carga_comentarios", "")).strip()
    monto_real = float(st.session_state.get("monto_real_float", 0.0))

    # Validaciones de campos
    errores = []
    if not categoria_val:
        errores.append("La **Categoría** es obligatoria.")
    if not detalle_val:
        errores.append("La **Descripción / Detalle** es obligatoria.")
    if monto_real <= 0:
        errores.append("El **Monto** debe ser mayor a 0,00.")
    if "Bs" in tipo_val and tasa_val <= 0:
        errores.append("La **Tasa Monitor** debe ser mayor a 0.")

    if errores:
        st.session_state["msg_carga"] = ("warning", errores)
        return

    # Validaciones contra Base de Datos
    df_fresco = obtener_movimientos_locales()
    ym_input = pd.to_datetime(fecha_val).strftime("%Y-%m")
    meses_cerrados_real = _obtener_meses_cerrados(df_fresco)

    if ym_input in meses_cerrados_real:
        st.session_state["msg_carga"] = ("error", ["❌ **BLOQUEO:** El mes seleccionado se encuentra consolidado."])
        return
    if _es_mes_anterior_al_inicio(df_fresco, ym_input):
        st.session_state["msg_carga"] = ("error", ["❌ **BLOQUEO:** El mes seleccionado es anterior al inicio histórico."])
        return

    # Inserción en Base de Datos
    nuevo_asiento = {
        "fecha": fecha_val.strftime("%Y-%m-%d"),
        "categoria": categoria_val.upper(),
        "detalle": detalle_val,
        "tipo": tipo_val,
        "monto": monto_real,
        "tasa": tasa_val if tasa_val > 0 else 1.0,
        "comentarios": comentarios_val,
        "activo": True,
        "consolidado": False,
        "creado_por": str(rol_actual),
    }

    exito, mensaje = insertar_movimiento_db(nuevo_asiento)

    if exito:
        st.session_state["df_movimientos"] = obtener_movimientos_locales()
        
        # 🧹 LIMPIEZA 100% SEGURA DENTRO DEL CALLBACK
        st.session_state["carga_monto_texto"] = ""
        st.session_state["monto_real_float"] = 0.0
        st.session_state["carga_categoria"] = ""
        st.session_state["carga_detalle"] = ""
        st.session_state["carga_comentarios"] = ""

        st.session_state["msg_carga"] = ("success", [f"🎉 {mensaje}"])
    else:
        st.session_state["msg_carga"] = ("error", [f"❌ FALLO EN BASE DE DATOS: {mensaje}"])


def render_carga(rol_actual, es_consolidado=False):
    # --- INICIALIZACIÓN DE VARIABLES DE ESTADO ---
    if "carga_monto_texto" not in st.session_state:
        st.session_state["carga_monto_texto"] = ""
    if "monto_real_float" not in st.session_state:
        st.session_state["monto_real_float"] = 0.0

    # --- SISTEMA DE NOTIFICACIONES POST-RECARGA ---
    if "msg_carga" in st.session_state:
        tipo, lista_mensajes = st.session_state["msg_carga"]
        for msg in lista_mensajes:
            if tipo == "success":
                st.success(msg)
            elif tipo == "warning":
                st.warning(f"⚠️ {msg}")
            elif tipo == "error":
                st.error(msg)
        del st.session_state["msg_carga"]

    # --- BANNER DE SALDOS ---
    df_actual = st.session_state.get("df_movimientos", pd.DataFrame())
    if df_actual.empty:
        df_actual = obtener_movimientos_locales()
        
    saldos_globales = _calcular_saldos_globales(df_actual)
    render_banner_saldos(saldos_globales)

    st.markdown("### 📝 Carga de Nuevos Movimientos de Caja")

    col1, col2 = st.columns(2)

    with col1:
        st.date_input(
            "Fecha de la transacción:",
            value=datetime.date.today(),
            help="Puedes seleccionar cualquier fecha de cualquier mes/año.",
            key="carga_fecha",
        )
        st.text_input(
            "Categoría (*):",
            placeholder="Ej: IMPRENTA, VENTA, ALQUILER...",
            key="carga_categoria",
        )
        st.text_input(
            "Descripción / Detalle (*):",
            placeholder="Ej: Pago de franelas cliente Marivet",
            key="carga_detalle",
        )

    with col2:
        st.selectbox(
            "Tipo de Cuenta (*):",
            options=[
                "IN-Bs", "EG-Bs", "IN-$Ze", "EG-$Ze", "IN-$Ch",
                "EG-$Ch", "IN-$AhZe", "EG-$AhZe", "IN-$AhCh", "EG-$AhCh",
            ],
            key="carga_tipo",
        )
        st.text_input(
            "Monto (*):",
            key="carga_monto_texto",
            on_change=_formatear_monto_callback,
            placeholder="0.00",
            help="Escribe el monto. Al presionar Enter o Tab se agregará el formato de miles.",
        )
        st.number_input(
            "Tasa de Cambio Monitor:", min_value=0.0, value=1.0, step=0.01, format="%.2f", key="carga_tasa",
        )

    st.text_area(
        "Comentarios adicionales (Opcional):", key="carga_comentarios"
    )

    st.divider()

    # --- VALIDACIÓN VISUAL PREVIA DE MESES ---
    fecha_sel = st.session_state.get("carga_fecha", datetime.date.today())
    meses_cerrados = _obtener_meses_cerrados(df_actual)
    ym_input = pd.to_datetime(fecha_sel).strftime("%Y-%m")
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
        # 🟢 EL BOTÓN INVOCA AL CALLBACK ANTES DE CUALQUIER REDIBUJADO DE LA PÁGINA
        st.button(
            "💾 Registrar Transacción en Base de Datos",
            type="primary",
            use_container_width=True,
            on_click=_procesar_registro_callback,
            args=(rol_actual,),
        )
