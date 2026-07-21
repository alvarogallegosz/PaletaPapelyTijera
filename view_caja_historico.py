import pandas as pd
import streamlit as st
import time
from core_finance_engine import procesar_mes_aislado
from db_connection import (
    actualizar_consolidado_mes_db,
    obtener_movimientos_locales,
)
from view_caja_visor import preparar_columnas_monto


def render_historico(df_todos, rol_actual):
    # --- FILA SUPERIOR PARALELA MÁXIMA ---
    c_title, c_ano, c_mes, c_date, c_cat, c_tipo = st.columns(
        [1.4, 0.7, 0.9, 1.2, 1.2, 1.2]
    )

    with c_title:
        st.markdown("### 📚 Histórico\n*Reportes*")

    with c_ano:
        anho_rep = st.selectbox("Año", [2026, 2025], key="h_anho")

    with c_mes:
        meses = {
            1: "Enero",
            2: "Febrero",
            3: "Marzo",
            4: "Abril",
            5: "Mayo",
            6: "Junio",
            7: "Julio",
            8: "Agosto",
            9: "Septiembre",
            10: "Octubre",
            11: "Noviembre",
            12: "Diciembre",
        }
        mes_rep_nom = st.selectbox("Mes", list(meses.values()), key="h_mes")
        mes_rep_num = [k for k, v in meses.items() if v == mes_rep_nom][0]

    df_mes, _, saldos_fin = procesar_mes_aislado(df_todos, anho_rep, mes_rep_num)
    df_filtrado = df_mes.copy()

    with c_date:
        df_filtrado["fecha_date"] = pd.to_datetime(df_filtrado["fecha"]).dt.date
        min_f = (
            df_filtrado["fecha_date"].min()
            if not df_filtrado.empty
            else pd.Timestamp.now().date()
        )
        max_f = (
            df_filtrado["fecha_date"].max()
            if not df_filtrado.empty
            else pd.Timestamp.now().date()
        )
        rango_fecha = st.date_input(
            "Rango Diario",
            value=(min_f, max_f),
            min_value=min_f,
            max_value=max_f,
            key="h_date",
        )

    with c_cat:
        cats_opts = (
            sorted(df_filtrado["categoria"].unique()) if not df_filtrado.empty else []
        )
        cats_sel = st.multiselect("Categoría", options=cats_opts, key="h_cat")

    with c_tipo:
        tipos_opts = (
            sorted(df_filtrado["tipo"].unique()) if not df_filtrado.empty else []
        )
        tipos_sel = st.multiselect("Tipo Cuenta", options=tipos_opts, key="h_tipo")

    if isinstance(rango_fecha, tuple) and len(rango_fecha) == 2:
        df_filtrado = df_filtrado[
            (df_filtrado["fecha_date"] >= rango_fecha[0])
            & (df_filtrado["fecha_date"] <= rango_fecha[1])
        ]
    elif isinstance(rango_fecha, tuple) and len(rango_fecha) == 1:
        df_filtrado = df_filtrado[df_filtrado["fecha_date"] == rango_fecha[0]]

    if cats_sel:
        df_filtrado = df_filtrado[df_filtrado["categoria"].isin(cats_sel)]
    if tipos_sel:
        df_filtrado = df_filtrado[df_filtrado["tipo"].isin(tipos_sel)]

    df_global = st.session_state["df_movimientos"].copy()
    df_global["fecha_dt"] = pd.to_datetime(df_global["fecha"], errors="coerce")
    mascara_mes = (df_global["fecha_dt"].dt.year == anho_rep) & (
        df_global["fecha_dt"].dt.month == mes_rep_num
    )

    estado_consolidado = False
    if not df_global[mascara_mes].empty:
        # Conversión explícita a booleano puro de Python
        estado_consolidado = bool(df_global[mascara_mes]["consolidado"].all())

    if estado_consolidado:
        st.success("🔒 **ESTADO PERÍODO: CONSOLIDADO / COMPLETO**")
    else:
        st.warning("🔓 **ESTADO PERÍODO: ABIERTO / EN AUDITORÍA**")

    # --- SALDOS DE LAS 5 CUENTAS ---
    val_bs = float(saldos_fin.get("Bs", 0.0))
    val_ze = float(saldos_fin.get("Ze", 0.0))
    val_ch = float(saldos_fin.get("Ch", 0.0))
    val_ah_ze = float(saldos_fin.get("AhZe", 0.0))
    val_ah_ch = float(saldos_fin.get("AhCh", 0.0))

    st.markdown(
        f"""
        <div style="font-size: 14px; background-color: #f8f9fa; padding: 10px 14px; border-radius: 6px; border-left: 4px solid #10b981; margin-top: 5px; margin-bottom: 12px; line-height: 1.8;">
            <strong>Cierre de Saldos Disponibles:</strong> <br>
            <span style="color: #111827;">🟢 <b>Bs:</b> {val_bs:,.2f}</span> &nbsp;|&nbsp;
            <span style="color: #111827;">🔵 <b>Zelle Op:</b> ${val_ze:,.2f}</span> &nbsp;|&nbsp;
            <span style="color: #111827;">💵 <b>Cash Op:</b> ${val_ch:,.2f}</span> &nbsp;|&nbsp;
            <span style="color: #0d9488;">🏦 <b>Ahorro Zelle:</b> ${val_ah_ze:,.2f}</span> &nbsp;|&nbsp;
            <span style="color: #0d9488;">🐷 <b>Ahorro Cash:</b> ${val_ah_ch:,.2f}</span>
        </div>
    """,
        unsafe_allow_html=True,
    )

    if df_filtrado.empty:
        st.info("Ningún registro histórico coincide con los filtros aplicados.")
    else:
        df_hist_visual = df_filtrado.copy()
        df_hist_visual = preparar_columnas_monto(df_hist_visual)
        df_hist_visual["Fecha Ext"] = pd.to_datetime(
            df_hist_visual["fecha"]
        ).dt.strftime("%d/%m/%Y")
        df_hist_visual = df_hist_visual.rename(
            columns={
                "detalle": "Descripción",
                "categoria": "Categoría",
                "tipo": "Tipo",
                "comentarios": "Comentario",
            }
        )

        st.dataframe(
            df_hist_visual[[
                "Fecha Ext",
                "Descripción",
                "Categoría",
                "Tipo",
                "Monto Bs",
                "Monto $ Zelle",
                "Monto $ Cash",
                "Monto $ Ah-Ze",
                "Monto $ Ah-Ch",
                "Comentario",
            ]],
            column_config={
                "Fecha Ext": st.column_config.TextColumn("Fecha", width=100),
                "Descripción": st.column_config.TextColumn(
                    "Descripción", width=300
                ),
                "Categoría": st.column_config.TextColumn("Categoría", width=140),
                "Tipo": st.column_config.TextColumn("Tipo", width=90),
                "Monto Bs": st.column_config.TextColumn("Monto Bs", width=110),
                "Monto $ Zelle": st.column_config.TextColumn(
                    "Monto $ Zelle", width=110
                ),
                "Monto $ Cash": st.column_config.TextColumn(
                    "Monto $ Cash", width=110
                ),
                "Monto $ Ah-Ze": st.column_config.TextColumn(
                    "Monto $ Ah-Ze", width=110
                ),
                "Monto $ Ah-Ch": st.column_config.TextColumn(
                    "Monto $ Ah-Ch", width=110
                ),
                "Comentario": st.column_config.TextColumn("Comentario", width=300),
            },
            use_container_width=False,
            hide_index=True,
            height=600,
        )

    # --- LÓGICA DE CIERRE/APERTURA CON PROTECCIÓN Y RETROALIMENTACIÓN COMPLETA ---
    rol_limpio = str(rol_actual).strip().lower()
    if rol_limpio in ["administrador", "gerente"]:
        st.markdown("---")
        
        # Manejo de la notificación de estado persistente entre recargas de pantalla
        if "msg_accion_historico" in st.session_state:
            tipo_msg, texto_msg = st.session_state.pop("msg_accion_historico")
            if tipo_msg == "success":
                st.success(texto_msg)
            else:
                st.error(texto_msg)

        # Conversión a enteros puros de Python
        indices_mes = (
            [int(x) for x in df_global[mascara_mes]["id"].tolist()]
            if not df_global[mascara_mes].empty
            else []
        )

        if indices_mes:
            if estado_consolidado:
                btn_label = "🔓 Reabrir Auditoría de este Mes"
                nuevo_estado = False
            else:
                btn_label = "✅ Consolidar y Bloquear Mes Seleccionado"
                nuevo_estado = True

            # --- BOTÓN DE CAMBIO DE ESTADO ---
            if st.button(btn_label, key="btn_toggle_estado", use_container_width=True):
                with st.spinner("Actualizando estado de auditoría en la base de datos..."):
                    exito, mensaje_bd = actualizar_consolidado_mes_db(
                        anho=anho_rep,
                        mes=mes_rep_num,
                        estado=nuevo_estado
                    )
                    
                    if exito:
                        # Actualización optimista en session_state local
                        if "df_movimientos" in st.session_state:
                            df_local = st.session_state["df_movimientos"]
                            df_local.loc[df_local["id"].isin(indices_mes), "consolidado"] = nuevo_estado
                            st.session_state["df_movimientos"] = df_local
                        
                        # Sincronización real
                        obtener_movimientos_locales()
                        
                        estado_texto = "CERRADO DEFINITIVAMENTE" if nuevo_estado else "ABIERTO"
                        st.session_state["msg_accion_historico"] = (
                            "success",
                            f"✅ El período {mes_rep_nom} {anho_rep} ahora se encuentra {estado_texto}."
                        )
                        st.toast(f"Estado de {mes_rep_nom} {anho_rep} actualizado.", icon="🔒" if nuevo_estado else "🔓")
                    else:
                        st.session_state["msg_accion_historico"] = (
                            "error",
                            f"❌ No se pudo actualizar la base de datos: {mensaje_bd}"
                        )
                        st.toast("Error al actualizar la base de datos", icon="⚠️")
                
                time.sleep(0.2)
                st.rerun()
        else:
            st.info(
                f"No hay registros en el período {mes_rep_nom} {anho_rep} para"
                " aplicar acciones de cierre o apertura."
            )