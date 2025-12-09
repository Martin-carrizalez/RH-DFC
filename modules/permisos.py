import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from config import get_sheets_manager

def show_permisos_module():
    """Módulo de gestión de permisos (9 días/año)"""
    user_data = st.session_state.get('user_data', {})
    rol = user_data.get('rol', '')
    
    st.title("📅 Gestión de Permisos")
    st.caption("Control de permisos (máximo 9 días por año)")
    
    # Tabs según rol
    if rol == 'admin' or rol == 'supervisora':
        tabs = st.tabs(["📝 Solicitar", "✅ Aprobar", "📊 Historial", "🔄 Sincronizar"])
        
        with tabs[0]:
            solicitar_permiso(user_data)
        
        with tabs[1]:
            aprobar_rechazar_permisos(user_data)
        
        with tabs[2]:
            ver_historial_permisos(user_data, todos=True)
        
        with tabs[3]:
            sincronizar_permisos()
    
    else:  # registrador
        tabs = st.tabs(["📝 Solicitar", "📊 Mi Historial"])
        
        with tabs[0]:
            solicitar_permiso(user_data)
        
        with tabs[1]:
            ver_historial_permisos(user_data, todos=False)


def solicitar_permiso(user_data):
    """Solicitar permiso para empleado"""
    st.subheader("Solicitar Permiso")
    
    manager = get_sheets_manager()
    
    try:
        df_empleados = manager.get_dataframe("empleados")
        
        # Filtrar por oficina si es registrador
        if user_data['rol'] == 'registrador':
            df_empleados = df_empleados[df_empleados['oficina'] == user_data['oficina']]
        
        # Solo empleados activos
        df_empleados = df_empleados[df_empleados['activo'].str.upper() == 'SI']
        
        if df_empleados.empty:
            st.warning("⚠️ No hay empleados disponibles")
            return
        
        with st.form("form_permiso_solicitud", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                empleado_seleccionado = st.selectbox(
                    "Empleado",
                    options=df_empleados['nombre_completo'].tolist()
                )
                
                # Obtener datos del empleado
                empleado_data = df_empleados[df_empleados['nombre_completo'] == empleado_seleccionado].iloc[0]
                id_empleado = empleado_data['id_empleado']
                dias_disponibles = empleado_data['dias_permiso_disponibles']
                
                st.info(f"📊 Días disponibles: **{dias_disponibles}** de 9")
            
            with col2:
                motivo = st.text_area(
                    "Motivo del permiso",
                    placeholder="Describe el motivo del permiso...",
                    height=100
                )
            
            col3, col4, col5 = st.columns(3)
            
            with col3:
                fecha_inicio = st.date_input(
                    "Fecha inicio",
                    min_value=datetime.today(),
                    value=datetime.today()
                )
            
            with col4:
                fecha_fin = st.date_input(
                    "Fecha fin",
                    min_value=datetime.today(),
                    value=datetime.today()
                )
            
            with col5:
                # Calcular días hábiles (lunes a viernes)
                dias_solicitados = calcular_dias_habiles(fecha_inicio, fecha_fin)
                st.metric("Días hábiles", dias_solicitados)
            
            submit = st.form_submit_button("✅ Solicitar Permiso", type="primary", use_container_width=True)
            
            if submit:
                # Validaciones
                if not motivo.strip():
                    st.error("❌ El motivo es obligatorio")
                    st.stop()
                
                if fecha_fin < fecha_inicio:
                    st.error("❌ La fecha fin no puede ser anterior a la fecha inicio")
                    st.stop()
                
                if dias_solicitados <= 0:
                    st.error("❌ El permiso debe incluir al menos un día hábil")
                    st.stop()
                
                if dias_solicitados > dias_disponibles:
                    st.error(f"❌ Días insuficientes. Disponibles: {dias_disponibles}, Solicitados: {dias_solicitados}")
                    st.stop()
                
                # Verificar solapamiento de permisos
                if verificar_solapamiento(manager, id_empleado, fecha_inicio, fecha_fin):
                    st.error("❌ Ya existe un permiso para este empleado en ese período")
                    st.stop()
                
                # Guardar permiso
                try:
                    permiso_data = {
                        'id_empleado': id_empleado,
                        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
                        'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
                        'dias_solicitados': dias_solicitados,
                        'motivo': motivo.strip(),
                        'estado': 'Pendiente',
                        'oficina': empleado_data['oficina'],
                        'solicitado_por': user_data['email'],
                        'timestamp_creacion': datetime.now().isoformat(),
                        'sincronizado': False
                    }
                    
                    manager.supabase.table("permisos").insert(permiso_data).execute()
                    
                    # Log auditoría
                    manager.log_action(
                        usuario=user_data['email'],
                        accion="solicitar_permiso",
                        modulo="permisos",
                        detalles=f"Permiso solicitado para {empleado_seleccionado}: {dias_solicitados} días ({fecha_inicio} a {fecha_fin})"
                    )
                    
                    st.success(f"✅ Permiso solicitado correctamente: {dias_solicitados} días")
                    st.balloons()
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error al solicitar permiso: {e}")
    
    except Exception as e:
        st.error(f"❌ Error: {e}")


def aprobar_rechazar_permisos(user_data):
    """Aprobar o rechazar permisos pendientes"""
    st.subheader("Aprobar Permisos")
    
    manager = get_sheets_manager()
    
    try:
        # Obtener permisos pendientes
        df_permisos = manager.get_dataframe("permisos")
        df_permisos_pendientes = df_permisos[df_permisos['estado'] == 'Pendiente'].copy()
        
        if df_permisos_pendientes.empty:
            st.info("✅ No hay permisos pendientes de aprobación")
            return
        
        # Obtener info de empleados
        df_empleados = manager.get_dataframe("empleados")
        
        # Merge para mostrar nombres
        df_permisos_pendientes = df_permisos_pendientes.merge(
            df_empleados[['id_empleado', 'nombre_completo', 'oficina']],
            on='id_empleado',
            how='left',
            suffixes=('', '_emp')
        )
        
        st.info(f"📋 {len(df_permisos_pendientes)} permisos pendientes")
        
        # Mostrar cada permiso
        for idx, permiso in df_permisos_pendientes.iterrows():
            with st.expander(f"📄 {permiso['nombre_completo']} - {permiso['dias_solicitados']} días"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Empleado:** {permiso['nombre_completo']}")
                    st.write(f"**ID:** {permiso['id_empleado']}")
                    st.write(f"**Oficina:** {permiso['oficina_emp']}")
                    st.write(f"**Solicitado por:** {permiso['solicitado_por']}")
                
                with col2:
                    st.write(f"**Fecha inicio:** {permiso['fecha_inicio']}")
                    st.write(f"**Fecha fin:** {permiso['fecha_fin']}")
                    st.write(f"**Días solicitados:** {permiso['dias_solicitados']}")
                    st.write(f"**Fecha solicitud:** {permiso['timestamp_creacion']}")
                
                st.write(f"**Motivo:** {permiso['motivo']}")
                
                # Obtener días disponibles
                empleado_info = df_empleados[df_empleados['id_empleado'] == permiso['id_empleado']].iloc[0]
                dias_disponibles = empleado_info['dias_permiso_disponibles']
                
                if permiso['dias_solicitados'] > dias_disponibles:
                    st.warning(f"⚠️ Días insuficientes. Disponibles: {dias_disponibles}")
                else:
                    st.success(f"✅ Días disponibles: {dias_disponibles}")
                
                col_aprobar, col_rechazar = st.columns(2)
                
                with col_aprobar:
                    comentario_aprobar = st.text_input(
                        "Comentario (opcional)",
                        key=f"permisos_comentario_aprobar_{permiso['id']}"
                    )
                    
                    if st.button("✅ Aprobar", key=f"permisos_aprobar_{permiso['id']}", type="primary", use_container_width=True):
                        procesar_aprobacion(manager, permiso, user_data, True, comentario_aprobar)
                
                with col_rechazar:
                    comentario_rechazar = st.text_input(
                        "Motivo rechazo",
                        key=f"permisos_comentario_rechazar_{permiso['id']}"
                    )
                    
                    if st.button("❌ Rechazar", key=f"permisos_rechazar_{permiso['id']}", use_container_width=True):
                        if not comentario_rechazar.strip():
                            st.error("⚠️ Debe indicar el motivo del rechazo")
                        else:
                            procesar_aprobacion(manager, permiso, user_data, False, comentario_rechazar)
    
    except Exception as e:
        st.error(f"❌ Error: {e}")


def procesar_aprobacion(manager, permiso, user_data, aprobar, comentario):
    """Procesar aprobación o rechazo de permiso"""
    try:
        nuevo_estado = "Aprobado" if aprobar else "Rechazado"
        
        # Actualizar estado del permiso
        manager.supabase.table("permisos").update({
            'estado': nuevo_estado,
            'aprobado_por': user_data['email'],
            'fecha_aprobacion': datetime.now().isoformat(),
            'comentario_aprobacion': comentario.strip() if comentario else None
        }).eq('id', permiso['id']).execute()
        
        # Si se aprueba, descontar días del empleado
        if aprobar:
            df_empleados = manager.get_dataframe("empleados")
            empleado = df_empleados[df_empleados['id_empleado'] == permiso['id_empleado']].iloc[0]
            dias_actuales = empleado['dias_permiso_disponibles']
            nuevos_dias = dias_actuales - permiso['dias_solicitados']
            
            manager.supabase.table("empleados").update({
                'dias_permiso_disponibles': nuevos_dias
            }).eq('id_empleado', permiso['id_empleado']).execute()
        
        # Log auditoría
        accion = "aprobar_permiso" if aprobar else "rechazar_permiso"
        detalles = f"Permiso {nuevo_estado.lower()} para {permiso['id_empleado']}: {permiso['dias_solicitados']} días"
        if comentario:
            detalles += f". Comentario: {comentario}"
        
        manager.log_action(
            usuario=user_data['email'],
            accion=accion,
            modulo="permisos",
            detalles=detalles
        )
        
        st.success(f"✅ Permiso {nuevo_estado.lower()} correctamente")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error al procesar: {e}")


def ver_historial_permisos(user_data, todos=True):
    """Ver historial de permisos"""
    st.subheader("Historial de Permisos")
    
    manager = get_sheets_manager()
    
    try:
        df_permisos = manager.get_dataframe("permisos")
        
        if df_permisos.empty:
            st.info("🔭 No hay permisos registrados")
            return
        
        # Filtrar por oficina si es registrador
        if not todos and user_data['rol'] == 'registrador':
            df_permisos = df_permisos[df_permisos['oficina'] == user_data['oficina']]
        
        # Obtener nombres de empleados
        df_empleados = manager.get_dataframe("empleados")
        df_permisos = df_permisos.merge(
            df_empleados[['id_empleado', 'nombre_completo']],
            on='id_empleado',
            how='left'
        )
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        
        with col1:
            estado_filtro = st.selectbox(
                "Estado",
                ["Todos", "Pendiente", "Aprobado", "Rechazado"],
                key="permisos_filtro_estado"
            )
        
        with col2:
            if todos:
                oficinas = ["Todas"] + sorted(df_permisos['oficina'].unique().tolist())
                oficina_filtro = st.selectbox("Oficina", oficinas, key="permisos_filtro_oficina")
            else:
                oficina_filtro = user_data['oficina']
                st.text_input("Oficina", value=oficina_filtro, disabled=True, key="permisos_oficina_display")
        
        with col3:
            año_filtro = st.selectbox(
                "Año",
                ["Todos"] + sorted(df_permisos['fecha_inicio'].str[:4].unique().tolist(), reverse=True),
                key="permisos_filtro_año"
            )
        
        # Aplicar filtros
        df_filtrado = df_permisos.copy()
        
        if estado_filtro != "Todos":
            df_filtrado = df_filtrado[df_filtrado['estado'] == estado_filtro]
        
        if todos and oficina_filtro != "Todas":
            df_filtrado = df_filtrado[df_filtrado['oficina'] == oficina_filtro]
        elif not todos:
            df_filtrado = df_filtrado[df_filtrado['oficina'] == oficina_filtro]
        
        if año_filtro != "Todos":
            df_filtrado = df_filtrado[df_filtrado['fecha_inicio'].str.startswith(año_filtro)]
        
        # Mostrar estadísticas
        col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
        
        with col_stats1:
            st.metric("Total Permisos", len(df_filtrado))
        
        with col_stats2:
            pendientes = len(df_filtrado[df_filtrado['estado'] == 'Pendiente'])
            st.metric("Pendientes", pendientes)
        
        with col_stats3:
            aprobados = len(df_filtrado[df_filtrado['estado'] == 'Aprobado'])
            st.metric("Aprobados", aprobados)
        
        with col_stats4:
            total_dias = df_filtrado[df_filtrado['estado'] == 'Aprobado']['dias_solicitados'].sum()
            st.metric("Días Aprobados", int(total_dias))
        
        # Mostrar tabla
        if df_filtrado.empty:
            st.info("🔭 No hay permisos con los filtros seleccionados")
        else:
            # Ordenar por fecha de creación descendente
            df_mostrar = df_filtrado.sort_values('timestamp_creacion', ascending=False)
            
            # Seleccionar y renombrar columnas
            columnas_mostrar = {
                'nombre_completo': 'Empleado',
                'id_empleado': 'ID',
                'fecha_inicio': 'Inicio',
                'fecha_fin': 'Fin',
                'dias_solicitados': 'Días',
                'motivo': 'Motivo',
                'estado': 'Estado',
                'solicitado_por': 'Solicitado por',
                'aprobado_por': 'Aprobado por'
            }
            
            df_tabla = df_mostrar[list(columnas_mostrar.keys())].copy()
            df_tabla = df_tabla.rename(columns=columnas_mostrar)
            
            # Aplicar estilos según estado
            def colorear_estado(val):
                if val == 'Aprobado':
                    return 'background-color: #d4edda; color: #155724'
                elif val == 'Rechazado':
                    return 'background-color: #f8d7da; color: #721c24'
                elif val == 'Pendiente':
                    return 'background-color: #fff3cd; color: #856404'
                return ''
            
            st.dataframe(
                df_tabla.style.applymap(colorear_estado, subset=['Estado']),
                use_container_width=True,
                height=400
            )
            
            # Exportar a CSV
            csv = df_tabla.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Exportar a CSV",
                csv,
                f"permisos_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv",
                use_container_width=True,
                key="permisos_download_csv"
            )
    
    except Exception as e:
        st.error(f"❌ Error: {e}")


def sincronizar_permisos():
    """Sincronizar permisos a Google Sheets"""
    st.subheader("Sincronizar Permisos a Google Sheets")
    
    manager = get_sheets_manager()
    
    try:
        # Contar pendientes de sincronizar
        df_permisos = manager.get_dataframe("permisos")
        pendientes = len(df_permisos[df_permisos['sincronizado'] == False])
        
        st.info(f"📊 Permisos pendientes de sincronizar: **{pendientes}**")
        
        if st.button("🔄 Sincronizar a Google Sheets", type="primary", use_container_width=True):
            if pendientes == 0:
                st.warning("✅ No hay permisos pendientes de sincronizar")
                return
            
            with st.spinner("Sincronizando permisos..."):
                try:
                    # Sincronizar
                    result = manager.sync_to_sheets(tabla="permisos")
                    
                    st.success(f"✅ Sincronización completada: {result['sincronizados']} permisos")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error en sincronización: {e}")
    
    except Exception as e:
        st.error(f"❌ Error: {e}")


def calcular_dias_habiles(fecha_inicio, fecha_fin):
    """Calcular días hábiles entre dos fechas (lunes a viernes)"""
    dias = 0
    fecha_actual = fecha_inicio
    
    while fecha_actual <= fecha_fin:
        # 0=lunes, 6=domingo
        if fecha_actual.weekday() < 5:  # Lunes a viernes
            dias += 1
        fecha_actual += timedelta(days=1)
    
    return dias


def verificar_solapamiento(manager, id_empleado, fecha_inicio, fecha_fin):
    """Verificar si hay permisos que se solapan"""
    try:
        df_permisos = manager.get_dataframe("permisos")
        
        # Filtrar permisos del empleado que no estén rechazados
        permisos_empleado = df_permisos[
            (df_permisos['id_empleado'] == id_empleado) &
            (df_permisos['estado'] != 'Rechazado')
        ]
        
        if permisos_empleado.empty:
            return False
        
        # Convertir fechas
        fecha_inicio_str = fecha_inicio.strftime('%Y-%m-%d')
        fecha_fin_str = fecha_fin.strftime('%Y-%m-%d')
        
        for _, permiso in permisos_empleado.iterrows():
            # Verificar solapamiento
            if (fecha_inicio_str <= permiso['fecha_fin'] and 
                fecha_fin_str >= permiso['fecha_inicio']):
                return True
        
        return False
        
    except:
        return False