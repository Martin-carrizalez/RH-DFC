import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime, timedelta

class SheetsManager:
    """Gestor de conexión y operaciones con Google Sheets"""
    
    def __init__(self):
        self.scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        self.credentials = None
        self.client = None
        self.spreadsheet = None
        self._connect()
        self._init_cache()
    
    def _init_cache(self):
        """Inicializa el sistema de caché en session_state"""
        if 'sheets_cache' not in st.session_state:
            st.session_state.sheets_cache = {}
        if 'cache_timestamps' not in st.session_state:
            st.session_state.cache_timestamps = {}
    
    def _connect(self):
        """Establece conexión con Google Sheets"""
        try:
            creds_dict = dict(st.secrets["gcp_service_account"])
            self.credentials = ServiceAccountCredentials.from_json_keyfile_dict(
                creds_dict, 
                self.scope
            )
            self.client = gspread.authorize(self.credentials)
            spreadsheet_url = st.secrets["sheets"]["spreadsheet_url"]
            self.spreadsheet = self.client.open_by_url(spreadsheet_url)
            
        except Exception as e:
            st.error(f"❌ Error al conectar con Google Sheets: {e}")
            st.stop()
    
    def _is_cache_valid(self, sheet_name, ttl_seconds=60):
        """Verifica si el caché es válido (no ha expirado)"""
        if sheet_name not in st.session_state.cache_timestamps:
            return False
        
        cache_time = st.session_state.cache_timestamps[sheet_name]
        elapsed = (datetime.now() - cache_time).total_seconds()
        return elapsed < ttl_seconds
    
    def _get_from_cache(self, sheet_name):
        """Obtiene datos del caché si están disponibles y válidos"""
        if sheet_name in st.session_state.sheets_cache and self._is_cache_valid(sheet_name):
            return st.session_state.sheets_cache[sheet_name].copy()
        return None
    
    def _save_to_cache(self, sheet_name, data):
        """Guarda datos en el caché con timestamp"""
        st.session_state.sheets_cache[sheet_name] = data.copy()
        st.session_state.cache_timestamps[sheet_name] = datetime.now()
    
    def invalidate_cache(self, sheet_name=None):
        """Invalida el caché de una hoja específica o todo el caché"""
        if sheet_name:
            if sheet_name in st.session_state.sheets_cache:
                del st.session_state.sheets_cache[sheet_name]
            if sheet_name in st.session_state.cache_timestamps:
                del st.session_state.cache_timestamps[sheet_name]
        else:
            st.session_state.sheets_cache = {}
            st.session_state.cache_timestamps = {}
    
    def get_worksheet(self, sheet_name):
        """Obtiene una hoja específica"""
        try:
            return self.spreadsheet.worksheet(sheet_name)
        except Exception as e:
            st.error(f"❌ Error al acceder a la hoja '{sheet_name}': {e}")
            return None
    
    def get_dataframe(self, sheet_name, use_cache=True, ttl_seconds=60):
        """Obtiene datos de una hoja como DataFrame con caché inteligente"""
        try:
            # Intentar obtener del caché primero
            if use_cache:
                cached_data = self._get_from_cache(sheet_name)
                if cached_data is not None:
                    return cached_data
            
            # Si no hay caché válido, leer de Google Sheets
            worksheet = self.get_worksheet(sheet_name)
            if worksheet:
                data = worksheet.get_all_records()
                df = pd.DataFrame(data)
                
                # Guardar en caché
                if use_cache:
                    self._save_to_cache(sheet_name, df)
                
                return df
            return pd.DataFrame()
        except Exception as e:
            st.error(f"❌ Error al leer datos de '{sheet_name}': {e}")
            return pd.DataFrame()
    
    def append_row(self, sheet_name, data):
        """Agrega una fila a una hoja e invalida el caché"""
        try:
            worksheet = self.get_worksheet(sheet_name)
            if worksheet:
                worksheet.append_row(data)
                # Invalidar caché de esta hoja
                self.invalidate_cache(sheet_name)
                return True
            return False
        except Exception as e:
            st.error(f"❌ Error al agregar datos a '{sheet_name}': {e}")
            return False
    
    def update_cell(self, sheet_name, row, col, value):
        """Actualiza una celda específica e invalida el caché"""
        try:
            worksheet = self.get_worksheet(sheet_name)
            if worksheet:
                worksheet.update_cell(row, col, value)
                # Invalidar caché de esta hoja
                self.invalidate_cache(sheet_name)
                return True
            return False
        except Exception as e:
            st.error(f"❌ Error al actualizar celda en '{sheet_name}': {e}")
            return False
    
    def batch_update(self, sheet_name, updates):
        """Actualiza múltiples celdas en una sola llamada API"""
        try:
            worksheet = self.get_worksheet(sheet_name)
            if worksheet:
                worksheet.batch_update(updates)
                self.invalidate_cache(sheet_name)
                return True
            return False
        except Exception as e:
            st.error(f"❌ Error al actualizar celdas en lote en '{sheet_name}': {e}")
            return False
    
    def get_next_id(self, sheet_name):
        """Obtiene el siguiente ID disponible para una hoja"""
        try:
            df = self.get_dataframe(sheet_name, use_cache=True)
            if df.empty or 'id' not in df.columns:
                return 1
            return int(df['id'].max()) + 1
        except:
            return 1
    
    def log_action(self, usuario, accion, modulo, detalles, id_registro=""):
        """Registra una acción en la hoja de auditoría"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ip = "local"
            
            data = [
                timestamp,
                usuario,
                accion,
                modulo,
                detalles,
                ip,
                str(id_registro)
            ]
            
            return self.append_row("auditoria", data)
        except Exception as e:
            print(f"Error al registrar auditoría: {e}")
            return False

# Singleton para reutilizar la conexión
@st.cache_resource
def get_sheets_manager():
    """Retorna instancia única de SheetsManager"""
    return SheetsManager()