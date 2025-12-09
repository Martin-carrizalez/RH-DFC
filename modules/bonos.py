import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from config import get_sheets_manager
import calendar

def show_bonos_module():
    """Módulo de cálculo de bonos"""
    user_data = st.session_state.get('user_data', {})
    rol = user_data.get('rol', '')
    
    st.title("💰 Cálculo de Bonos")
    st.caption("Sistema de bonificaciones basado en asistencia y desempeño")
    
    # Solo admin y supervisora pueden calcular bonos
    if rol not in ['admin', 'supervisora']:
        st.error("❌ No tienes permisos para acceder a este módulo")
        return
    
    # Tabs del módulo
    tabs = st.tabs(["📊 Calcular Bonos", "📋 Historial", "⚙️ Configuración"])
    
    with tabs[0]:
        calcular_bonos(user_data)
    
    with tabs[1]:
        ver_historial_bonos(user_data)
    
    with tabs[2]:
        configurar_bonos(user_data)


def calcular_bonos(user_data):
    """Calcular bonos del mes"""
    st.subheader("Calcular Bonos Mensuales")
    
    manager = get_sheets_manager()
    
    # Seleccionar periodo
    col1, col2, col3 = st.columns(3)
    
    with col1:
        año = st.selectbox(
            "Año",
            range(datetime.now().year, datetime.now().year - 3, -1),
            key="bonos_año"
        )
    
    with col2:
        meses = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]
        mes_nombre = st.selectbox("Mes", meses, key="bonos_mes")
        mes = meses.index(mes_nombre) + 1
    
    with col3:
        oficinas_list = ["Todas", "Norte", "Sur", "Este", "Oeste", "Centro"] + [f"Zona {i}" for i in range(1, 11)]
        oficina_filtro = st.selectbox("Oficina", oficinas_list, key="bonos_oficina")
    
    if st.button("🔍 Calcular Bonos del Periodo", type="primary", use_container_width=True):
        with st.spinner("Calculando bonos..."):
            calcular_bonos_periodo(manager, año, mes, oficina_filtro, user_data)


