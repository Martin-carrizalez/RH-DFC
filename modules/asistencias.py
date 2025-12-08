import streamlit as st
from datetime import datetime, date, timedelta
import pandas as pd
from config import get_sheets_manager
from auth import get_user_info
from utils.helpers import (
    format_date, format_time, is_saturday, 
    get_empleados_by_oficina, get_employee_stats,
    get_oficinas_list
)

def show_asistencias_module():
    """Módulo principal de asistencias"""
    st.title("📋 Registro de Asistencias")
    
    user = get_user_info()
    sheets = get_sheets_manager()
    
    # Tabs principales
    tab1, tab2, tab3 = st.tabs([
        "✏️ Registrar Asistencia", 
        "📊 Ver Asistencias",
        "📈 Estadísticas"
    ])
    
    with tab1:
        registrar_asistencia(user, sheets)
    
    with tab2:
        ver_asistencias(user, sheets)
    
    with tab3:
        mostrar_estadisticas(user, sheets)

def registrar_asistencia(user, sheets):
    """Formulario para registrar asistencias diarias"""
    st.subheader("Registro Diario de Asistencias")
    
    # Determinar oficina según rol
    if user['rol'] == 'registrador':
        oficina_seleccionada = user['oficina']
        st.info(f"📍 **Oficina:** {oficina_seleccionada}")
    else:
        # Admin y supervisora pueden ver todas las oficinas
        df_empleados = sheets.get_dataframe("empleados")
        if not df_empleados.empty:
            oficinas = sorted(df_empleados['oficina'].unique().tolist())
            oficina_seleccionada = st.selectbox("📍 Seleccionar Oficina", oficinas)
        else:
            st.warning("⚠️ No hay empleados registrados en el sistema")
            return
    
    # Seleccionar fecha
    col1, col2 = st.columns([2, 1])
    with col1:
        fecha_registro = st.date_input(
            "📅 Fecha de registro",
            value=date.today(),
            max_value=date.today()
        )
    
    with col2:
        es_sabado = is_saturday(fecha_registro)
        if es_sabado:
            st.warning("⚠️ Es SÁBADO")
        else:
            st.info("ℹ️ Día normal")
    
    # Obtener empleados de la oficina
    empleados = get_empleados_by_oficina(oficina_seleccionada, sheets)
    
    if empleados.empty:
        st.warning("⚠️ No hay empleados registrados en esta oficina")
        return
    
    st.markdown("---")
    st.subheader(f"👥 Empleados de {oficina_seleccionada} ({len(empleados)} personas)")
    
    # Verificar si ya hay registros para esta fecha
    df_asistencias = sheets.get_dataframe("asistencias")
    if not df_asistencias.empty and 'fecha' in df_asistencias.columns and 'oficina' in df_asistencias.columns:
        asistencias_fecha = df_asistencias[
            (df_asistencias['fecha'] == format_date(fecha_registro)) &
            (df_asistencias['oficina'] == oficina_seleccionada)
        ]
        
        if not asistencias_fecha.empty:
            st.warning(f"⚠️ Ya existen {len(asistencias_fecha)} registros para esta fecha. Puedes agregar más o editarlos.")
    
    # Formulario de registro
    with st.form("form_asistencias", clear_on_submit=True):
        registros = []
        
        for idx, emp in empleados.iterrows():
            col1, col2, col3, col4 = st.columns([3, 2, 2, 3])
            
            with col1:
                st.write(f"**{emp['nombre_completo']}**")
                st.caption(f"ID: {emp['id_empleado']}")
            
            with col2:
                estado = st.selectbox(
                    "Estado",
                    ["Presente", "Ausente", "Retardo", "Permiso", "Incapacidad"],
                    key=f"estado_{emp['id_empleado']}",
                    label_visibility="collapsed"
                )
            
            with col3:
                if estado == "Presente" or estado == "Retardo":
                    hora = st.time_input(
                        "Hora",
                        value=datetime.strptime("08:00", "%H:%M").time(),
                        key=f"hora_{emp['id_empleado']}",
                        label_visibility="collapsed"
                    )
                else:
                    hora = None
            
            with col4:
                observaciones = st.text_input(
                    "Observaciones",
                    key=f"obs_{emp['id_empleado']}",
                    placeholder="Opcional...",
                    label_visibility="collapsed"
                )
            
            registros.append({
                'id_empleado': emp['id_empleado'],
                'nombre': emp['nombre_completo'],
                'estado': estado,
                'hora': hora,
                'observaciones': observaciones
            })
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            submit = st.form_submit_button(
                "💾 Guardar Asistencias",
                use_container_width=True,
                type="primary"
            )
        
        if submit:
            guardar_asistencias(
                registros, 
                fecha_registro, 
                oficina_seleccionada, 
                es_sabado,
                user, 
                sheets
            )

