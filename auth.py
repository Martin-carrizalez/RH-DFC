import streamlit as st
import bcrypt
from config import get_sheets_manager

def check_authentication():
    """Verifica si el usuario está autenticado"""
    return st.session_state.get('authenticated', False)

def get_user_info():
    """Retorna información del usuario actual"""
    return st.session_state.get('user_data', {})

def login():
    """Pantalla de login contra Supabase"""
    st.title("🔐 Sistema de Recursos Humanos")
    st.subheader("Iniciar Sesión")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            email = st.text_input("📧 Email", placeholder="usuario@empresa.com")
            password = st.text_input("🔑 Contraseña", type="password")
            submit = st.form_submit_button("Ingresar", use_container_width=True, type="primary")
            
            if submit:
                if validate_user(email, password):
                    st.success("✅ Acceso concedido")
                    st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas")

def validate_user(email, password):
    """Validar usuario contra Supabase con bcrypt"""
    try:
        manager = get_sheets_manager()
        df_users = manager.get_dataframe("usuarios")
        
        # Buscar usuario por email (case insensitive)
        user = df_users[df_users['email'].str.lower() == email.lower()]
        
        if not user.empty:
            user_data = user.iloc[0]
            
            # Verificar que el usuario esté activo
            if user_data['activo'].upper() != 'SI':
                st.warning("⚠️ Usuario inactivo. Contacte al administrador.")
                return False
            
            # Verificar contraseña con bcrypt
            password_hash = user_data['password_hash']
            
            if bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
                # Login exitoso - guardar en session_state
                st.session_state.authenticated = True
                st.session_state.user_data = {
                    'email': user_data['email'],
                    'nombre': user_data['nombre'],
                    'rol': user_data['rol'],
                    'oficina': user_data['oficina_asignada']
                }
                
                # Registrar login en auditoría
                manager.log_action(
                    usuario=user_data['email'],
                    accion="login",
                    modulo="autenticacion",
                    detalles=f"Login exitoso - Rol: {user_data['rol']}, Oficina: {user_data['oficina_asignada']}"
                )
                
                return True
            else:
                # Contraseña incorrecta
                manager.log_action(
                    usuario=email,
                    accion="login_failed",
                    modulo="autenticacion",
                    detalles="Intento fallido - Contraseña incorrecta"
                )
                return False
        else:
            # Usuario no encontrado
            manager.log_action(
                usuario=email,
                accion="login_failed",
                modulo="autenticacion",
                detalles="Intento fallido - Usuario no existe"
            )
            return False
        
    except Exception as e:
        st.error(f"❌ Error de autenticación: {e}")
        return False

def logout():
    """Cerrar sesión del usuario"""
    if st.session_state.get('authenticated'):
        try:
            manager = get_sheets_manager()
            manager.log_action(
                usuario=st.session_state.user_data['email'],
                accion="logout",
                modulo="autenticacion",
                detalles="Cierre de sesión"
            )
        except:
            pass  # Si falla el log no bloqueamos el logout
    
    st.session_state.authenticated = False
    st.session_state.user_data = None
    st.rerun()