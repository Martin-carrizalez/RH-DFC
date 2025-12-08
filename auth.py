import streamlit as st
from config import get_sheets_manager

def check_authentication():
    """Verifica si el usuario está autenticado"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_data' not in st.session_state:
        st.session_state.user_data = None
    
    return st.session_state.authenticated

def login():
    """Muestra formulario de login y valida credenciales"""
    st.title("🔐 Sistema de Gestión de Personal")
    st.subheader("Inicio de Sesión")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            email = st.text_input("📧 Correo electrónico", placeholder="usuario@empresa.com")
            password = st.text_input("🔑 Contraseña", type="password")
            submit = st.form_submit_button("Ingresar", use_container_width=True)
            
            if submit:
                if validate_user(email, password):
                    st.success("✅ Acceso concedido")
                    st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas")

def validate_user(email, password):
    """Valida credenciales contra la hoja 'usuarios'"""
    try:
        sheets = get_sheets_manager()
        df_users = sheets.get_dataframe("usuarios")
        
        # Filtrar usuario por email
        user = df_users[df_users['email'].str.lower() == email.lower()]
        
        if not user.empty:
            user_data = user.iloc[0]
            
            # Verificar que esté activo
            if user_data['activo'].upper() != 'SI':
                st.warning("⚠️ Usuario inactivo. Contacte al administrador.")
                return False
            
            # En producción, aquí validarías password hasheado
            # Por ahora, password simple (¡CAMBIAR EN PRODUCCIÓN!)
            if password == "temporal123":  # TEMPORAL - CAMBIAR
                # Guardar datos del usuario en session_state
                st.session_state.authenticated = True
                st.session_state.user_data = {
                    'email': user_data['email'],
                    'nombre': user_data['nombre'],
                    'rol': user_data['rol'],
                    'oficina': user_data['oficina_asignada']
                }
                
                # Registrar login en auditoría
                sheets.log_action(
                    usuario=user_data['email'],
                    accion="login",
                    modulo="autenticacion",
                    detalles=f"Inicio de sesión exitoso - Rol: {user_data['rol']}"
                )
                
                return True
        
        return False
        
    except Exception as e:
        st.error(f"❌ Error al validar usuario: {e}")
        return False

def logout():
    """Cierra la sesión del usuario"""
    if st.session_state.authenticated:
        sheets = get_sheets_manager()
        sheets.log_action(
            usuario=st.session_state.user_data['email'],
            accion="logout",
            modulo="autenticacion",
            detalles="Cierre de sesión"
        )
    
    st.session_state.authenticated = False
    st.session_state.user_data = None
    st.rerun()

def require_role(allowed_roles):
    """Decorator para restringir acceso por rol"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not check_authentication():
                st.warning("⚠️ Debe iniciar sesión")
                return None
            
            user_role = st.session_state.user_data['rol']
            if user_role not in allowed_roles:
                st.error(f"❌ Acceso denegado. Se requiere rol: {', '.join(allowed_roles)}")
                return None
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def get_user_info():
    """Retorna información del usuario actual"""
    if check_authentication():
        return st.session_state.user_data
    return None