import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from config import get_sheets_manager

def show_incapacidades_module():
    """Módulo de gestión de incapacidades"""
    user_data = st.session_state.get('user_data', {})
    rol = user_data.get('rol', '')
    
    st.title("🏥 Gestión de Incapacidades")
    st.caption("Registro de incapacidades médicas, maternidad y accidentes laborales")
    
    # Tabs según rol
    if rol == 'admin' or rol == 'supervisora':
        tabs = st.tabs(["📝 Registrar", "📊 Historial", "📈 Estadísticas", "🔄 Sincronizar"])
        
        with tabs[0]:
            registrar_incapacidad(user_data)
        
        with tabs[1]:
            ver_historial_incapacidades(user_data, todos=True)
        
        with tabs[2]:
            ver_estadisticas_incapacidades()
        
        with tabs[3]:
            sincronizar_incapacidades()
    
    else:  # registrador
        tabs = st.tabs(["📝 Registrar", "📊 Historial"])
        
        with tabs[0]:
            registrar_incapacidad(user_data)
        
        with tabs[1]:
            ver_historial_incapacidades(user_data, todos=False)


def registrar_incapacidad(user_data):
    """Registrar incapacidad para empleado"""
    st.subheader("Registrar Incapacidad")
    
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
        
        with st.form("form_incapacidad_registro", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                empleado_seleccionado = st.selectbox(
                    "Empleado",
                    options=df_empleados['nombre_completo'].tolist()
                )
                
                empleado_data = df_empleados[df_empleados['nombre_completo'] == empleado_seleccionado].iloc[0]
                id_empleado = empleado_data['id_empleado']
                
                st.info(f"📋 ID: {id_empleado} | Oficina: {empleado_data['oficina']}")
            
            with col2:
                tipo = st.selectbox(
                    "Tipo de Incapacidad",
                    ["Enfermedad General", "Maternidad", "Accidente de Trabajo", "Riesgo de Trabajo"]
                )
            
            col3, col4 = st.columns(2)
            
            with col3:
                fecha_inicio = st.date_input(
                    "Fecha inicio",
                    value=datetime.today()
                )
            
            with col4:
                fecha_fin = st.date_input(
                    "Fecha fin",
                    value=datetime.today()
                )
            
            # Calcular días totales (calendario completo)
            if fecha_fin >= fecha_inicio:
                dias_totales = (fecha_fin - fecha_inicio).days + 1
                st.metric("📅 Días totales", dias_totales)
            else:
                dias_totales = 0
                st.error("⚠️ Fecha fin debe ser mayor o igual a fecha inicio")
            
            col5, col6 = st.columns(2)
            
            with col5:
                folio = st.text_input(
                    "Folio (opcional)",
                    placeholder="Número de folio IMSS/ISSSTE"
                )
            
            with col6:
                institucion = st.text_input(
                    "Institución (opcional)",
                    placeholder="IMSS, ISSSTE, Privado, etc."
                )
            
            motivo = st.text_area(
                "Descripción/Diagnóstico",
                placeholder="Describe el motivo de la incapacidad...",
                height=100
            )
            
            documento_url = st.text_input(
                "URL del documento (opcional)",
                placeholder="https://drive.google.com/...",
                help="Link a Google Drive, Dropbox, etc."
            )
            
            submit = st.form_submit_button("✅ Registrar Incapacidad", type="primary", use_container_width=True)
            
            if submit:
                # Validaciones
                if fecha_fin < fecha_inicio:
                    st.error("❌ La fecha fin no puede ser anterior a la fecha inicio")
                    st.stop()
                
                if not motivo.strip():
                    st.error("❌ La descripción/diagnóstico es obligatoria")
                    st.stop()
                
                # Guardar incapacidad
                try:
                    incapacidad_data = {
                        'id_empleado': id_empleado,
                        'tipo': tipo,
                        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
                        'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
                        'dias_totales': dias_totales,
                        'motivo': motivo.strip(),
                        'folio': folio.strip() if folio else None,
                        'institucion': institucion.strip() if institucion else None,
                        'documento_url': documento_url.strip() if documento_url else None,
                        'oficina': empleado_data['oficina'],
                        'registrado_por': user_data['email'],
                        'timestamp_creacion': datetime.now().isoformat(),
                        'sincronizado': False
                    }
                    
                    manager.supabase.table("incapacidades").insert(incapacidad_data).execute()
                    
                    # Log auditoría
                    manager.log_action(
                        usuario=user_data['email'],
                        accion="registrar_incapacidad",
                        modulo="incapacidades",
                        detalles=f"Incapacidad registrada para {empleado_seleccionado}: {tipo}, {dias_totales} días ({fecha_inicio} a {fecha_fin})"
                    )
                    
                    st.success(f"✅ Incapacidad registrada correctamente: {dias_totales} días")
                    st.balloons()
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error al registrar incapacidad: {e}")
    
    except Exception as e:
        st.error(f"❌ Error: {e}")


def ver_historial_incapacidades(user_data, todos=True):
    """Ver historial de incapacidades"""
    st.subheader("Historial de Incapacidades")
    
    manager = get_sheets_manager()
    
    try:
        df_incapacidades = manager.get_dataframe("incapacidades")
        
        if df_incapacidades.empty:
            st.info("🔭 No hay incapacidades registradas")
            return
        
        # Filtrar por oficina si es registrador
        if not todos and user_data['rol'] == 'registrador':
            df_incapacidades = df_incapacidades[df_incapacidades['oficina'] == user_data['oficina']]
        
        # Obtener nombres de empleados
        df_empleados = manager.get_dataframe("empleados")
        df_incapacidades = df_incapacidades.merge(
            df_empleados[['id_empleado', 'nombre_completo']],
            on='id_empleado',
            how='left'
        )
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        
        with col1:
            tipos = ["Todos"] + sorted(df_incapacidades['tipo'].unique().tolist())
            tipo_filtro = st.selectbox("Tipo", tipos, key="incapacidades_filtro_tipo")
        
        with col2:
            if todos:
                oficinas = ["Todas"] + sorted(df_incapacidades['oficina'].unique().tolist())
                oficina_filtro = st.selectbox("Oficina", oficinas, key="incapacidades_filtro_oficina")
            else:
                oficina_filtro = user_data['oficina']
                st.text_input("Oficina", value=oficina_filtro, disabled=True, key="incapacidades_oficina_display")
        
        with col3:
            años = ["Todos"] + sorted(df_incapacidades['fecha_inicio'].str[:4].unique().tolist(), reverse=True)
            año_filtro = st.selectbox("Año", años, key="incapacidades_filtro_año")
        
        # Aplicar filtros
        df_filtrado = df_incapacidades.copy()
        
        if tipo_filtro != "Todos":
            df_filtrado = df_filtrado[df_filtrado['tipo'] == tipo_filtro]
        
        if todos and oficina_filtro != "Todas":
            df_filtrado = df_filtrado[df_filtrado['oficina'] == oficina_filtro]
        elif not todos:
            df_filtrado = df_filtrado[df_filtrado['oficina'] == oficina_filtro]
        
        if año_filtro != "Todos":
            df_filtrado = df_filtrado[df_filtrado['fecha_inicio'].str.startswith(año_filtro)]
        
        # Estadísticas
        col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
        
        with col_stats1:
            st.metric("Total Registros", len(df_filtrado))
        
        with col_stats2:
            total_dias = df_filtrado['dias_totales'].sum()
            st.metric("Total Días", int(total_dias))
        
        with col_stats3:
            if not df_filtrado.empty:
                promedio_dias = df_filtrado['dias_totales'].mean()
                st.metric("Promedio Días", f"{promedio_dias:.1f}")
            else:
                st.metric("Promedio Días", 0)
        
        with col_stats4:
            empleados_unicos = df_filtrado['id_empleado'].nunique()
            st.metric("Empleados", empleados_unicos)
        
        # Mostrar tabla
        if df_filtrado.empty:
            st.info("🔭 No hay incapacidades con los filtros seleccionados")
        else:
            # Ordenar por fecha de creación descendente
            df_mostrar = df_filtrado.sort_values('timestamp_creacion', ascending=False)
            
            # Seleccionar y renombrar columnas
            columnas_mostrar = {
                'nombre_completo': 'Empleado',
                'id_empleado': 'ID',
                'tipo': 'Tipo',
                'fecha_inicio': 'Inicio',
                'fecha_fin': 'Fin',
                'dias_totales': 'Días',
                'folio': 'Folio',
                'institucion': 'Institución',
                'motivo': 'Diagnóstico'
            }
            
            df_tabla = df_mostrar[list(columnas_mostrar.keys())].copy()
            df_tabla = df_tabla.rename(columns=columnas_mostrar)
            
            # Aplicar estilos según tipo
            def colorear_tipo(val):
                if val == 'Maternidad':
                    return 'background-color: #e7f3ff; color: #0066cc'
                elif 'Accidente' in val or 'Riesgo' in val:
                    return 'background-color: #fff3cd; color: #856404'
                else:
                    return 'background-color: #f8f9fa; color: #495057'
            
            st.dataframe(
                df_tabla.style.applymap(colorear_tipo, subset=['Tipo']),
                use_container_width=True,
                height=400
            )
            
            # Mostrar detalles con links a documentos
            if st.checkbox("🔎 Mostrar documentos adjuntos", key="incapacidades_show_docs"):
                df_con_docs = df_mostrar[df_mostrar['documento_url'].notna()]
                if not df_con_docs.empty:
                    for idx, row in df_con_docs.iterrows():
                        with st.expander(f"{row['nombre_completo']} - {row['tipo']}", key=f"incapacidades_exp_doc_{idx}"):
                            st.write(f"**Fecha:** {row['fecha_inicio']} a {row['fecha_fin']}")
                            st.write(f"**Diagnóstico:** {row['motivo']}")
                            st.markdown(f"**📄 Documento:** [{row['documento_url']}]({row['documento_url']})")
                else:
                    st.info("No hay documentos adjuntos")
            
            # Exportar a CSV
            csv = df_tabla.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Exportar a CSV",
                csv,
                f"incapacidades_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv",
                use_container_width=True,
                key="incapacidades_download_csv"
            )
    
    except Exception as e:
        st.error(f"❌ Error: {e}")