def guardar_asistencias(registros, fecha, oficina, es_sabado, user, sheets):
    """Guarda los registros de asistencia en Google Sheets"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        contador_guardados = 0
        
        with st.spinner("💾 Guardando asistencias..."):
            for reg in registros:
                # Solo guardar si tiene estado válido
                if reg['estado'] in ["Presente", "Retardo", "Ausente", "Permiso", "Incapacidad"]:
                    
                    next_id = sheets.get_next_id("asistencias")
                    
                    hora_str = format_time(reg['hora']) if reg['hora'] else ""
                    
                    datos = [
                        next_id,
                        reg['id_empleado'],
                        format_date(fecha),
                        hora_str,
                        reg['estado'],
                        "SI" if es_sabado else "NO",
                        oficina,
                        user['email'],
                        timestamp,
                        "local",
                        reg['observaciones'],
                        ""
                    ]
                    
                    if sheets.append_row("asistencias", datos):
                        contador_guardados += 1
                        
                        sheets.log_action(
                            usuario=user['email'],
                            accion="registro_asistencia",
                            modulo="asistencias",
                            detalles=f"Empleado: {reg['nombre']}, Estado: {reg['estado']}, Fecha: {format_date(fecha)}",
                            id_registro=next_id
                        )
        
        if contador_guardados > 0:
            st.success(f"✅ {contador_guardados} asistencias registradas correctamente")
            st.balloons()
            st.rerun()
        else:
            st.warning("⚠️ No se guardó ningún registro")
            
    except Exception as e:
        st.error(f"❌ Error al guardar asistencias: {e}")

def ver_asistencias(user, sheets):
    """Visualiza asistencias registradas"""
    st.subheader("📊 Consultar Asistencias")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        fecha_inicio = st.date_input(
            "Fecha inicio",
            value=date.today() - timedelta(days=7)
        )
    
    with col2:
        fecha_fin = st.date_input(
            "Fecha fin",
            value=date.today()
        )
    
    with col3:
        if user['rol'] == 'registrador':
            oficina_filtro = user['oficina']
            st.info(f"Oficina: {oficina_filtro}")
        else:
            oficinas_list = get_oficinas_list(sheets)
            if oficinas_list:
                oficinas = ["Todas"] + oficinas_list
                oficina_filtro = st.selectbox("Oficina", oficinas, key="filtro_oficina_ver")
            else:
                oficina_filtro = "Todas"
                st.warning("No hay oficinas disponibles")
    
    # Obtener datos
    df_asistencias = sheets.get_dataframe("asistencias")
    df_empleados = sheets.get_dataframe("empleados")
    
    if df_asistencias.empty:
        st.info("ℹ️ No hay asistencias registradas aún")
        return
    
    # Filtrar por fechas
    df_asistencias['fecha'] = pd.to_datetime(df_asistencias['fecha'])
    mask_fechas = (
        (df_asistencias['fecha'] >= pd.to_datetime(fecha_inicio)) &
        (df_asistencias['fecha'] <= pd.to_datetime(fecha_fin))
    )
    df_filtrado = df_asistencias[mask_fechas]
    
    # Filtrar por oficina
    if oficina_filtro != "Todas" and 'oficina' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['oficina'] == oficina_filtro]
    
    if not df_filtrado.empty:
        # Merge con empleados para mostrar nombres
        if not df_empleados.empty:
            df_merged = df_filtrado.merge(
                df_empleados[['id_empleado', 'nombre_completo']], 
                on='id_empleado',
                how='left'
            )
        else:
            df_merged = df_filtrado.copy()
        
        # Ordenar por fecha descendente
        df_merged = df_merged.sort_values('fecha', ascending=False)
        
        # Mostrar métricas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total registros", len(df_merged))
        with col2:
            if 'estado' in df_merged.columns:
                presentes = len(df_merged[df_merged['estado'] == 'Presente'])
                st.metric("Presentes", presentes)
        with col3:
            if 'estado' in df_merged.columns:
                ausentes = len(df_merged[df_merged['estado'] == 'Ausente'])
                st.metric("Ausentes", ausentes)
        with col4:
            if 'es_sabado' in df_merged.columns:
                sabados = len(df_merged[df_merged['es_sabado'] == 'SI'])
                st.metric("Sábados trabajados", sabados)
        
        st.markdown("---")
        
        # Mostrar tabla con columnas disponibles
        columnas_disponibles = df_merged.columns.tolist()
        columnas_mostrar = [col for col in ['fecha', 'nombre_completo', 'estado', 'hora_registro', 'oficina', 'es_sabado', 'observaciones', 'registrado_por'] if col in columnas_disponibles]
        
        if columnas_mostrar:
            df_display = df_merged[columnas_mostrar].copy()
            df_display['fecha'] = df_display['fecha'].dt.strftime('%Y-%m-%d')
            
            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True
            )
            
            # Opción de descargar
            csv = df_display.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar CSV",
                data=csv,
                file_name=f"asistencias_{fecha_inicio}_{fecha_fin}.csv",
                mime="text/csv"
            )
    else:
        st.info("ℹ️ No hay registros en el rango de fechas seleccionado")

def mostrar_estadisticas(user, sheets):
    """Muestra estadísticas de asistencias"""
    st.subheader("📈 Estadísticas de Asistencias")
    
    df_asistencias = sheets.get_dataframe("asistencias")
    df_empleados = sheets.get_dataframe("empleados")
    
    if df_asistencias.empty:
        st.info("ℹ️ No hay datos para mostrar estadísticas")
        return
    
    # Filtros
    col1, col2 = st.columns(2)
    with col1:
        year = st.selectbox("Año", [2024, 2025, 2026], index=1, key="year_stats")
    with col2:
        if user['rol'] == 'registrador':
            oficina = user['oficina']
            st.info(f"Oficina: {oficina}")
        else:
            oficinas_list = get_oficinas_list(sheets)
            if oficinas_list:
                oficinas = ["Todas"] + oficinas_list
                oficina = st.selectbox("Oficina", oficinas, key="filtro_oficina_stats")
            else:
                oficina = "Todas"
                st.warning("No hay oficinas disponibles")
    
    # Filtrar datos
    df_asistencias['fecha'] = pd.to_datetime(df_asistencias['fecha'])
    df_year = df_asistencias[df_asistencias['fecha'].dt.year == year]
    
    if oficina != "Todas" and 'oficina' in df_year.columns:
        df_year = df_year[df_year['oficina'] == oficina]
    
    if not df_year.empty:
        # Métricas generales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_registros = len(df_year)
            st.metric("📋 Total Registros", total_registros)
        
        with col2:
            if 'estado' in df_year.columns:
                tasa_asistencia = len(df_year[df_year['estado'] == 'Presente']) / len(df_year) * 100
                st.metric("✅ Tasa Asistencia", f"{tasa_asistencia:.1f}%")
        
        with col3:
            if 'es_sabado' in df_year.columns:
                total_sabados = len(df_year[df_year['es_sabado'] == 'SI'])
                st.metric("📅 Sábados Trabajados", total_sabados)
        
        with col4:
            if 'estado' in df_year.columns:
                total_retardos = len(df_year[df_year['estado'] == 'Retardo'])
                st.metric("⏰ Retardos", total_retardos)
        
        st.markdown("---")
        
        # Top empleados por asistencia
        if not df_empleados.empty and 'estado' in df_year.columns:
            st.subheader("🏆 Top 10 - Mejor Asistencia")
            
            df_top = df_year[df_year['estado'] == 'Presente'].groupby('id_empleado').size().reset_index(name='dias_presente')
            df_top = df_top.merge(df_empleados[['id_empleado', 'nombre_completo', 'oficina']], on='id_empleado')
            df_top = df_top.sort_values('dias_presente', ascending=False).head(10)
            
            st.dataframe(
                df_top[['nombre_completo', 'oficina', 'dias_presente']],
                use_container_width=True,
                hide_index=True
            )
    else:
        st.info("ℹ️ No hay datos para el año seleccionado")