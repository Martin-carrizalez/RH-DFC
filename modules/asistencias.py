import streamlit as st
from datetime import datetime, date, timedelta
import pandas as pd

def show_asistencias_module():
    """Módulo de asistencias con Supabase + Sync a Sheets"""
    st.title("📋 Registro de Asistencias")
    
    from config import get_sheets_manager
    from auth import get_user_info
    
    user = get_user_info()
    manager = get_sheets_manager()
    
    # Tabs principales
    tab1, tab2, tab3, tab4 = st.tabs([
        "✏️ Registrar",
        "📊 Ver Asistencias", 
        "📈 Estadísticas",
        "🔄 Sincronizar"
    ])
    
    with tab1:
        registrar_asistencia(user, manager)
    
    with tab2:
        ver_asistencias(user, manager)
    
    with tab3:
        mostrar_estadisticas(user, manager)
    
    with tab4:
        sincronizar_sheets(user, manager)

def registrar_asistencia(user, manager):
    """Formulario de registro"""
    st.subheader("Registro Diario")
    
    # Determinar oficina
    if user['rol'] == 'registrador':
        oficina = user['oficina']
        st.info(f"📍 Oficina: {oficina}")
    else:
        df_emp = manager.get_dataframe("empleados")
        oficinas = sorted(df_emp['oficina'].unique().tolist()) if not df_emp.empty else []
        oficina = st.selectbox("📍 Oficina", oficinas)
    
    # Fecha
    col1, col2 = st.columns([2, 1])
    with col1:
        fecha = st.date_input("📅 Fecha", value=date.today(), max_value=date.today())
    with col2:
        es_sabado = fecha.weekday() == 5
        st.warning("⚠️ SÁBADO") if es_sabado else st.info("Día normal")
    
    # Obtener empleados
    df_empleados = manager.get_dataframe("empleados")
    empleados = df_empleados[df_empleados['oficina'] == oficina] if not df_empleados.empty else pd.DataFrame()
    
    if empleados.empty:
        st.warning("No hay empleados en esta oficina")
        return
    
    st.markdown("---")
    st.subheader(f"👥 Empleados ({len(empleados)})")
    
    # Verificar duplicados
    df_asist = manager.get_dataframe("asistencias")
    fecha_str = fecha.strftime("%Y-%m-%d")
    ya_registrados = []
    if not df_asist.empty:
        ya_registrados = df_asist[
            (df_asist['fecha'] == fecha_str) & 
            (df_asist['oficina'] == oficina)
        ]['id_empleado'].tolist()
    
    if ya_registrados:
        st.error(f"⚠️ {len(ya_registrados)} empleados ya registrados hoy")
    
    # Formulario
    with st.form("form_asistencias"):
        registros = []
        
        for idx, emp in empleados.iterrows():
            ya_tiene = emp['id_empleado'] in ya_registrados
            
            col1, col2, col3, col4 = st.columns([3, 2, 2, 3])
            
            with col1:
                st.write(f"**{emp['nombre_completo']}**")
                if ya_tiene:
                    st.caption("✅ Ya registrado")
            
            with col2:
                estado = st.selectbox(
                    "Estado",
                    ["Presente", "Ausente", "Retardo", "Permiso", "Incapacidad"],
                    key=f"estado_{emp['id_empleado']}",
                    disabled=ya_tiene,
                    label_visibility="collapsed"
                )
            
            with col3:
                if estado in ["Presente", "Retardo"] and not ya_tiene:
                    hora = st.time_input(
                        "Hora",
                        value=datetime.strptime("08:00", "%H:%M").time(),
                        key=f"hora_{emp['id_empleado']}",
                        label_visibility="collapsed"
                    )
                else:
                    hora = None
            
            with col4:
                obs = st.text_input(
                    "Observaciones",
                    key=f"obs_{emp['id_empleado']}",
                    disabled=ya_tiene,
                    label_visibility="collapsed"
                )
            
            if not ya_tiene:
                registros.append({
                    'id_empleado': emp['id_empleado'],
                    'nombre': emp['nombre_completo'],
                    'estado': estado,
                    'hora': hora,
                    'observaciones': obs
                })
        
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            submit = st.form_submit_button("💾 Guardar", use_container_width=True, type="primary")
        
        if submit and registros:
            guardar_asistencias(registros, fecha, oficina, es_sabado, user, manager)

