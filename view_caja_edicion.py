# view_caja_edicion.py
import datetime
import pandas as pd
import streamlit as st
import calendar

from db_connection import actualizar_movimiento_db, obtener_movimientos_locales
# 📦 IMPORTACIÓN DE FUNCIONES DE SALDOS REUTILIZABLES DEL VISOR
from view_caja_visor import render_banner_saldos, render_banner_acumulados, calcular_acumulados_filtrados


def _obtener_meses_cerrados(df_datos) -> set:
    if df_datos is None or df_datos.empty or "consolidado" not in df_datos.columns:
        return set()
    df_temp = df_datos.copy()
    df_temp["ym"] = pd.to_datetime(df_temp["fecha"], errors="coerce").dt.strftime("%Y-%m")
    meses_bloqueados = df_temp[df_temp["consolidado"] == True]["ym"].unique()
    return set(meses_bloqueados)


def render_edicion(df_completo, rol_actual, es_consolidado=False):
    # ↔️ CSS INYECTADO PARA FORZAR SCROLLBAR HORIZONTAL EN EL DATA_EDITOR
    st.markdown("""
        <style>
            div[data-testid="stDataFrame"] > div,
            div[data-testid="stDataEditor"] > div {
                overflow-x: auto !important;
            }
        </style>
    """, unsafe_allow_html=True)

    # --- SISTEMA DE NOTIFICACIONES POST-RECARGA ---
    if "msg_edicion" in st.session_state:
        tipo, texto = st.session_state["msg_edicion"]
        if tipo == "success":
            st.success(texto)
        elif tipo == "error":
            st.error(texto)
        del st.session_state["msg_edicion"]

    st.markdown("### 🛠️ Modificaciones Generales de Auditoría")

    if df_completo.empty:
        st.info("No hay registros editables en la base de datos.")
        return

    df = df_completo.copy()
    df["fecha_dt"] = pd.to_datetime(df["fecha"])
    ym_minimo_global = df["fecha_dt"].min().strftime("%Y-%m")
    
    if "activo" not in df.columns:
        df["activo"] = True

    # --- EVALUACIÓN STRICTA DE PERMISOS DE ROL ---
    rol_clean = str(rol_actual or st.session_state.get("rol_actual", "")).strip().lower()
    es_soporte = (rol_clean == "soporte")
    
    col_anio, col_mes, col_buscar, col_ver_inactivos = st.columns([1, 1, 2, 1.2])

    with col_ver_inactivos:
        st.markdown("<br>", unsafe_allow_html=True) # Espaciador visual
        # Solo el usuario soporte puede ver/marcar inactivos
        if es_soporte:
            ver_inactivos = st.checkbox("🔍 Ver inactivos (Soporte)", value=False, help="Muestra los registros anulados para revisión técnica.")
        else:
            ver_inactivos = False

    if not ver_inactivos:
        df = df[df["activo"] == True]

    if df.empty:
        st.warning("No hay registros activos disponibles para editar.")
        return

    # --- FECHAS PREDETERMINADAS: MES Y AÑO ACTUAL ---
    hoy = datetime.date.today()
    anio_actual = hoy.year
    mes_actual_num = hoy.month

    anios = sorted(df["fecha_dt"].dt.year.unique(), reverse=True)
    idx_anio = anios.index(anio_actual) if anio_actual in anios else 0

    with col_anio:
        anio_sel = st.selectbox("Año a editar:", options=anios, index=idx_anio)

    meses_nombres = [
        "Todo el año", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
    ]
    
    with col_mes:
        # Por defecto selecciona el número de mes actual (Índice 1 = Enero, 2 = Febrero, etc.)
        idx_mes_defecto = mes_actual_num if mes_actual_num < len(meses_nombres) else 0
        mes_sel = st.selectbox("Mes:", options=meses_nombres, index=idx_mes_defecto)

    with col_buscar:
        busqueda = st.text_input(
            "🔍 Buscador rápido:", placeholder="Ej: 147, Zelle, Imprenta..."
        )

    # --- FILTRADO DE DATOS ---
    df_filtrado = df[df["fecha_dt"].dt.year == anio_sel].copy()

    num_mes_sel = None
    if mes_sel != "Todo el año":
        num_mes_sel = meses_nombres.index(mes_sel)
        df_filtrado = df_filtrado[df_filtrado["fecha_dt"].dt.month == num_mes_sel]

    if busqueda:
        b_lower = busqueda.strip().lower()
        df_filtrado = df_filtrado[
            df_filtrado["id"].astype(str).str.contains(b_lower)
            | df_filtrado["detalle"].astype(str).str.lower().str.contains(b_lower)
            | df_filtrado["categoria"].astype(str).str.lower().str.contains(b_lower)
        ]

    # --- SALDOS DINÁMICOS SITUADOS JUSTO DEBAJO DE LOS FILTROS ---
    if not df_filtrado.empty:
        max_fecha_dt = df_filtrado["fecha_dt"].max()
        df_hasta_max = df[df["fecha_dt"] <= max_fecha_dt]
        fecha_hasta_str = max_fecha_dt.strftime("%d/%m/%Y")
    else:
        df_hasta_max = pd.DataFrame()
        fecha_hasta_str = ""

    # 1. Saldo acumulado hasta la fecha máxima seleccionada
    saldos_hasta_max = calcular_acumulados_filtrados(df_hasta_max)
    render_banner_saldos(saldos_hasta_max, fecha_hasta_str=fecha_hasta_str)
    
    # 2. Balance específico del período filtrado (Sin acumulado anterior)
    render_banner_acumulados(df_filtrado)

    if df_filtrado.empty:
        st.warning("No se encontraron registros con los filtros seleccionados.")
        return

    # --- BLOQUEO VISUAL MASIVO ---
    meses_cerrados_locales = _obtener_meses_cerrados(df)
    bloqueo_total_vista = False

    if mes_sel != "Todo el año":
        ym_seleccionado = f"{anio_sel}-{num_mes_sel:02d}"
        if ym_seleccionado in meses_cerrados_locales:
            bloqueo_total_vista = True
        elif ym_seleccionado < ym_minimo_global:
            bloqueo_total_vista = True

    # Definición dinámica de columnas visibles según rol (Oculta 'activo' en Admin / Gerente)
    if es_soporte:
        columnas_orden = ["id", "activo", "fecha", "categoria", "detalle", "tipo", "monto", "tasa", "comentarios"]
    else:
        columnas_orden = ["id", "fecha", "categoria", "detalle", "tipo", "monto", "tasa", "comentarios"]

    if bloqueo_total_vista:
        st.warning(f"🔒 **EDICIÓN SUSPENDIDA:** El mes de {mes_sel} {anio_sel} se encuentra cerrado / consolidado.")
        st.dataframe(
            df_filtrado[columnas_orden],
            use_container_width=True, hide_index=True, height=500,
        )
        return

    st.caption(
        f"💡 Editando {len(df_filtrado)} registros. Desmarca 'Activo' para dar de baja un asiento (desaparecerá de las vistas operativas)." if es_soporte else f"💡 Editando {len(df_filtrado)} registros."
    )

    df_editado = st.data_editor(
        df_filtrado,
        column_order=columnas_orden,
        column_config={
            "id": st.column_config.NumberColumn("ID", width=60, disabled=True),
            "activo": st.column_config.CheckboxColumn("Activo", width=60, help="Desmarca para anular lógicamente el registro"),
            "fecha": st.column_config.DateColumn("Fecha", width=100, format="DD/MM/YYYY"),
            "categoria": st.column_config.TextColumn("Categoría", width=160),
            "detalle": st.column_config.TextColumn("Descripción", width=340),
            "tipo": st.column_config.SelectboxColumn(
                "Tipo Cuenta", width=120,
                options=["IN-Bs", "EG-Bs", "IN-$Ze", "EG-$Ze", "IN-$Ch", "EG-$Ch", "IN-$AhZe", "EG-$AhZe", "IN-$AhCh", "EG-$AhCh"],
            ),
            "monto": st.column_config.NumberColumn("Monto Base", width=130, min_value=0.0, format="%.2f"),
            "tasa": st.column_config.NumberColumn("Tasa Monitor", width=110, min_value=0.0, format="%.2f"),
            "comentarios": st.column_config.TextColumn("Comentario", width=340),
        },
        disabled=False, hide_index=True, use_container_width=True, height=500, key="editor_excel_caja",
    )

    if st.button("💾 Aplicar Cambios Consolidados en Base de Datos"):
        with st.spinner("Comparando cambios y validando bloqueos..."):
            df_fresco = obtener_movimientos_locales()
            meses_cerrados_real = _obtener_meses_cerrados(df_fresco)

            df_fil_comp = df_filtrado.set_index("id")
            df_edi_comp = df_editado.set_index("id")
            
            ids_modificados = []
            errores_bloqueo = []

            for id_reg in df_edi_comp.index:
                row_f = df_fil_comp.loc[id_reg]
                row_e = df_edi_comp.loc[id_reg]
                
                cambio = False
                
                activo_f = bool(row_f["activo"]) if pd.notnull(row_f["activo"]) else True
                activo_e = bool(row_e["activo"]) if "activo" in row_e and pd.notnull(row_e["activo"]) else activo_f
                if activo_f != activo_e: cambio = True
                
                if pd.to_datetime(row_f["fecha"]) != pd.to_datetime(row_e["fecha"]): cambio = True
                if str(row_f["categoria"]).strip().upper() != str(row_e["categoria"]).strip().upper(): cambio = True
                if str(row_f["detalle"]).strip() != str(row_e["detalle"]).strip(): cambio = True
                if str(row_f["tipo"]) != str(row_e["tipo"]): cambio = True
                if float(row_f["monto"]) != float(row_e["monto"]): cambio = True
                
                tasa_f = float(row_f["tasa"]) if pd.notnull(row_f["tasa"]) else 1.0
                tasa_e = float(row_e["tasa"]) if pd.notnull(row_e["tasa"]) else 1.0
                if tasa_f != tasa_e: cambio = True
                
                com_f = str(row_f["comentarios"]).strip() if pd.notnull(row_f["comentarios"]) and str(row_f["comentarios"]).lower() not in ['nan', 'none'] else ""
                com_e = str(row_e["comentarios"]).strip() if pd.notnull(row_e["comentarios"]) and str(row_e["comentarios"]).lower() not in ['nan', 'none'] else ""
                if com_f != com_e: cambio = True
                
                if cambio:
                    ym_original = pd.to_datetime(row_f["fecha"]).strftime("%Y-%m")
                    ym_nuevo = pd.to_datetime(row_e["fecha"]).strftime("%Y-%m")
                    
                    if ym_original in meses_cerrados_real:
                        errores_bloqueo.append(f"El ID {id_reg} pertenece a un mes cerrado ({ym_original}). No puede ser alterado ni anulado.")
                    elif ym_nuevo in meses_cerrados_real:
                        errores_bloqueo.append(f"No puedes mover el ID {id_reg} a un mes cerrado ({ym_nuevo}).")
                    elif ym_nuevo < ym_minimo_global:
                        errores_bloqueo.append(f"No puedes asignar el ID {id_reg} a un mes anterior al inicio histórico ({ym_nuevo}).")
                    else:
                        ids_modificados.append(id_reg)

            if errores_bloqueo:
                for err in list(set(errores_bloqueo)):
                    st.error(f"❌ {err}")
                st.error("Operación abortada por seguridad.")
                return

            if not ids_modificados:
                st.info("No se detectaron cambios en los datos que requieran guardarse.")
                return

            for id_reg in ids_modificados:
                row_e = df_edi_comp.loc[id_reg]
                fecha_str = row_e["fecha"].strftime("%Y-%m-%d") if hasattr(row_e["fecha"], "strftime") else str(row_e["fecha"])
                
                val_activo = bool(row_e["activo"]) if "activo" in row_e else True

                cambios = {
                    "activo": val_activo,
                    "fecha": fecha_str,
                    "categoria": str(row_e["categoria"]).strip().upper(),
                    "detalle": str(row_e["detalle"]).strip(),
                    "tipo": row_e["tipo"],
                    "monto": float(row_e["monto"]),
                    "tasa": float(row_e["tasa"]) if pd.notnull(row_e["tasa"]) else 1.0,
                    "comentarios": str(row_e["comentarios"]).strip() if pd.notnull(row_e["comentarios"]) and str(row_e["comentarios"]).lower() not in ['nan', 'none'] else "",
                    "modificado_por": rol_actual,
                }
                actualizar_movimiento_db(int(id_reg), cambios)

            st.session_state["df_movimientos"] = obtener_movimientos_locales()
            st.session_state["msg_edicion"] = ("success", f"🎉 ¡{len(ids_modificados)} registro(s) actualizado(s) correctamente!")
            st.rerun()
