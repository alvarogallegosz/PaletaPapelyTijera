import streamlit as st
import pandas as pd
import datetime

def render_creacion_presupuesto():
    st.title("📝 Creación de Presupuesto")
    st.caption("Diligencie los campos y agregue los ítems requeridos para generar la propuesta.")
    
    # --------------------------------------------------------------------------
    # 1. INICIALIZACIÓN DE SESSION_STATE (Evita errores de variables faltantes)
    # --------------------------------------------------------------------------
    if "meta_presupuesto" not in st.session_state:
        st.session_state["meta_presupuesto"] = {
            "nombre": "",
            "cliente": "",
            "fecha_evento": "",
            "lugar": "",
            "fecha_larga": datetime.date.today().strftime("%d de %B de %Y").upper(),
            "incluir_precios_pdf": True
        }

    if "lista_secciones" not in st.session_state or not st.session_state["lista_secciones"]:
        st.session_state["lista_secciones"] = [
            {"id": "sec_1", "titulo": "1. ESTRUCTURAS Y MONTAJES"}
        ]

    if "clausulas_presupuesto" not in st.session_state:
        st.session_state["clausulas_presupuesto"] = (
            "1. Precios indicados no incluyen IVA salvo especificación contraria.\n"
            "2. Validez de la presente propuesta: 15 días continuos a partir de su emisión.\n"
            "3. La reserva de equipos requiere un anticipo del 50% al momento de la aprobación."
        )

    # --------------------------------------------------------------------------
    # 2. METADATOS / ENCABEZADO DEL PRESUPUESTO
    # --------------------------------------------------------------------------
    st.markdown("### 📋 Datos Generales de la Propuesta")
    
    meta = st.session_state["meta_presupuesto"]
    
    col1, col2 = st.columns(2)
    with col1:
        meta["nombre"] = st.text_input("Nombre de la Propuesta / Evento:", value=meta.get("nombre", ""))
        meta["cliente"] = st.text_input("Cliente / Empresa:", value=meta.get("cliente", ""))
        meta["fecha_evento"] = st.text_input("Fecha del Evento:", value=meta.get("fecha_evento", ""))
    
    with col2:
        meta["lugar"] = st.text_input("Lugar / Recinto:", value=meta.get("lugar", ""))
        meta["fecha_larga"] = st.text_input("Fecha de Emisión (Texto para PDF):", value=meta.get("fecha_larga", ""))
        meta["incluir_precios_pdf"] = st.checkbox("Mostrar precios y totales en el PDF", value=meta.get("incluir_precios_pdf", True))

    st.session_state["meta_presupuesto"] = meta
    st.divider()

    # --------------------------------------------------------------------------
    # 3. TABLAS DINÁMICAS POR SECCIÓN
    # --------------------------------------------------------------------------
    st.markdown("### 🛠️ Detalles por Sección e Ítems")
    
    secciones_a_eliminar = []

    for idx, sec in enumerate(st.session_state["lista_secciones"]):
        sec_id = sec["id"]
        
        # Inicializar DataFrame para la sección si no existe
        if f"df_{sec_id}" not in st.session_state:
            st.session_state[f"df_{sec_id}"] = pd.DataFrame([
                {"descripción": "", "medidas": "", "juegos/kits": 1.0, "cantidad": 1.0, "precio_unitario": 0.0}
            ])

        with st.expander(f"📌 {sec['titulo']}", expanded=True):
            col_tit, col_del = st.columns([5, 1])
            with col_tit:
                nuevo_titulo = st.text_input(
                    f"Título de la Sección #{idx+1}:",
                    value=sec["titulo"],
                    key=f"tit_{sec_id}"
                )
                sec["titulo"] = nuevo_titulo
            
            with col_del:
                st.write("") # Espaciador vertical
                st.write("")
                if len(st.session_state["lista_secciones"]) > 1:
                    if st.button("🗑️ Eliminar", key=f"del_{sec_id}"):
                        secciones_a_eliminar.append(sec)

            # Editor de tabla interactivo
            st.markdown("**Renglones / Ítems:**")
            edited_df = st.data_editor(
                st.session_state[f"df_{sec_id}"],
                num_rows="dynamic",
                column_config={
                    "descripción": st.column_config.TextColumn("Descripción", width="large", required=True),
                    "medidas": st.column_config.TextColumn("Medidas", width="medium"),
                    "juegos/kits": st.column_config.NumberColumn("Juegos / Kits", min_value=0, step=1, format="%d"),
                    "cantidad": st.column_config.NumberColumn("Cantidad", min_value=0, step=1, format="%d"),
                    "precio_unitario": st.column_config.NumberColumn("Precio Unitario ($)", min_value=0.0, format="$%.2f"),
                },
                use_container_width=True,
                key=f"editor_{sec_id}"
            )
            # Guardar cambios del DataEditor en session_state
            st.session_state[f"df_{sec_id}"] = edited_df

    # Eliminar secciones marcadas
    if secciones_a_eliminar:
        for s in secciones_a_eliminar:
            st.session_state["lista_secciones"].remove(s)
            if f"df_{s['id']}" in st.session_state:
                del st.session_state[f"df_{s['id']}"]
        st.rerun()

    # Botón para agregar nueva sección
    if st.button("➕ Agregar Nueva Sección"):
        nuevo_id = f"sec_{len(st.session_state['lista_secciones']) + 1}_{int(pd.Timestamp.now().timestamp())}"
        st.session_state["lista_secciones"].append({
            "id": nuevo_id,
            "titulo": f"{len(st.session_state['lista_secciones']) + 1}. NUEVA SECCIÓN"
        })
        st.rerun()

    st.divider()

    # --------------------------------------------------------------------------
    # 4. CLÁUSULAS Y CONDICIONES
    # --------------------------------------------------------------------------
    st.markdown("### 📜 Cláusulas y Condiciones Commerciales")
    st.session_state["clausulas_presupuesto"] = st.text_area(
        "Edite las cláusulas que aparecerán al final del presupuesto:",
        value=st.session_state["clausulas_presupuesto"],
        height=120
    )

    st.divider()

    # --------------------------------------------------------------------------
    # 5. ACCIONES (VISTA PREVIA Y GUARDADO)
    # --------------------------------------------------------------------------
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("👁️ Generar Vista Previa del Documento", use_container_width=True, type="primary"):
            st.session_state["mostrar_vista_previa"] = True
            st.success("¡Vista previa actualizada correctamente!")

    with col_btn2:
        if st.button("💾 Guardar Presupuesto en BD", use_container_width=True):
            st.info("Conectando con Supabase para persistir los datos...")