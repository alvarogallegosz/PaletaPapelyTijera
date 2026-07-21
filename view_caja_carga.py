# view_caja_carga.py
import datetime
import pandas as pd
import streamlit as st
from db_connection import insertar_movimiento_db, obtener_movimientos_locales


def render_carga(rol_actual, es_consolidado=False):
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
            "IN-Bs",
            "EG-Bs",
            "IN-$Ze",
            "EG-$Ze",
            "IN-$Ch",
            "EG-$Ch",
            "IN-$AhZe",
            "EG-$AhZe",
            "IN-$AhCh",
            "EG-$AhCh",
        ],
        key="carga_tipo",
    )
    monto_input = st.number_input(
        "Monto (*):",
        min_value=0.0,
        step=0.01,
        format="%.2f",
        key="carga_monto",
    )
    tasa_input = st.number_input(
        "Tasa de Cambio Monitor:",
        min_value=0.0,
        value=1.0,
        step=0.01,
        format="%.2f",
        key="carga_tasa",
    )

  comentarios_input = st.text_area(
      "Comentarios adicionales (Opcional):", key="carga_comentarios"
  )

  st.divider()

  btn_registrar = st.button(
      "💾 Registrar Transacción en Base de Datos",
      type="primary",
      use_container_width=True,
  )

  if btn_registrar:
    # 1. VALIDACIONES
    errores_validacion = []

    if not categoria_input.strip():
      errores_validacion.append("La **Categoría** es obligatoria.")

    if not detalle_input.strip():
      errores_validacion.append("La **Descripción / Detalle** es obligatoria.")

    if monto_input <= 0:
      errores_validacion.append("El **Monto** debe ser mayor a 0,00.")

    if "Bs" in tipo_input and tasa_input <= 0:
      errores_validacion.append(
          "La **Tasa Monitor** debe ser mayor a 0 para cuentas en Bolívares."
      )

    if errores_validacion:
      for err in errores_validacion:
        st.warning(f"⚠️ {err}")
      st.error(
          "❌ La transacción NO fue enviada a la base de datos debido a datos"
          " faltantes o erróneos."
      )
      return

    # 2. DICCIONARIO
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

    # 3. ENVÍO A BASE DE DATOS
    with st.spinner("Guardando en Supabase..."):
      exito, mensaje = insertar_movimiento_db(nuevo_asiento)

    if exito:
      st.balloons()
      st.success(f"🎉 {mensaje}")
      obtener_movimientos_locales()
    else:
      st.error(f"❌ FALLO EN BASE DE DATOS: {mensaje}")