def guardar_asistencias(registros, fecha, oficina, es_sabado, user, manager):
    """Guardar en Supabase"""
    try:
        timestamp = datetime.now().isoformat()
        guardados = 0
        
        progress = st.progress(0)
        for i, reg in enumerate(registros):
            datos = {
                'id_empleado': reg['id_empleado'],
                'fecha': fecha.strftime("%Y-%m-%d"),
                'hora_registro': reg['hora'].strftime("%H:%M") if reg['hora'] else "",
                'estado': reg['estado'],
                'es_sabado': "SI" if es_sabado else "NO",
                'oficina': oficina,
                'registrado_por': user['email'],
                'timestamp_sistema': timestamp,
                'ip_registro': 'local',
                'observaciones': reg['observaciones']
            }
            
            if manager.append_row('asistencias', datos):
                guardados += 1
            
            progress.progress((i + 1) / len(registros))
        
        progress.empty()
        
        if guardados > 0:
            st.success(f"✅ {guardados} asistencias guardadas en Supabase")
            st.info("💡 Sincroniza con Sheets al final del día")
            st.balloons()
            st.rerun()
        
    except Exception as e:
        st.error(f"Error: {e}")

def ver_asistencias(user, manager):
    """Consultar asistencias"""
    st.subheader("📊 Consultar Asistencias")
    
    col1, col2 = st.columns(2)
    with col1:
        fecha_inicio = st.date_input("Desde", value=date.today() - timedelta(days=7))
    with col2:
        fecha_fin = st.date_input("Hasta", value=date.today())
    
    df = manager.get_dataframe("asistencias")
    if df.empty:
        st.info("No hay registros")
        return
    
    df['fecha'] = pd.to_datetime(df['fecha'])
    df_filtrado = df[
        (df['fecha'] >= pd.to_datetime(fecha_inicio)) &
        (df['fecha'] <= pd.to_datetime(fecha_fin))
    ]
    
    if user['rol'] == 'registrador':
        df_filtrado = df_filtrado[df_filtrado['oficina'] == user['oficina']]
    
    if not df_filtrado.empty:
        st.metric("Total registros", len(df_filtrado))
        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
    else:
        st.info("Sin registros en este rango")

def mostrar_estadisticas(user, manager):
    """Estadísticas"""
    st.subheader("📈 Estadísticas")
    st.info("🚧 En desarrollo")

def sincronizar_sheets(user, manager):
    """Sincronizar con Google Sheets"""
    st.subheader("🔄 Sincronización con Google Sheets")
    
    if user['rol'] not in ['admin', 'supervisora']:
        st.error("❌ Solo admin y supervisora pueden sincronizar")
        return
    
    st.info("""
    **¿Cómo funciona?**
    - Supabase: Base principal (rápida, sin límites)
    - Sheets: Backup diario
    - Sincroniza UNA vez al final del día
    """)
    
    # Ver pendientes
    df_pendientes = manager.supabase.table('asistencias').select("*").eq('sincronizado', False).execute()
    total_pendientes = len(df_pendientes.data)
    
    st.metric("Registros sin sincronizar", total_pendientes)
    
    if total_pendientes == 0:
        st.success("✅ Todo sincronizado")
        return
    
    st.markdown("---")
    
    if st.button("🚀 Sincronizar ahora", type="primary", use_container_width=True):
        with st.spinner("Sincronizando..."):
            exito, mensaje = manager.sincronizar_a_sheets()
            
            if exito:
                st.success(f"✅ {mensaje}")
                manager.log_action(
                    usuario=user['email'],
                    accion="sincronizacion_sheets",
                    modulo="asistencias",
                    detalles=mensaje
                )
                st.balloons()
                st.rerun()
            else:
                st.error(f"❌ {mensaje}")