# view_caja_carga.py
import datetime
import time
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


def render_carga(rol_actual, es_consolidado=False):
    # --- SISTEMA DE NOTIFICACIONES POST-RECARGA ---
    if "msg_carga" in st.session_state:
        tipo, texto = st.session_state.pop("msg_carga")
        if tipo == "success":
            st.success(texto)
            st.toast(texto, icon="🎉")
        elif tipo == "error":
            st.error(texto)
            st.toast(texto, icon="❌")

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
        monto_input = st.number_input(
            "Monto (*):", min_value=0.0, step=0.01, format="%.2f", key="carga_monto",
        )
        tasa_input = st.number_input(
            "Tasa de Cambio Monitor:", min_value=0.0, value=1.0, step=0.01, format="%.2f", key="carga_tasa",
        )

    comentarios_input = st.text_area(
        "Comentarios adicionales (Opcional):", key="carga_comentarios"
    )

    st.divider()

    # --- VALIDACIÓN VISUAL PREVIA ---
    df_actual = st.session_state.get("df_movimientos", pd.DataFrame())
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
            # Validaciones previas de formulario (Locales)
            errores_validacion = []
            if not categoria_input.strip():
                errores_validacion.append("La **Categoría** es obligatoria.")
            if not detalle_input.strip():
                errores_validacion.append("La **Descripción / Detalle** es obligatoria.")
            if monto_input <= 0:
                errores_validacion.append("El **Monto** debe ser mayor a 0,00.")
            if "Bs" in tipo_input and tasa_input <= 0:
                errores_validacion.append("La **Tasa Monitor** debe ser mayor a 0.")

            if errores_validacion:
                for err in errores_validacion:
                    st.warning(f"⚠️ {err}")
                st.toast("Verifica los campos obligatorios del formulario.", icon="⚠️")
                return

            # --- CANDADO ESTRICTO Y OPERACIÓN EN BASE DE DATOS ---
            with st.spinner("Validando auditoría en tiempo real y registrando movimiento..."):
                df_fresco = obtener_movimientos_locales()
                meses_cerrados_real = _obtener_meses_cerrados(df_fresco)
                
                if ym_input in meses_cerrados_real:
                    st.error("❌ **BLOQUEO:** El mes seleccionado acaba de ser bloqueado por otro administrador.")
                    st.toast("Mes bloqueado recientemente", icon="🔒")
                    return
                if _es_mes_anterior_al_inicio(df_fresco, ym_input):
                    st.error("❌ **BLOQUEO:** El mes seleccionado es anterior al inicio histórico de operaciones.")
                    st.toast("Mes anterior al inicio histórico", icon="🔒")
                    return

                nuevo_asiento = {
                    "fecha": fecha_input.strftime("%Y-%m-%d"),
                    "categoria": categoria_input.strip().upper(),
                    "detalle": detalle_input.strip(),
                    "tipo": tipo_input,
                    "monto": float(monto_input),
                    "tasa": float(tasa_input) if tasa_input > 0 else 1.0,
                    "comentarios": comentarios_input.strip(),
                    "activo": True,
                    "consolidado": False,
                    "creado_por": str(rol_actual),
                }

                exito, mensaje = insertar_movimiento_db(nuevo_asiento)

                if exito:
                    st.session_state["df_movimientos"] = obtener_movimientos_locales()
                    st.session_state["msg_carga"] = ("success", f"Transacción registrada con éxito: {mensaje}")
                else:
                    st.session_state["msg_carga"] = ("error", f"FALLO EN BASE DE DATOS: {mensaje}")

                time.sleep(0.2)
                st.rerun()