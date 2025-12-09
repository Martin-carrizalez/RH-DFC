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
        self._cache_version = 0  # Control de versión de caché
    
    @staticmethod
    @st.cache_resource
    def _init_supabase():
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
    
    def get_dataframe(self, table_name):
        """Leer desde Supabase con caché mejorado"""
        # Usar función cacheada interna
        return self._get_dataframe_cached(table_name, self._cache_version)
    
    @staticmethod
    @st.cache_data(ttl=60, show_spinner=False)
    def _get_dataframe_cached(table_name, _cache_version):
        """Función interna cacheada con control de versión"""
        try:
            # Obtener instancia de supabase directamente
            supabase = create_client(
                st.secrets["supabase"]["url"],
                st.secrets["supabase"]["key"]
            )
            response = supabase.table(table_name).select("*").execute()
            return pd.DataFrame(response.data)
        except Exception as e:
            st.error(f"Error al leer {table_name}: {e}")
            return pd.DataFrame()
    
    def invalidate_cache(self):
        """Invalidar caché incrementando la versión"""
        self._cache_version += 1
        # También limpiar el caché general
        st.cache_data.clear()
    
    # ==================== ESCRITURA (Supabase) ====================
    
    def append_row(self, table_name, data_dict):
        """Guardar en Supabase (marca como no sincronizado)"""
        try:
            data_dict['sincronizado'] = False
            self.supabase.table(table_name).insert(data_dict).execute()
            
            # CRÍTICO: Invalidar caché después de insertar
            self.invalidate_cache()
            return True
        except Exception as e:
            st.error(f"Error al guardar en {table_name}: {e}")
            return False
    
    def update_row(self, table_name, row_id, data_dict):
        """Actualizar registro en Supabase"""
        try:
            self.supabase.table(table_name).update(data_dict).eq('id', row_id).execute()
            
            # Invalidar caché después de actualizar
            self.invalidate_cache()
            return True
        except Exception as e:
            st.error(f"Error al actualizar en {table_name}: {e}")
            return False
    
    def delete_row(self, table_name, row_id):
        """Eliminar registro en Supabase"""
        try:
            self.supabase.table(table_name).delete().eq('id', row_id).execute()
            
            # Invalidar caché después de eliminar
            self.invalidate_cache()
            return True
        except Exception as e:
            st.error(f"Error al eliminar en {table_name}: {e}")
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
            # Obtener registros no sincronizados directamente (sin caché)
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
            
            # Invalidar caché después de sincronizar
            self.invalidate_cache()
            
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
            # No invalidar caché para logs (no son consultados frecuentemente)
        except:
            pass

@st.cache_resource
def get_sheets_manager():
    """Instancia única del gestor dual"""
    return DualManager()