def ver_estadisticas_incapacidades():
    """Estadísticas de incapacidades"""
    st.subheader("Estadísticas de Incapacidades")
    
    manager = get_sheets_manager()
    
    try:
        df_incapacidades = manager.get_dataframe("incapacidades")
        
        if df_incapacidades.empty:
            st.info("🔭 No hay datos para mostrar estadísticas")
            return
        
        # Obtener nombres
        df_empleados = manager.get_dataframe("empleados")
        df_incapacidades = df_incapacidades.merge(
            df_empleados[['id_empleado', 'nombre_completo', 'oficina']],
            on='id_empleado',
            how='left',
            suffixes=('', '_emp')
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Por Tipo")
            tipo_stats = df_incapacidades.groupby('tipo').agg({
                'id': 'count',
                'dias_totales': 'sum'
            }).rename(columns={'id': 'Casos', 'dias_totales': 'Días Totales'})
            st.dataframe(tipo_stats, use_container_width=True)
        
        with col2:
            st.subheader("🏢 Por Oficina")
            oficina_col = 'oficina' if 'oficina' in df_incapacidades.columns else 'oficina_emp'
            oficina_stats = df_incapacidades.groupby(oficina_col).agg({
                'id': 'count',
                'dias_totales': 'sum'
            }).rename(columns={'id': 'Casos', 'dias_totales': 'Días Totales'})
            st.dataframe(oficina_stats, use_container_width=True)
        
        st.subheader("👥 Top 10 Empleados con más Incapacidades")
        empleado_stats = df_incapacidades.groupby(['id_empleado', 'nombre_completo']).agg({
            'id': 'count',
            'dias_totales': 'sum'
        }).rename(columns={'id': 'Casos', 'dias_totales': 'Días Totales'}).sort_values('Casos', ascending=False).head(10)
        st.dataframe(empleado_stats, use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ Error: {e}")


def sincronizar_incapacidades():
    """Sincronizar incapacidades a Google Sheets"""
    st.subheader("Sincronizar Incapacidades a Google Sheets")
    
    manager = get_sheets_manager()
    
    try:
        df_incapacidades = manager.get_dataframe("incapacidades")
        pendientes = len(df_incapacidades[df_incapacidades['sincronizado'] == False])
        
        st.info(f"📊 Incapacidades pendientes de sincronizar: **{pendientes}**")
        
        if st.button("🔄 Sincronizar a Google Sheets", type="primary", use_container_width=True):
            if pendientes == 0:
                st.warning("✅ No hay incapacidades pendientes de sincronizar")
                return
            
            with st.spinner("Sincronizando incapacidades..."):
                try:
                    result = manager.sync_to_sheets(tabla="incapacidades")
                    
                    st.success(f"✅ Sincronización completada: {result['sincronizados']} incapacidades")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error en sincronización: {e}")
    
    except Exception as e:
        st.error(f"❌ Error: {e}")