from datetime import datetime, date
import pandas as pd

def format_date(date_obj):
    """Formatea fecha a string YYYY-MM-DD"""
    if isinstance(date_obj, str):
        return date_obj
    return date_obj.strftime("%Y-%m-%d")

def format_datetime(dt_obj):
    """Formatea datetime a string YYYY-MM-DD HH:MM:SS"""
    if isinstance(dt_obj, str):
        return dt_obj
    return dt_obj.strftime("%Y-%m-%d %H:%M:%S")

def format_time(time_obj):
    """Formatea time a string HH:MM:SS"""
    if isinstance(time_obj, str):
        return time_obj
    return time_obj.strftime("%H:%M:%S")

def get_current_year():
    """Retorna el año actual"""
    return datetime.now().year

def is_saturday(date_obj):
    """Verifica si una fecha es sábado"""
    if isinstance(date_obj, str):
        date_obj = datetime.strptime(date_obj, "%Y-%m-%d").date()
    return date_obj.weekday() == 5

def calculate_days_between(start_date, end_date):
    """Calcula días entre dos fechas (inclusive)"""
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    
    return (end_date - start_date).days + 1

def get_year_progress():
    """Retorna el progreso del año actual (0-1)"""
    today = datetime.now()
    start_year = datetime(today.year, 1, 1)
    end_year = datetime(today.year, 12, 31)
    
    total_days = (end_year - start_year).days
    elapsed_days = (today - start_year).days
    
    return elapsed_days / total_days

def calculate_permisos_disponibles(id_empleado, df_permisos):
    """Calcula días de permiso disponibles para un empleado"""
    year = get_current_year()
    
    # Filtrar permisos aprobados del año actual
    permisos_year = df_permisos[
        (df_permisos['id_empleado'] == id_empleado) &
        (df_permisos['estado'] == 'Aprobado') &
        (pd.to_datetime(df_permisos['fecha_inicio']).dt.year == year)
    ]
    
    dias_usados = permisos_year['dias_solicitados'].sum() if not permisos_year.empty else 0
    return max(0, 9 - dias_usados)

def calculate_sabados_trabajados(id_empleado, df_asistencias, periodo=None):
    """Calcula sábados trabajados por un empleado"""
    if periodo:
        # Filtrar por periodo específico
        asistencias = df_asistencias[
            (df_asistencias['id_empleado'] == id_empleado) &
            (df_asistencias['es_sabado'] == 'SI') &
            (df_asistencias['estado'] == 'Presente')
        ]
    else:
        # Todo el año actual
        year = get_current_year()
        asistencias = df_asistencias[
            (df_asistencias['id_empleado'] == id_empleado) &
            (df_asistencias['es_sabado'] == 'SI') &
            (df_asistencias['estado'] == 'Presente') &
            (pd.to_datetime(df_asistencias['fecha']).dt.year == year)
        ]
    
    return len(asistencias)

def get_employee_stats(id_empleado, sheets_manager):
    """Obtiene estadísticas generales de un empleado"""
    year = get_current_year()
    
    # Obtener datos
    df_asistencias = sheets_manager.get_dataframe("asistencias")
    df_permisos = sheets_manager.get_dataframe("permisos")
    df_incapacidades = sheets_manager.get_dataframe("incapacidades")
    
    # Filtrar por empleado y año actual
    asistencias_year = df_asistencias[
        (df_asistencias['id_empleado'] == id_empleado) &
        (pd.to_datetime(df_asistencias['fecha']).dt.year == year)
    ]
    
    stats = {
        'dias_asistencia': len(asistencias_year[asistencias_year['estado'] == 'Presente']),
        'dias_ausencia': len(asistencias_year[asistencias_year['estado'] == 'Ausente']),
        'retardos': len(asistencias_year[asistencias_year['estado'] == 'Retardo']),
        'sabados_trabajados': calculate_sabados_trabajados(id_empleado, df_asistencias),
        'permisos_disponibles': calculate_permisos_disponibles(id_empleado, df_permisos),
        'incapacidades': len(df_incapacidades[
            (df_incapacidades['id_empleado'] == id_empleado) &
            (pd.to_datetime(df_incapacidades['fecha_inicio']).dt.year == year)
        ])
    }
    
    return stats

def validate_date_range(start_date, end_date):
    """Valida que un rango de fechas sea válido"""
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    
    if start_date > end_date:
        return False, "La fecha de inicio no puede ser posterior a la fecha de fin"
    
    return True, ""

def get_oficinas_list(sheets_manager):
    """Obtiene lista de oficinas únicas"""
    df_empleados = sheets_manager.get_dataframe("empleados")
    if not df_empleados.empty:
        return sorted(df_empleados['oficina'].unique().tolist())
    return []

def get_empleados_by_oficina(oficina, sheets_manager):
    """Obtiene empleados de una oficina específica"""
    df_empleados = sheets_manager.get_dataframe("empleados")
    empleados = df_empleados[
        (df_empleados['oficina'] == oficina) &
        (df_empleados['activo'] == 'SI')
    ]
    return empleados.sort_values('nombre_completo')