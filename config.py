import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

class DualManager:
    """Gestor que usa Supabase como principal y Sheets como backup"""
    
    def __init__(self):
        self.supabase = self._init_supabase()
        self.sheets = self._init_sheets()
    
    @st.cache_resource
    def _init_supabase(_self):
        """Conectar a Supabase"""
        return create_client(
            st.secrets["supabase"]["url"],
            st.secrets["supabase"]["key"]
        )
    
    def _init_sheets(self):
        """Conectar a Google Sheets (para sync)"""
        try:
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(
                dict(st.secrets["gcp_service_account"]), 
                scope
            )
            client = gspread.authorize(creds)
            return client.open_by_url(st.secrets["sheets"]["spreadsheet_url"])
        except:
            return None
    
    # ==================== LECTURA (Supabase) ====================
    
    @st.cache_data(ttl=30)
    def get_dataframe(_self, table_name):
        """Leer desde Supabase (rápido, sin límites)"""
        try:
            response = _self.supabase.table(table_name).select("*").execute()
            return pd.DataFrame(response.data)
        except Exception as e:
            st.error(f"Error al leer {table_name}: {e}")
            return pd.DataFrame()
    
    # ==================== ESCRITURA (Supabase) ====================
    
    def append_row(self, table_name, data_dict):
        """Guardar en Supabase (marca como no sincronizado)"""
        try:
            data_dict['sincronizado'] = False
            self.supabase.table(table_name).insert(data_dict).execute()
            st.cache_data.clear()
            return True
        except Exception as e:
            st.error(f"Error al guardar en {table_name}: {e}")
            return False
    
    def get_next_id(self, table_name):
        """Siguiente ID (Supabase lo hace automático)"""
        return None  # Supabase usa SERIAL
    
    # ==================== SINCRONIZACIÓN ====================
    
    def sincronizar_a_sheets(self):
        """Exportar asistencias a Google Sheets"""
        return self.sync_to_sheets(tabla="asistencias")
    
    def sync_to_sheets(self, tabla="asistencias"):
        """Exportar registros no sincronizados a Google Sheets (genérico)"""
        if not self.sheets:
            return {"success": False, "mensaje": "Google Sheets no configurado", "sincronizados": 0}
        
        try:
            # Obtener registros no sincronizados
            response = self.supabase.table(tabla).select("*").eq('sincronizado', False).execute()
            pendientes = response.data
            
            if not pendientes:
                return {"success": True, "mensaje": "No hay registros pendientes", "sincronizados": 0}
            
            # Determinar estructura según tabla
            if tabla == "asistencias":
                worksheet = self.sheets.worksheet('asistencias')
                for registro in pendientes:
                    fila = [
                        registro.get('id'),
                        registro.get('id_empleado'),
                        registro.get('fecha'),
                        registro.get('hora_registro'),
                        registro.get('estado'),
                        registro.get('es_sabado'),
                        registro.get('oficina'),
                        registro.get('registrado_por'),
                        registro.get('timestamp_sistema'),
                        registro.get('ip_registro'),
                        registro.get('observaciones'),
                    ]
                    worksheet.append_row(fila)
                    
                    # Marcar como sincronizado
                    self.supabase.table(tabla).update({
                        'sincronizado': True
                    }).eq('id', registro['id']).execute()
            
            elif tabla == "permisos":
                worksheet = self.sheets.worksheet('permisos')
                for registro in pendientes:
                    fila = [
                        registro.get('id'),
                        registro.get('id_empleado'),
                        registro.get('fecha_inicio'),
                        registro.get('fecha_fin'),
                        registro.get('dias_solicitados'),
                        registro.get('motivo'),
                        registro.get('estado'),
                        registro.get('aprobado_por'),
                        registro.get('fecha_aprobacion'),
                        registro.get('comentario_aprobacion'),
                        registro.get('oficina'),
                        registro.get('solicitado_por'),
                        registro.get('timestamp_creacion'),
                    ]
                    worksheet.append_row(fila)
                    
                    # Marcar como sincronizado
                    self.supabase.table(tabla).update({
                        'sincronizado': True
                    }).eq('id', registro['id']).execute()
            
            elif tabla == "incapacidades":
                worksheet = self.sheets.worksheet('incapacidades')
                for registro in pendientes:
                    fila = [
                        registro.get('id'),
                        registro.get('id_empleado'),
                        registro.get('tipo'),
                        registro.get('fecha_inicio'),
                        registro.get('fecha_fin'),
                        registro.get('dias_totales'),
                        registro.get('motivo'),
                        registro.get('folio'),
                        registro.get('institucion'),
                        registro.get('documento_url'),
                        registro.get('oficina'),
                        registro.get('registrado_por'),
                        registro.get('timestamp_creacion'),
                    ]
                    worksheet.append_row(fila)
                    
                    # Marcar como sincronizado
                    self.supabase.table(tabla).update({
                        'sincronizado': True
                    }).eq('id', registro['id']).execute()
            
            return {"success": True, "mensaje": f"{len(pendientes)} registros sincronizados", "sincronizados": len(pendientes)}
            
        except Exception as e:
            return {"success": False, "mensaje": f"Error: {e}", "sincronizados": 0}
    
    def log_action(self, usuario, accion, modulo, detalles, id_registro=None):
        """Log de auditoría"""
        try:
            self.supabase.table('auditoria').insert({
                'timestamp': datetime.now().isoformat(),
                'usuario': usuario,
                'accion': accion,
                'modulo': modulo,
                'detalles': detalles,
                'ip': 'local'
            }).execute()
        except:
            pass

@st.cache_resource
def get_sheets_manager():
    """Instancia única del gestor dual"""
    return DualManager()