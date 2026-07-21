# view_auth.py
import base64
import hashlib
import os
import random
import string
import time
import streamlit as st
from core_auth import (
    ROLES_PERMITIDOS,
    calcular_hash_256,
    enviar_correo_simulado,
    generar_codigo_temporal,
)
from db_connection import supabase


def _render_logo_corporativo():
    """Carga y renderiza el logotipo corporativo desde la raíz o directorio del script."""
    logo_nombre = "encabezado_paleta.png"
    ruta_script = os.path.join(os.path.dirname(__file__), logo_nombre)
    ruta_raiz = os.path.join(os.getcwd(), logo_nombre)
    ruta_final = (
        ruta_script
        if os.path.exists(ruta_script)
        else (ruta_raiz if os.path.exists(ruta_raiz) else None)
    )

    if ruta_final:
        with open(ruta_final, "rb") as f:
            data_img = base64.b64encode(f.read()).decode("utf-8")
        st.markdown(
            f"""
            <div style="text-align: center; margin-bottom: 20px;">
                <img src="data:image/png;base64,{data_img}" style="width: 75%; height: auto; display: block; margin: 0 auto;">
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_modulo_autenticacion():
    # Inicializar estados de la pantalla si no existen
    if "auth_vista" not in st.session_state:
        st.session_state["auth_vista"] = "login"  # Opciones: login, registro, recuperar, verificar, establecer_nueva
    if "auth_email_pendiente" not in st.session_state:
        st.session_state["auth_email_pendiente"] = ""
        st.session_state["auth_codigo_esperado"] = ""
        st.session_state["auth_datos_registro"] = {}

    # --- PANTALLA 1: LOGIN ---
    if st.session_state["auth_vista"] == "login":
        _render_logo_corporativo()
        st.markdown(
            "<h2 style='text-align: center;'>🔐 Acceso al Sistema</h2>",
            unsafe_allow_html=True,
        )
        st.markdown("---")

        # Notificaciones emergentes tras redirecciones
        if "msg_login" in st.session_state:
            tipo, texto = st.session_state.pop("msg_login")
            if tipo == "success":
                st.success(texto)
                st.toast(texto, icon="🎉")
            elif tipo == "error":
                st.error(texto)
                st.toast(texto, icon="⚠️")

        usuario_input = st.text_input(
            "Usuario / Alias", autocomplete="username"
        ).strip().lower()
        pass_input = st.text_input(
            "Contraseña", type="password", autocomplete="current-password"
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Ingresar", use_container_width=True, type="primary"):
                if usuario_input and pass_input:
                    with st.spinner("Verificando credenciales en la base de datos..."):
                        hash_login = calcular_hash_256(pass_input)
                        try:
                            res = (
                                supabase.table("usuarios")
                                .select("*")
                                .eq("usuario", usuario_input)
                                .execute()
                            )
                            if res.data:
                                user_db = res.data[0]
                                if not user_db.get("verificado", False):
                                    st.warning(
                                        "⚠️ Tu cuenta está registrada pero aún no ha sido certificada por correo."
                                    )
                                    st.toast("Cuenta pendiente de verificación", icon="⚠️")
                                elif user_db["password_hash"] == hash_login:
                                    st.session_state["usuario_logueado"] = user_db["usuario"]
                                    st.session_state["usuario_rol"] = user_db["rol"]
                                    st.toast(f"¡Bienvenido, {user_db['usuario']}!", icon="🔑")
                                    time.sleep(0.2)
                                    st.rerun()
                                else:
                                    st.error("Contraseña incorrecta.")
                                    st.toast("Contraseña incorrecta", icon="❌")
                            else:
                                st.error("El usuario no existe.")
                                st.toast("Usuario no encontrado", icon="❌")
                        except Exception as e:
                            st.error(f"Error de conexión con la base de datos de usuarios: {e}")
                            st.toast("Error de conexión con el servidor", icon="⚠️")
                else:
                    st.warning("Por favor rellena todos los campos.")
                    st.toast("Campos incompletos", icon="⚠️")

        with col2:
            if st.button("Crear Cuenta", use_container_width=True):
                st.session_state["auth_vista"] = "registro"
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Recuperar acceso vía correo", key="btn_rec", use_container_width=True, type="secondary"):
            st.session_state["auth_vista"] = "recuperar"
            st.rerun()

    # --- PANTALLA 2: REGISTRO AUTOMÁTICO ---
    elif st.session_state["auth_vista"] == "registro":
        st.subheader("📝 Registro Nuevo Usuario")
        nuevo_user = st.text_input("Define tu Usuario (Único)").strip().lower()
        nuevo_email = st.text_input("Correo Electrónico Corporativo").strip()
        nuevo_pass = st.text_input("Contraseña Sensible", type="password")
        nuevo_rol = st.selectbox("Rol Solicitado", ROLES_PERMITIDOS)

        if st.button("Enviar Código de Certificación", type="primary", use_container_width=True):
            if nuevo_user and nuevo_email and nuevo_pass:
                with st.spinner("Procesando registro y despachando código de seguridad..."):
                    codigo = generar_codigo_temporal()
                    st.session_state["auth_codigo_esperado"] = codigo
                    st.session_state["auth_email_pendiente"] = nuevo_email
                    st.session_state["auth_datos_registro"] = {
                        "usuario": nuevo_user,
                        "email": nuevo_email,
                        "password_hash": calcular_hash_256(nuevo_pass),
                        "rol": nuevo_rol,
                        "verificado": False,
                    }

                    enviar_correo_simulado(nuevo_email, "Código de Certificación de Registro", codigo)
                    st.session_state["auth_vista"] = "verificar"
                    st.toast(f"Código enviado a {nuevo_email}", icon="✉️")
                    time.sleep(0.2)
                    st.rerun()
            else:
                st.error("Completa todos los campos obligatorios.")
                st.toast("Campos incompletos", icon="⚠️")

        if st.button("Volver al Login", use_container_width=True):
            st.session_state["auth_vista"] = "login"
            st.rerun()

    # --- PANTALLA 3: CERTIFICACIÓN DE CÓDIGO ---
    elif st.session_state["auth_vista"] == "verificar":
        st.subheader("✉️ Verificación de Correo")
        st.write(
            f"Introduce el código de 6 dígitos enviado a: **{st.session_state['auth_email_pendiente']}**"
        )
        codigo_ingresado = st.text_input("Código de Seguridad", max_chars=6).strip().upper()

        if st.button("Confirmar Registro", type="primary", use_container_width=True):
            if codigo_ingresado == st.session_state["auth_codigo_esperado"]:
                with st.spinner("Certificando cuenta y creando registro en la base de datos..."):
                    datos = st.session_state["auth_datos_registro"]
                    datos["verificado"] = True

                    try:
                        supabase.table("usuarios").insert(datos).execute()
                        st.session_state["msg_login"] = (
                            "success",
                            "¡Cuenta certificada y guardada con éxito! Ya puedes iniciar sesión.",
                        )
                        st.session_state["auth_vista"] = "login"
                        time.sleep(0.2)
                        st.rerun()
                    except Exception as e:
                        st.error(
                            f"Error al guardar usuario (puede que el nombre ya esté tomado): {e}"
                        )
                        st.toast("Error al guardar usuario", icon="❌")
            else:
                st.error("El código no coincide. Intenta de nuevo.")
                st.toast("Código de verificación incorrecto", icon="❌")

        if st.button("Cancelar y Volver", use_container_width=True):
            st.session_state["auth_vista"] = "login"
            st.rerun()

    # --- PANTALLA 4: RECUPERACIÓN DE CONTRASEÑA ---
    elif st.session_state["auth_vista"] == "recuperar":
        st.subheader("🔑 Recuperación de Contraseña")
        email_rec = st.text_input("Ingresa tu correo registrado").strip()

        if st.button("Generar Código Temporal", type="primary", use_container_width=True):
            if email_rec:
                with st.spinner("Buscando cuenta y despachando código de recuperación..."):
                    try:
                        res = (
                            supabase.table("usuarios")
                            .select("*")
                            .eq("email", email_rec)
                            .execute()
                        )
                        if res.data:
                            user_db = res.data[0]
                            codigo_temp = generar_codigo_temporal()

                            supabase.table("usuarios").update(
                                {"codigo_temporal": codigo_temp}
                            ).eq("usuario", user_db["usuario"]).execute()

                            enviar_correo_simulado(
                                email_rec, "Código Temporal de Recuperación", codigo_temp
                            )
                            st.session_state["auth_user_recuperando"] = user_db["usuario"]
                            st.session_state["auth_vista"] = "establecer_nueva"
                            st.toast("Código de recuperación despachado", icon="🔑")
                            time.sleep(0.2)
                            st.rerun()
                        else:
                            st.error("No existe ningún usuario asociado a ese correo.")
                            st.toast("Correo no encontrado", icon="❌")
                    except Exception as e:
                        st.error(f"Error de base de datos: {e}")
                        st.toast("Error de conexión", icon="⚠️")
            else:
                st.warning("Por favor ingresa un correo electrónico.")
                st.toast("Ingresa tu correo", icon="⚠️")

        if st.button("Regresar", use_container_width=True):
            st.session_state["auth_vista"] = "login"
            st.rerun()

    # --- PANTALLA 5: ESTABLECER NUEVA CONTRASEÑA ---
    elif st.session_state["auth_vista"] == "establecer_nueva":
        st.subheader("🔒 Crear Nueva Contraseña")
        cod_validacion = (
            st.text_input("Introduce el Código Temporal recibido").strip().upper()
        )
        pass_nueva = st.text_input("Nueva Contraseña", type="password")

        if st.button("Actualizar Acceso", type="primary", use_container_width=True):
            if cod_validacion and pass_nueva:
                with st.spinner("Validando token y actualizando contraseña..."):
                    try:
                        user_act = st.session_state["auth_user_recuperando"]
                        res = (
                            supabase.table("usuarios")
                            .select("codigo_temporal")
                            .eq("usuario", user_act)
                            .execute()
                        )

                        if res.data and res.data[0]["codigo_temporal"] == cod_validacion:
                            nuevo_hash = calcular_hash_256(pass_nueva)
                            supabase.table("usuarios").update(
                                {"password_hash": nuevo_hash, "codigo_temporal": None}
                            ).eq("usuario", user_act).execute()

                            st.session_state["msg_login"] = (
                                "success",
                                "Contraseña actualizada correctamente. Ya puedes ingresar.",
                            )
                            st.session_state["auth_vista"] = "login"
                            time.sleep(0.2)
                            st.rerun()
                        else:
                            st.error("Código incorrecto o vencido.")
                            st.toast("Código no válido", icon="❌")
                    except Exception as e:
                        st.error(f"Error al restablecer clave: {e}")
                        st.toast("Error de actualización", icon="⚠️")
            else:
                st.warning("Rellena todos los campos.")
                st.toast("Campos incompletos", icon="⚠️")

        if st.button("Cancelar", use_container_width=True):
            st.session_state["auth_vista"] = "login"
            st.rerun()