def calcular_bonos_periodo(manager, año, mes, oficina_filtro, user_data):
    """Calcular bonos de un periodo específico"""
    try:
        # Obtener configuración de bonos
        config = obtener_configuracion_bonos(manager)
        
        # Obtener empleados
        df_empleados = manager.get_dataframe("empleados")
        df_empleados = df_empleados[df_empleados['activo'].str.upper() == 'SI']
        
        if oficina_filtro != "Todas":
            df_empleados = df_empleados[df_empleados['oficina'] == oficina_filtro]
        
        if df_empleados.empty:
            st.warning("⚠️ No hay empleados activos en la oficina seleccionada")
            return
        
        # Obtener asistencias del mes
        df_asistencias = manager.get_dataframe("asistencias")
        
        # Filtrar asistencias del periodo
        fecha_inicio = f"{año}-{mes:02d}-01"
        ultimo_dia = calendar.monthrange(año, mes)[1]
        fecha_fin = f"{año}-{mes:02d}-{ultimo_dia}"
        
        df_asistencias = df_asistencias[
            (df_asistencias['fecha'] >= fecha_inicio) &
            (df_asistencias['fecha'] <= fecha_fin)
        ]
        
        # Calcular bonos por empleado
        resultados = []
        
        for _, empleado in df_empleados.iterrows():
            id_empleado = empleado['id_empleado']
            
            # Asistencias del empleado
            asistencias_emp = df_asistencias[df_asistencias['id_empleado'] == id_empleado]
            
            # Contar por estado
            total_dias = len(asistencias_emp)
            presentes = len(asistencias_emp[asistencias_emp['estado'] == 'Presente'])
            retardos = len(asistencias_emp[asistencias_emp['estado'] == 'Retardo'])
            ausentes = len(asistencias_emp[asistencias_emp['estado'] == 'Ausente'])
            
            # Calcular bono
            bono = calcular_monto_bono(
                presentes, retardos, ausentes, config
            )
            
            resultados.append({
                'id_empleado': id_empleado,
                'nombre_completo': empleado['nombre_completo'],
                'oficina': empleado['oficina'],
                'dias_trabajados': total_dias,
                'presentes': presentes,
                'retardos': retardos,
                'ausentes': ausentes,
                'monto_bono': bono,
                'periodo': f"{año}-{mes:02d}",
                'año': año,
                'mes': mes
            })
        
        df_resultados = pd.DataFrame(resultados)
        
        # Mostrar resultados
        st.success(f"✅ Bonos calculados para {len(df_resultados)} empleados")
        
        # Métricas generales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Empleados", len(df_resultados))
        
        with col2:
            total_bonos = df_resultados['monto_bono'].sum()
            st.metric("Total Bonos", f"${total_bonos:,.2f}")
        
        with col3:
            promedio = df_resultados['monto_bono'].mean()
            st.metric("Promedio", f"${promedio:,.2f}")
        
        with col4:
            con_bono = len(df_resultados[df_resultados['monto_bono'] > 0])
            st.metric("Con Bono", con_bono)
        
        # Tabla de resultados
        st.markdown("---")
        st.subheader("Detalle de Bonos")
        
        # Formatear para mostrar
        df_mostrar = df_resultados.copy()
        df_mostrar['monto_bono'] = df_mostrar['monto_bono'].apply(lambda x: f"${x:,.2f}")
        
        columnas_mostrar = {
            'nombre_completo': 'Empleado',
            'oficina': 'Oficina',
            'presentes': 'Presentes',
            'retardos': 'Retardos',
            'ausentes': 'Ausentes',
            'monto_bono': 'Bono'
        }
        
        df_tabla = df_mostrar[list(columnas_mostrar.keys())].rename(columns=columnas_mostrar)
        
        st.dataframe(df_tabla, use_container_width=True, height=400)
        
        # Botón para guardar bonos
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("💾 Guardar Bonos Calculados", type="primary", use_container_width=True):
                guardar_bonos_calculados(manager, df_resultados, user_data)
        
        with col_btn2:
            # Exportar a CSV
            csv = df_mostrar.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Exportar a CSV",
                csv,
                f"bonos_{año}_{mes:02d}.csv",
                "text/csv",
                use_container_width=True
            )
    
    except Exception as e:
        st.error(f"❌ Error al calcular bonos: {e}")


def calcular_monto_bono(presentes, retardos, ausentes, config):
    """Calcular monto de bono según configuración"""
    # Obtener valores de configuración
    bono_base = config.get('bono_base', 1000)
    penalizacion_retardo = config.get('penalizacion_retardo', 50)
    penalizacion_ausencia = config.get('penalizacion_ausencia', 200)
    asistencias_minimas = config.get('asistencias_minimas', 20)
    
    # Si no cumple asistencias mínimas, no hay bono
    if presentes < asistencias_minimas:
        return 0
    
    # Calcular bono
    bono = bono_base
    bono -= (retardos * penalizacion_retardo)
    bono -= (ausentes * penalizacion_ausencia)
    
    # El bono no puede ser negativo
    return max(0, bono)


def guardar_bonos_calculados(manager, df_bonos, user_data):
    """Guardar bonos calculados en Supabase"""
    try:
        guardados = 0
        
        for _, bono in df_bonos.iterrows():
            # Verificar si ya existe
            año = bono['año']
            mes = bono['mes']
            id_empleado = bono['id_empleado']
            
            # Buscar si ya existe
            df_existentes = manager.get_dataframe("bonos")
            existe = df_existentes[
                (df_existentes['id_empleado'] == id_empleado) &
                (df_existentes['año'] == año) &
                (df_existentes['mes'] == mes)
            ]
            
            if not existe.empty:
                # Actualizar
                manager.supabase.table("bonos").update({
                    'dias_trabajados': int(bono['dias_trabajados']),
                    'presentes': int(bono['presentes']),
                    'retardos': int(bono['retardos']),
                    'ausentes': int(bono['ausentes']),
                    'monto_bono': float(bono['monto_bono']),
                    'calculado_por': user_data['email'],
                    'fecha_calculo': datetime.now().isoformat()
                }).eq('id', existe.iloc[0]['id']).execute()
            else:
                # Insertar nuevo
                bono_data = {
                    'id_empleado': id_empleado,
                    'periodo': bono['periodo'],
                    'año': int(año),
                    'mes': int(mes),
                    'dias_trabajados': int(bono['dias_trabajados']),
                    'presentes': int(bono['presentes']),
                    'retardos': int(bono['retardos']),
                    'ausentes': int(bono['ausentes']),
                    'monto_bono': float(bono['monto_bono']),
                    'oficina': bono['oficina'],
                    'calculado_por': user_data['email'],
                    'fecha_calculo': datetime.now().isoformat()
                }
                
                manager.supabase.table("bonos").insert(bono_data).execute()
            
            guardados += 1
        
        st.success(f"✅ {guardados} bonos guardados correctamente")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error al guardar bonos: {e}")


