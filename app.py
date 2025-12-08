import streamlit as st
from auth import check_authentication, login, logout, get_user_info
from modules.asistencias import show_asistencias_module


# Configuración de la página
st.set_page_config(
    page_title="Sistema RH",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .sidebar-info {
        padding: 1rem;
        background-color: #f0f2f6;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

def main():
    """Función principal de la aplicación"""
    
    # Verificar autenticación
    if not check_authentication():
        login()
        return
    
    # Usuario autenticado - mostrar interfaz principal
    user = get_user_info()
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"""
        <div class="sidebar-info">
            <h3>👤 {user['nombre']}</h3>
            <p><strong>Rol:</strong> {user['rol'].title()}</p>
            <p><strong>Oficina:</strong> {user['oficina']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Menú de navegación
        st.subheader("📋 Menú")
        
        # Opciones según rol
        menu_options = {
            "admin": [
                "🏠 Dashboard",
                "📋 Asistencias",
                "📝 Permisos",
                "🏥 Incapacidades",
                "💰 Bonos",
                "👥 Empleados",
                "👤 Usuarios",
                "📊 Reportes",
                "🔍 Auditoría"
            ],
            "supervisora": [
                "🏠 Dashboard",
                "📋 Asistencias",
                "📝 Permisos",
                "🏥 Incapacidades",
                "💰 Bonos",
                "📊 Reportes"
            ],
            "registrador": [
                "📋 Asistencias",
                "📝 Permisos",
                "🏥 Incapacidades"
            ]
        }
        
        opciones = menu_options.get(user['rol'], menu_options['registrador'])
        menu_selection = st.radio(
            "Seleccionar módulo",
            opciones,
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # Botón de logout
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            logout()
    
    # Contenido principal según selección
    if menu_selection == "🏠 Dashboard":
        show_dashboard()
    elif menu_selection == "📋 Asistencias":
        show_asistencias_module()
    elif menu_selection == "📝 Permisos":
        show_permisos_module()
    elif menu_selection == "🏥 Incapacidades":
        show_incapacidades_module()
    elif menu_selection == "💰 Bonos":
        show_bonos_module()
    elif menu_selection == "👥 Empleados":
        show_empleados_module()
    elif menu_selection == "👤 Usuarios":
        show_usuarios_module()
    elif menu_selection == "📊 Reportes":
        show_reportes_module()
    elif menu_selection == "🔍 Auditoría":
        show_auditoria_module()

def show_dashboard():
    """Dashboard principal con métricas generales"""
    st.title("🏠 Dashboard General")
    
    user = get_user_info()
    from config import get_sheets_manager
    sheets = get_sheets_manager()
    
    # Métricas generales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        df_empleados = sheets.get_dataframe("empleados")
        total_empleados = 0
        if not df_empleados.empty and 'activo' in df_empleados.columns:
            total_empleados = len(df_empleados[df_empleados['activo'] == 'SI'])
        st.metric("👥 Empleados Activos", total_empleados)
    
    with col2:
        df_asistencias = sheets.get_dataframe("asistencias")
        import pandas as pd
        from datetime import date
        hoy = date.today().strftime("%Y-%m-%d")
        
        asistencias_hoy = 0
        if not df_asistencias.empty and 'fecha' in df_asistencias.columns:
            asistencias_hoy = len(df_asistencias[df_asistencias['fecha'] == hoy])
        
        st.metric("📋 Asistencias Hoy", asistencias_hoy)
    
    with col3:
        df_permisos = sheets.get_dataframe("permisos")
        permisos_pendientes = 0
        if not df_permisos.empty and 'estado' in df_permisos.columns:
            permisos_pendientes = len(df_permisos[df_permisos['estado'] == 'Pendiente'])
        st.metric("📝 Permisos Pendientes", permisos_pendientes)
    
    with col4:
        oficinas = get_oficinas_list(sheets)
        st.metric("🏢 Oficinas", len(oficinas))
    
    st.markdown("---")
    
    # Información rápida
    st.subheader("📊 Resumen del Sistema")
    
    tab1, tab2, tab3 = st.tabs(["Últimas Asistencias", "Permisos Recientes", "Alertas"])
    
    with tab1:
        if not df_asistencias.empty and 'timestamp_sistema' in df_asistencias.columns:
            cols_mostrar = [col for col in ['fecha', 'id_empleado', 'estado', 'oficina'] if col in df_asistencias.columns]
            if cols_mostrar:
                df_ultimas = df_asistencias.tail(10).sort_values('timestamp_sistema', ascending=False)
                st.dataframe(df_ultimas[cols_mostrar], use_container_width=True)
        else:
            st.info("No hay asistencias registradas")
    
    with tab2:
        if not df_permisos.empty and 'fecha_solicitud' in df_permisos.columns:
            cols_mostrar = [col for col in ['id_empleado', 'fecha_solicitud', 'dias_solicitados', 'estado'] if col in df_permisos.columns]
            if cols_mostrar:
                df_recientes = df_permisos.tail(10).sort_values('fecha_solicitud', ascending=False)
                st.dataframe(df_recientes[cols_mostrar], use_container_width=True)
        else:
            st.info("No hay permisos registrados")
    
    with tab3:
        st.info("🔔 Sistema de alertas en desarrollo")

def show_permisos_module():
    """Módulo de permisos (placeholder)"""
    st.title("📝 Gestión de Permisos")
    st.info("🚧 Módulo en desarrollo - Próximamente disponible")

def show_incapacidades_module():
    """Módulo de incapacidades (placeholder)"""
    st.title("🏥 Gestión de Incapacidades")
    st.info("🚧 Módulo en desarrollo - Próximamente disponible")

def show_bonos_module():
    """Módulo de bonos (placeholder)"""
    st.title("💰 Cálculo de Bonos")
    st.info("🚧 Módulo en desarrollo - Próximamente disponible")

def show_empleados_module():
    """Módulo de empleados (placeholder)"""
    st.title("👥 Gestión de Empleados")
    st.info("🚧 Módulo en desarrollo - Próximamente disponible")

def show_usuarios_module():
    """Módulo de usuarios (placeholder)"""
    st.title("👤 Gestión de Usuarios")
    st.info("🚧 Módulo en desarrollo - Próximamente disponible")

def show_reportes_module():
    """Módulo de reportes (placeholder)"""
    st.title("📊 Reportes y Análisis")
    st.info("🚧 Módulo en desarrollo - Próximamente disponible")

def show_auditoria_module():
    """Módulo de auditoría (placeholder)"""
    st.title("🔍 Registro de Auditoría")
    st.info("🚧 Módulo en desarrollo - Próximamente disponible")

def get_oficinas_list(sheets):
    """Helper temporal"""
    from utils.helpers import get_oficinas_list as get_list
    return get_list(sheets)

if __name__ == "__main__":
    main()