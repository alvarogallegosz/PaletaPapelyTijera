# view_caja_carga.py
import datetime
import pandas as pd
import streamlit as st
from db_connection import insertar_movimiento_db, obtener_movimientos_locales


def _obtener_meses_cerrados(df_datos) -> set:
    """Devuelve un set de strings 'YYYY-MM' que están bloqueados."""
    if df_datos is None or df_datos.empty or "consolidado" not in df_datos.columns:
        return set()
    
    # Creamos una columna temporal YYYY-MM
    df_temp = df_datos.copy()
    df_temp["ym"] = pd.to_datetime(df_temp["fecha"], errors="coerce").dt.strftime("%Y-%m")
    
    # Si AL MENOS UN registro en ese mes es True, el mes entero entra a la lista negra
    meses_bloqueados = df_temp[df_temp["consolidado"] == True]["ym"].unique()
    return set(meses_bloqueados)


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

  # --- VALIDACIÓN VISUAL PREVIA ---
  df_actual = st.session_state.get("df_movimientos", pd.DataFrame())
  meses_cerrados = _obtener_meses_cerrados(df_actual)
  ym_input = pd.to_datetime(fecha_input).strftime("%Y-%m")

  if ym_input in meses_cerrados:
    st.error(
        f"🔒 **CARGA SUSPENDIDA:** El mes ({ym_input}) se encuentra "
        "**CONSOLIDADO y BLOQUEADO**. No se admiten nuevos asientos."
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
          st.error("❌ **BLOQUEO:** El mes seleccionado acaba de ser bloqueado por otro administrador. Operación abortada.")
          return

      # Validaciones de formulario
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

      with st.spinner("Guardando en Supabase..."):
        exito, mensaje = insertar_movimiento_db(nuevo_asiento)

      if exito:
        st.success(f"🎉 {mensaje}")
        # ACTUALIZACIÓN DE MEMORIA CACHÉ OBLIGATORIA
        st.session_state["df_movimientos"] = obtener_movimientos_locales()
        st.rerun()
      else:
        st.error(f"❌ FALLO EN BASE DE DATOS: {mensaje}")