def ver_historial_bonos(user_data):
    """Ver historial de bonos calculados"""
    st.subheader("Historial de Bonos")
    
    manager = get_sheets_manager()
    
    try:
        df_bonos = manager.get_dataframe("bonos")
        
        if df_bonos.empty:
            st.info("🔭 No hay bonos registrados")
            return
        
        # Obtener nombres de empleados
        df_empleados = manager.get_dataframe("empleados")
        df_bonos = df_bonos.merge(
            df_empleados[['id_empleado', 'nombre_completo']],
            on='id_empleado',
            how='left'
        )
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        
        with col1:
            años = ["Todos"] + sorted(df_bonos['año'].unique().tolist(), reverse=True)
            año_filtro = st.selectbox("Año", años, key="bonos_hist_año")
        
        with col2:
            meses_dict = {
                1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
                5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
                9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
            }
            mes_filtro = st.selectbox(
                "Mes",
                ["Todos"] + [meses_dict[m] for m in sorted(df_bonos['mes'].unique().tolist())],
                key="bonos_hist_mes"
            )
        
        with col3:
            oficinas = ["Todas"] + sorted(df_bonos['oficina'].unique().tolist())
            oficina_filtro = st.selectbox("Oficina", oficinas, key="bonos_hist_oficina")
        
        # Aplicar filtros
        df_filtrado = df_bonos.copy()
        
        if año_filtro != "Todos":
            df_filtrado = df_filtrado[df_filtrado['año'] == año_filtro]
        
        if mes_filtro != "Todos":
            mes_num = [k for k, v in meses_dict.items() if v == mes_filtro][0]
            df_filtrado = df_filtrado[df_filtrado['mes'] == mes_num]
        
        if oficina_filtro != "Todas":
            df_filtrado = df_filtrado[df_filtrado['oficina'] == oficina_filtro]
        
        # Estadísticas
        col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
        
        with col_stats1:
            st.metric("Total Registros", len(df_filtrado))
        
        with col_stats2:
            total_pagado = df_filtrado['monto_bono'].sum()
            st.metric("Total Pagado", f"${total_pagado:,.2f}")
        
        with col_stats3:
            promedio = df_filtrado['monto_bono'].mean()
            st.metric("Promedio", f"${promedio:,.2f}")
        
        with col_stats4:
            con_bono = len(df_filtrado[df_filtrado['monto_bono'] > 0])
            st.metric("Con Bono", con_bono)
        
        # Tabla
        if df_filtrado.empty:
            st.info("🔭 No hay bonos con los filtros seleccionados")
        else:
            df_mostrar = df_filtrado.copy()
            df_mostrar['monto_bono'] = df_mostrar['monto_bono'].apply(lambda x: f"${x:,.2f}")
            df_mostrar['periodo_str'] = df_mostrar['año'].astype(str) + '-' + df_mostrar['mes'].astype(str).str.zfill(2)
            
            columnas_mostrar = {
                'nombre_completo': 'Empleado',
                'periodo_str': 'Periodo',
                'oficina': 'Oficina',
                'presentes': 'Presentes',
                'retardos': 'Retardos',
                'ausentes': 'Ausentes',
                'monto_bono': 'Bono'
            }
            
            df_tabla = df_mostrar[list(columnas_mostrar.keys())].rename(columns=columnas_mostrar)
            
            st.dataframe(df_tabla, use_container_width=True, height=400)
            
            # Exportar
            csv = df_tabla.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Exportar a CSV",
                csv,
                f"historial_bonos_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv",
                use_container_width=True,
                key="bonos_hist_download"
            )
    
    except Exception as e:
        st.error(f"❌ Error: {e}")


