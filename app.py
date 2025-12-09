import streamlit as st
from auth import check_authentication, login, logout, get_user_info
from modules.asistencias import show_asistencias_module
from modules.permisos import show_permisos_module
from modules.incapacidades import show_incapacidades_module


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
    user_key = f"{user['email']}_{user['oficina']}"
    
    # CRÍTICO: Inicializar módulo actual
    if 'active_module' not in st.session_state:
        st.session_state.active_module = None
    
    if 'module_counter' not in st.session_state:
        st.session_state.module_counter = 0
    
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
                "🔖 Permisos",
                "🏥 Incapacidades",
                "💰 Bonos",
                "👥 Empleados",
                "👤 Usuarios",
                "📊 Reportes",
                "📝 Auditoría"
            ],
            "supervisora": [
                "🏠 Dashboard",
                "📋 Asistencias",
                "🔖 Permisos",
                "🏥 Incapacidades",
                "💰 Bonos",
                "📊 Reportes"
            ],
            "registrador": [
                "📋 Asistencias",
                "🔖 Permisos",
                "🏥 Incapacidades"
            ]
        }
        
        opciones = menu_options.get(user['rol'], menu_options['registrador'])
        
        # Determinar índice actual
        if st.session_state.active_module in opciones:
            current_index = opciones.index(st.session_state.active_module)
        else:
            current_index = 0
            st.session_state.active_module = opciones[0]
        
        # Radio button
        menu_selection = st.radio(
            "Seleccionar módulo",
            opciones,
            index=current_index,
            label_visibility="collapsed",
            key=f"menu_radio_{user_key}"
        )
        
        # CRÍTICO: Detectar cambio de módulo
        if menu_selection != st.session_state.active_module:
            # LIMPIAR TODO el estado excepto auth
            keys_to_keep = ['authenticated', 'user_data', 'active_module', 'module_counter']
            keys_to_delete = [k for k in st.session_state.keys() if k not in keys_to_keep]
            for key in keys_to_delete:
                del st.session_state[key]
            
            # Actualizar módulo activo
            st.session_state.active_module = menu_selection
            st.session_state.module_counter += 1
            
            # Limpiar caché
            st.cache_data.clear()
            
            # Forzar rerun
            st.rerun()
        
        st.markdown("---")
        
        # Botón de logout
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.cache_data.clear()
            logout()
    
    # Contenido principal con aislamiento por contador
    module_key = f"{st.session_state.active_module}_{st.session_state.module_counter}"
    
    # Container único para forzar re-renderizado limpio
    with st.container(key=module_key):
        if st.session_state.active_module == "🏠 Dashboard":
            show_dashboard()
        elif st.session_state.active_module == "📋 Asistencias":
            show_asistencias_module()
        elif st.session_state.active_module == "🔖 Permisos":
            show_permisos_module()
        elif st.session_state.active_module == "🏥 Incapacidades":
            show_incapacidades_module()
        elif st.session_state.active_module == "💰 Bonos":
            show_bonos_module()
        elif st.session_state.active_module == "👥 Empleados":
            show_empleados_module()
        elif st.session_state.active_module == "👤 Usuarios":
            show_usuarios_module()
        elif st.session_state.active_module == "📊 Reportes":
            show_reportes_module()
        elif st.session_state.active_module == "📝 Auditoría":
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
            total_empleados = len(df_empleados[df_empleados['activo'].str.upper() == 'SI'])
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
        st.metric("🔖 Permisos Pendientes", permisos_pendientes)
    
    with col4:
        oficinas = []
        if not df_empleados.empty and 'oficina' in df_empleados.columns:
            oficinas = df_empleados['oficina'].unique().tolist()
        st.metric("🏢 Oficinas", len(oficinas))
    
    st.markdown("---")
    
    # Información rápida
    st.subheader("📊 Resumen del Sistema")
    
    tab1, tab2, tab3 = st.tabs(["Últimas Asistencias", "Permisos Recientes", "Incapacidades Activas"])
    
    with tab1:
        if not df_asistencias.empty:
            try:
                df_empleados_info = sheets.get_dataframe("empleados")
                df_display = df_asistencias.merge(
                    df_empleados_info[['id_empleado', 'nombre_completo']],
                    on='id_empleado',
                    how='left'
                )
                
                if 'timestamp_sistema' in df_display.columns:
                    df_display = df_display.sort_values('timestamp_sistema', ascending=False).head(10)
                else:
                    df_display = df_display.tail(10)
                
                cols_mostrar = []
                if 'fecha' in df_display.columns:
                    cols_mostrar.append('fecha')
                if 'nombre_completo' in df_display.columns:
                    cols_mostrar.append('nombre_completo')
                elif 'id_empleado' in df_display.columns:
                    cols_mostrar.append('id_empleado')
                if 'estado' in df_display.columns:
                    cols_mostrar.append('estado')
                if 'oficina' in df_display.columns:
                    cols_mostrar.append('oficina')
                
                if cols_mostrar:
                    st.dataframe(df_display[cols_mostrar], use_container_width=True, hide_index=True)
                else:
                    st.info("No hay datos para mostrar")
            except Exception as e:
                st.error(f"Error al cargar asistencias: {e}")
        else:
            st.info("No hay asistencias registradas")
    
    with tab2:
        if not df_permisos.empty:
            try:
                df_empleados_info = sheets.get_dataframe("empleados")
                df_display = df_permisos.merge(
                    df_empleados_info[['id_empleado', 'nombre_completo']],
                    on='id_empleado',
                    how='left'
                )
                
                if 'timestamp_creacion' in df_display.columns:
                    df_display = df_display.sort_values('timestamp_creacion', ascending=False).head(10)
                else:
                    df_display = df_display.tail(10)
                
                cols_mostrar = []
                if 'nombre_completo' in df_display.columns:
                    cols_mostrar.append('nombre_completo')
                elif 'id_empleado' in df_display.columns:
                    cols_mostrar.append('id_empleado')
                if 'fecha_inicio' in df_display.columns:
                    cols_mostrar.append('fecha_inicio')
                if 'dias_solicitados' in df_display.columns:
                    cols_mostrar.append('dias_solicitados')
                if 'estado' in df_display.columns:
                    cols_mostrar.append('estado')
                
                if cols_mostrar:
                    st.dataframe(df_display[cols_mostrar], use_container_width=True, hide_index=True)
                else:
                    st.info("No hay datos para mostrar")
            except Exception as e:
                st.error(f"Error al cargar permisos: {e}")
        else:
            st.info("No hay permisos registrados")
    
    with tab3:
        df_incapacidades = sheets.get_dataframe("incapacidades")
        if not df_incapacidades.empty:
            try:
                from datetime import datetime
                import pandas as pd
                hoy = datetime.now().date()
                
                df_incapacidades['fecha_fin_dt'] = pd.to_datetime(df_incapacidades['fecha_fin']).dt.date
                df_activas = df_incapacidades[df_incapacidades['fecha_fin_dt'] >= hoy]
                
                if not df_activas.empty:
                    df_empleados_info = sheets.get_dataframe("empleados")
                    df_display = df_activas.merge(
                        df_empleados_info[['id_empleado', 'nombre_completo']],
                        on='id_empleado',
                        how='left'
                    )
                    
                    cols_mostrar = []
                    if 'nombre_completo' in df_display.columns:
                        cols_mostrar.append('nombre_completo')
                    if 'tipo' in df_display.columns:
                        cols_mostrar.append('tipo')
                    if 'fecha_inicio' in df_display.columns:
                        cols_mostrar.append('fecha_inicio')
                    if 'fecha_fin' in df_display.columns:
                        cols_mostrar.append('fecha_fin')
                    if 'dias_totales' in df_display.columns:
                        cols_mostrar.append('dias_totales')
                    
                    if cols_mostrar:
                        st.dataframe(df_display[cols_mostrar].head(10), use_container_width=True, hide_index=True)
                    else:
                        st.info("No hay incapacidades activas")
                else:
                    st.info("No hay incapacidades activas")
            except Exception as e:
                st.error(f"Error al cargar incapacidades: {e}")
        else:
            st.info("No hay incapacidades registradas")

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
    st.title("📝 Registro de Auditoría")
    st.info("🚧 Módulo en desarrollo - Próximamente disponible")

if __name__ == "__main__":
    main()