# view_auth.py
import streamlit as st
from db_connection import supabase # Tu conector existente
from core_auth import calcular_hash_256, generar_codigo_temporal, enviar_correo_simulado, ROLES_PERMITIDOS

def render_modulo_autenticacion():
    # Inicializar estados de la pantalla si no existen
    if "auth_vista" not in st.session_state:
        st.session_state["auth_vista"] = "login" # Opciones: login, registro, recuperar, verificar
    if "auth_email_pendiente" not in st.session_state:
        st.session_state["auth_email_pendiente"] = ""
        st.session_state["auth_codigo_esperado"] = ""
        st.session_state["auth_datos_registro"] = {}

    st.markdown("<h2 style='text-align: center;'>🔐 Acceso al Sistema</h2>", unsafe_allow_html=True)
    st.markdown("---")

    # --- PANTALLA 1: LOGIN ---
    if st.session_state["auth_vista"] == "login":
        usuario_input = st.text_input("Usuario / Alias", autocomplete="username").strip().lower()
        pass_input = st.text_input("Contraseña", type="password", autocomplete="current-password")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Ingresar", use_container_width=True, type="primary"):
                if usuario_input and pass_input:
                    # Consultar en la tabla 'usuarios'
                    hash_login = calcular_hash_256(pass_input)
                    try:
                        res = supabase.table("usuarios").select("*").eq("usuario", usuario_input).execute()
                        if res.data:
                            user_db = res.data[0]
                            if not user_db.get("verificado", False):
                                st.warning("⚠️ Tu cuenta está registrada pero aún no ha sido certificada por correo.")
                            elif user_db["password_hash"] == hash_login:
                                st.session_state["usuario_logueado"] = user_db["usuario"]
                                st.session_state["usuario_rol"] = user_db["rol"] # Campo exacto: 'rol'
                                st.success(f"¡Bienvenido, {user_db['usuario']} ({user_db['rol']})!")
                                st.rerun()
                            else:
                                st.error("Contraseña incorrecta.")
                        else:
                            st.error("El usuario no existe.")
                    except Exception as e:
                        st.error(f"Error de conexión con la base de datos de usuarios: {e}")
                else:
                    st.warning("Por favor rellena todos los campos.")
                    
        with col2:
            if st.button("Crear Cuenta", use_container_width=True):
                st.session_state["auth_vista"] = "registro"
                st.rerun()
                
        st.markdown("<br><p style='text-align: center;'><a href='#' id='recuperar'>¿Olvidaste tu contraseña?</a></p>", unsafe_allow_html=True)
        if st.button("Recuperar acceso vía correo", key="btn_rec"):
            st.session_state["auth_vista"] = "recuperar"
            st.rerun()

    # --- PANTALLA 2: REGISTRO AUTOMÁTICO ---
    elif st.session_state["auth_vista"] == "registro":
        st.subheader("Registro Nuevo Usuario")
        nuevo_user = st.text_input("Define tu Usuario (Único)").strip().lower()
        nuevo_email = st.text_input("Correo Electrónico Corporativo").strip()
        nuevo_pass = st.text_input("Contraseña Sensible", type="password")
        nuevo_rol = st.selectbox("Rol Solicitado", ROLES_PERMITIDOS)
        
        if st.button("Enviar Código de Certificación", type="primary"):
            if nuevo_user and nuevo_email and nuevo_pass:
                # Generar token de verificación
                codigo = generar_codigo_temporal()
                st.session_state["auth_codigo_esperado"] = codigo
                st.session_state["auth_email_pendiente"] = nuevo_email
                st.session_state["auth_datos_registro"] = {
                    "usuario": nuevo_user,
                    "email": nuevo_email,
                    "password_hash": calcular_hash_256(nuevo_pass),
                    "rol": nuevo_rol,
                    "verificado": False
                }
                
                # Despachar código
                enviar_correo_simulado(nuevo_email, "Código de Certificación de Registro", codigo)
                st.session_state["auth_vista"] = "verificar"
                st.info(f"Se ha enviado un código de seguridad a {nuevo_email}. Revisa tu bandeja.")
                st.rerun()
            else:
                st.error("Completa todos los campos obligatorios.")
                
        if st.button("Volver al Login"):
            st.session_state["auth_vista"] = "login"
            st.rerun()

    # --- PANTALLA 3: CERTIFICACIÓN DE CÓDIGO ---
    elif st.session_state["auth_vista"] == "verificar":
        st.subheader("Verificación de Correo")
        st.write(f"Introduce el código de 6 dígitos enviado a: **{st.session_state['auth_email_pendiente']}**")
        codigo_ingresado = st.text_input("Código de Seguridad", max_chars=6).strip().upper()
        
        if st.button("Confirmar Registro"):
            if codigo_ingresado == st.session_state["auth_codigo_esperado"]:
                datos = st.session_state["auth_datos_registro"]
                datos["verificado"] = True # Cuenta certificada de forma segura
                
                try:
                    supabase.table("usuarios").insert(datos).execute()
                    st.success("¡Cuenta certificada y guardada con éxito! Ya puedes iniciar sesión.")
                    st.session_state["auth_vista"] = "login"
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar usuario (puede que el nombre ya esté tomado): {e}")
            else:
                st.error("El código no coincide. Intenta de nuevo.")

    # --- PANTALLA 4: RECUPERACIÓN DE CONTRASEÑA ---
    elif st.session_state["auth_vista"] == "recuperar":
        st.subheader("Recuperación de Contraseña")
        email_rec = st.text_input("Ingresa tu correo registrado").strip()
        
        if st.button("Generar Código Temporal"):
            if email_rec:
                try:
                    res = supabase.table("usuarios").select("*").eq("email", email_rec).execute()
                    if res.data:
                        user_db = res.data[0]
                        codigo_temp = generar_codigo_temporal()
                        
                        # Guardar el código temporal en la base de datos para ese usuario
                        supabase.table("usuarios").update({"codigo_temporal": codigo_temp}).eq("usuario", user_db["usuario"]).execute()
                        
                        enviar_correo_simulado(email_rec, "Código Temporal de Recuperación", codigo_temp)
                        st.session_state["auth_user_recuperando"] = user_db["usuario"]
                        st.session_state["auth_vista"] = "establecer_nueva"
                        st.success("Código enviado. Procede a cambiar tu clave.")
                        st.rerun()
                    else:
                        st.error("No existe ningún usuario asociado a ese correo.")
                except Exception as e:
                    st.error(f"Error de base de datos: {e}")
                    
        if st.button("Regresar"):
            st.session_state["auth_vista"] = "login"
            st.rerun()

    # --- PANTALLA 5: ESTABLECER NUEVA CONTRASEÑA ---
    elif st.session_state["auth_vista"] == "establecer_nueva":
        st.subheader("Crear Nueva Contraseña")
        cod_validacion = st.text_input("Introduce el Código Temporal recibido").strip().upper()
        pass_nueva = st.text_input("Nueva Contraseña", type="password")
        
        if st.button("Actualizar Acceso"):
            if cod_validacion and pass_nueva:
                try:
                    user_act = st.session_state["auth_user_recuperando"]
                    res = supabase.table("usuarios").select("codigo_temporal").eq("usuario", user_act).execute()
                    
                    if res.data and res.data[0]["codigo_temporal"] == cod_validacion:
                        nuevo_hash = calcular_hash_256(pass_nueva)
                        # Limpiamos el código temporal para que no pueda ser reusado
                        supabase.table("usuarios").update({"password_hash": nuevo_hash, "codigo_temporal": None}).eq("usuario", user_act).execute()
                        st.success("Contraseña actualizada correctamente. Ya puedes ingresar.")
                        st.session_state["auth_vista"] = "login"
                        st.rerun()
                    else:
                        st.error("Código incorrecto o vencido.")
                except Exception as e:
                    st.error(f"Error al restablecer clave: {e}")