def configurar_bonos(user_data):
    """Configurar parámetros de bonos"""
    st.subheader("Configuración de Bonos")
    
    if user_data['rol'] != 'admin':
        st.warning("⚠️ Solo el administrador puede modificar la configuración")
        return
    
    manager = get_sheets_manager()
    
    # Obtener configuración actual
    config = obtener_configuracion_bonos(manager)
    
    st.info("💡 Define los parámetros para el cálculo de bonos mensuales")
    
    with st.form("config_bonos"):
        col1, col2 = st.columns(2)
        
        with col1:
            bono_base = st.number_input(
                "Bono Base ($)",
                min_value=0,
                value=int(config.get('bono_base', 1000)),
                step=100,
                help="Monto base del bono mensual"
            )
            
            asistencias_minimas = st.number_input(
                "Asistencias Mínimas",
                min_value=1,
                value=int(config.get('asistencias_minimas', 20)),
                step=1,
                help="Días mínimos de asistencia para obtener bono"
            )
        
        with col2:
            penalizacion_retardo = st.number_input(
                "Penalización por Retardo ($)",
                min_value=0,
                value=int(config.get('penalizacion_retardo', 50)),
                step=10,
                help="Descuento por cada retardo"
            )
            
            penalizacion_ausencia = st.number_input(
                "Penalización por Ausencia ($)",
                min_value=0,
                value=int(config.get('penalizacion_ausencia', 200)),
                step=50,
                help="Descuento por cada ausencia"
            )
        
        st.markdown("---")
        st.markdown("### 📋 Ejemplo de Cálculo")
        
        col_ej1, col_ej2 = st.columns(2)
        
        with col_ej1:
            st.write("**Escenario 1: Asistencia perfecta**")
            st.write(f"- 22 días presentes")
            st.write(f"- 0 retardos")
            st.write(f"- 0 ausencias")
            ejemplo_1 = bono_base
            st.success(f"**Bono: ${ejemplo_1:,.2f}**")
        
        with col_ej2:
            st.write("**Escenario 2: Con penalizaciones**")
            st.write(f"- 20 días presentes")
            st.write(f"- 2 retardos")
            st.write(f"- 1 ausencia")
            ejemplo_2 = bono_base - (2 * penalizacion_retardo) - (1 * penalizacion_ausencia)
            if ejemplo_2 < 0:
                ejemplo_2 = 0
            st.warning(f"**Bono: ${ejemplo_2:,.2f}**")
        
        submit = st.form_submit_button("💾 Guardar Configuración", type="primary", use_container_width=True)
        
        if submit:
            try:
                config_data = {
                    'bono_base': bono_base,
                    'penalizacion_retardo': penalizacion_retardo,
                    'penalizacion_ausencia': penalizacion_ausencia,
                    'asistencias_minimas': asistencias_minimas,
                    'modificado_por': user_data['email'],
                    'fecha_modificacion': datetime.now().isoformat()
                }
                
                # Verificar si existe configuración
                df_config = manager.get_dataframe("config_bonos")
                
                if df_config.empty:
                    # Crear nueva
                    manager.supabase.table("config_bonos").insert(config_data).execute()
                else:
                    # Actualizar existente
                    manager.supabase.table("config_bonos").update(config_data).eq('id', df_config.iloc[0]['id']).execute()
                
                st.success("✅ Configuración guardada correctamente")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error al guardar: {e}")


def obtener_configuracion_bonos(manager):
    """Obtener configuración de bonos desde Supabase"""
    try:
        df_config = manager.get_dataframe("config_bonos")
        
        if df_config.empty:
            # Valores por defecto
            return {
                'bono_base': 1000,
                'penalizacion_retardo': 50,
                'penalizacion_ausencia': 200,
                'asistencias_minimas': 20
            }
        
        return df_config.iloc[0].to_dict()
        
    except:
        # Si hay error, retornar valores por defecto
        return {
            'bono_base': 1000,
            'penalizacion_retardo': 50,
            'penalizacion_ausencia': 200,
            'asistencias_minimas': 20
        }