# 🏢 Sistema de Recursos Humanos

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-green.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.32+-red.svg)
![License](https://img.shields.io/badge/license-Proprietary-orange.svg)

**Sistema integral de gestión de recursos humanos con control de asistencias, permisos, incapacidades y bonos**

[Características](#-características) • [Tecnologías](#-tecnologías) • [Instalación](#-instalación) • [Uso](#-uso) • [Licencia](#-licencia)

</div>

---

## 📋 Descripción

Sistema completo de gestión de recursos humanos desarrollado con **Streamlit** y **Supabase**, diseñado para administrar eficientemente:

- ✅ **Asistencias**: Registro diario con detección de retardos y ausencias
- 📅 **Permisos**: Control de días de permiso (máximo 9 al año)
- 🏥 **Incapacidades**: Gestión de incapacidades médicas, maternidad y riesgos laborales
- 💰 **Bonos**: Cálculo automático de bonificaciones basado en asistencia
- 👥 **Empleados**: Base de datos completa con información laboral
- 📊 **Reportes**: Estadísticas y análisis en tiempo real
- 🔐 **Auditoría**: Registro completo de todas las acciones del sistema

---

## ✨ Características

### 🎯 Gestión de Asistencias
- 📋 Registro masivo por oficina
- ⏰ Control de retardos automático
- 📅 Diferenciación de días sábados
- 📈 Estadísticas en tiempo real
- 🔄 Sincronización con Google Sheets

### 📝 Control de Permisos
- 🗓️ Cálculo automático de días hábiles
- ✅ Flujo de aprobación/rechazo
- 🚫 Validación de disponibilidad (9 días/año)
- 📊 Historial completo con filtros
- ⚠️ Detección de solapamientos

### 🏥 Gestión de Incapacidades
- 📋 Múltiples tipos: enfermedad, maternidad, accidentes
- 📄 Adjuntar documentos (URLs)
- 🔢 Registro de folios IMSS/ISSSTE
- 📊 Estadísticas por tipo y oficina
- 📈 Top empleados con más incapacidades

### 💰 Cálculo de Bonos
- 🎯 Basado en asistencia mensual
- ⚙️ Configuración personalizable
- 📉 Penalizaciones por retardos/ausencias
- 📊 Historial de bonos pagados
- 📥 Exportación a CSV

### 🔐 Sistema de Autenticación
- 👤 3 roles: Admin, Supervisora, Registrador
- 🔒 Permisos por nivel
- 🏢 Filtrado automático por oficina
- 📝 Log de auditoría completo

### 📊 Reportes y Análisis
- 📈 Dashboard con métricas clave
- 🔍 Filtros avanzados por periodo/oficina
- 📥 Exportación a CSV/Excel
- 📊 Visualización de estadísticas

---

## 🛠️ Tecnologías

### Backend
- 🐍 **Python 3.9+**
- 🎈 **Streamlit** - Framework web
- 🗄️ **Supabase** - Base de datos PostgreSQL
- 📊 **Pandas** - Procesamiento de datos

### Integrations
- 📊 **Google Sheets API** - Sincronización de respaldo
- 🔐 **OAuth2** - Autenticación Google

### Frontend
- 🎨 **Streamlit Components** - UI interactiva
- 📊 **Plotly** - Visualizaciones (opcional)
- 🎯 **Custom CSS** - Estilos personalizados

---

## 📦 Estructura del Proyecto

```
sistema-rh/
├── 📄 app.py                      # Aplicación principal
├── 🔐 auth.py                     # Sistema de autenticación
├── ⚙️ config.py                   # Configuración y gestión de datos
├── 📁 modules/
│   ├── 📋 asistencias.py         # Módulo de asistencias
│   ├── 📅 permisos.py            # Módulo de permisos
│   ├── 🏥 incapacidades.py       # Módulo de incapacidades
│   └── 💰 bonos.py               # Módulo de bonos
├── 📄 requirements.txt           # Dependencias Python
├── 🔒 .streamlit/
│   └── secrets.toml              # Configuración secreta (NO INCLUIR EN GIT)
├── 📘 README.md                  # Este archivo
└── 📜 LICENSE                    # Licencia de uso

```

---

## 🚀 Instalación

### Prerrequisitos

- Python 3.9 o superior
- Cuenta de Supabase
- Cuenta de Google Cloud (para Google Sheets)
- Git

### Paso 1: Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/sistema-rh.git
cd sistema-rh
```

### Paso 2: Crear entorno virtual

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### Paso 3: Instalar dependencias

```bash
pip install -r requirements.txt
```

### Paso 4: Configurar Supabase

1. Crear proyecto en [supabase.com](https://supabase.com)
2. Ejecutar los scripts SQL para crear las tablas:
   - `empleados`
   - `asistencias`
   - `permisos`
   - `incapacidades`
   - `bonos`
   - `config_bonos`
   - `auditoria`

### Paso 5: Configurar Google Sheets API

1. Crear proyecto en [Google Cloud Console](https://console.cloud.google.com)
2. Habilitar Google Sheets API
3. Crear Service Account y descargar JSON
4. Compartir el Spreadsheet con el email del Service Account

### Paso 6: Configurar secrets

Crear archivo `.streamlit/secrets.toml`:

```toml
[supabase]
url = "https://tu-proyecto.supabase.co"
key = "tu-anon-key"

[gcp_service_account]
type = "service_account"
project_id = "tu-proyecto"
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "..."
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."

[sheets]
spreadsheet_url = "https://docs.google.com/spreadsheets/d/..."

[usuarios.admin]
email = "admin@eprepa.com"
password = "56678"
nombre = "Administrador"
rol = "admin"
oficina = "Matriz"
```

### Paso 7: Ejecutar la aplicación

```bash
streamlit run app.py
```

La aplicación estará disponible en `http://localhost:8501`

---

## 💻 Uso

### Roles y Permisos

#### 👑 Admin
- ✅ Acceso total a todos los módulos
- ⚙️ Configuración de bonos
- 👥 Gestión de usuarios
- 📊 Reportes completos

#### 👩‍💼 Supervisora
- ✅ Aprobar/rechazar permisos
- 📋 Ver todas las oficinas
- 💰 Calcular bonos
- 🔄 Sincronizar datos

#### 👤 Registrador
- 📋 Registrar asistencias de su oficina
- 📅 Solicitar permisos
- 🏥 Registrar incapacidades
- 📊 Ver historial de su oficina

### Flujo de Trabajo

1. **Registro de Asistencias**
   - Ingresar al módulo de Asistencias
   - Seleccionar fecha y oficina
   - Marcar estado de cada empleado
   - Guardar registros

2. **Solicitud de Permisos**
   - Ir a módulo de Permisos → Solicitar
   - Seleccionar empleado y fechas
   - Describir motivo
   - Enviar solicitud

3. **Aprobación de Permisos**
   - Ir a módulo de Permisos → Aprobar
   - Revisar solicitudes pendientes
   - Aprobar o rechazar con comentario

4. **Cálculo de Bonos**
   - Ir a módulo de Bonos
   - Seleccionar periodo (año/mes)
   - Calcular bonos automáticamente
   - Guardar resultados

---

## 📊 Base de Datos

### Tablas Principales

#### 👥 empleados
```sql
- id_empleado (PK, unique)
- nombre_completo
- oficina
- activo
- puesto
- fecha_ingreso
- dias_permiso_disponibles
```

#### 📋 asistencias
```sql
- id (PK)
- id_empleado (FK)
- fecha
- hora_registro
- estado (Presente/Ausente/Retardo/Permiso/Incapacidad)
- oficina
- registrado_por
```

#### 📅 permisos
```sql
- id (PK)
- id_empleado (FK)
- fecha_inicio
- fecha_fin
- dias_solicitados
- estado (Pendiente/Aprobado/Rechazado)
- motivo
```

#### 🏥 incapacidades
```sql
- id (PK)
- id_empleado (FK)
- tipo
- fecha_inicio
- fecha_fin
- dias_totales
- motivo
```

#### 💰 bonos
```sql
- id (PK)
- id_empleado (FK)
- año
- mes
- presentes
- retardos
- ausentes
- monto_bono
```

---

## 🔧 Configuración Avanzada

### Personalizar Cálculo de Bonos

En el módulo de Bonos → Configuración:

- **Bono Base**: Monto inicial del bono ($1,000)
- **Penalización Retardo**: Descuento por retardo ($50)
- **Penalización Ausencia**: Descuento por ausencia ($200)
- **Asistencias Mínimas**: Días requeridos para obtener bono (20)

### Oficinas Disponibles

El sistema soporta las siguientes oficinas/zonas:
- Norte, Sur, Este, Oeste, Centro
- Zona 1 a Zona 10

Para agregar nuevas oficinas, actualizar en `app.py`

---

## 🐛 Solución de Problemas

### Error de conexión a Supabase
```bash
Error: Unable to connect to Supabase
```
**Solución**: Verificar URL y API key en `secrets.toml`

### Error de autenticación Google Sheets
```bash
Error: Invalid credentials
```
**Solución**: Verificar que el Service Account tiene acceso al spreadsheet

### Error "No se pudo ejecutar removeChild"
```bash
NotFoundError: removeChild
```
**Solución**: Limpiar caché del navegador o usar `st.rerun()`

---

## 📈 Roadmap

- [ ] 📱 Versión móvil responsive
- [ ] 📧 Notificaciones por email
- [ ] 📊 Dashboard con gráficas avanzadas
- [ ] 🔔 Alertas automáticas
- [ ] 📄 Generación de reportes PDF
- [ ] 🌐 Soporte multi-idioma
- [ ] 🔐 Autenticación con SSO
- [ ] 📲 App móvil nativa

---

## 👨‍💻 Autor

**[Martin Angel Carrizalez Piña]**
- 📧 Email: [martin.carrizalez0823@alumnos.udg.mx.com]]
- 💼 LinkedIn: [tu-linkedin]
- 🌐 Website: [tu-website]

---

## 🤝 Contribuciones

❌ **Este es un proyecto privado y propietario.**

Las contribuciones, forks, y uso no autorizado están prohibidos.

---

## 📄 Licencia

```
Copyright © 2026 [Martin Angel Carrizalez Piña]

LICENCIA DE SOFTWARE PROPIETARIO

Todos los derechos reservados.

Este software y su código fuente son propiedad exclusiva de [Martin Angel Carrizalez Piña].

ESTÁ PROHIBIDO:
❌ Copiar, modificar o distribuir este software
❌ Crear trabajos derivados
❌ Uso comercial sin autorización escrita
❌ Ingeniería inversa
❌ Sublicenciar o vender

PERMISOS:
✅ Uso personal del propietario
✅ Instalación en servidores propios
✅ Modificación para uso interno

Para solicitar una licencia de uso, contactar a:
📧 [martin.carrizalez0823@alumnos.udg.mx.com]

EL SOFTWARE SE PROPORCIONA "TAL CUAL", SIN GARANTÍA DE NINGÚN TIPO.
```

---

## ⚠️ Aviso Legal

Este software es **PRIVADO Y PROPIETARIO**. 

**NO ESTÁ PERMITIDO:**
- ❌ Copiar total o parcialmente
- ❌ Redistribuir o compartir
- ❌ Uso comercial sin licencia
- ❌ Modificación sin autorización
- ❌ Ingeniería inversa

**Cualquier uso no autorizado será perseguido legalmente.**

---

## 📞 Soporte

Para soporte técnico o consultas sobre licencias:

- 📧 **Email**: [martin.carrizalez0823@alumnos.udg.mx.com]]
- 💬 **WhatsApp**: [+52 3310220930]
- 🌐 **Website**: [www.tu-empresa.com]

---

## 🔒 Seguridad

Si encuentras una vulnerabilidad de seguridad, por favor **NO** abras un issue público.

Envía un email a: [martin.carrizalez0823@alumnos.udg.mx.com]]

---

## 📝 Changelog

### v1.0.0 (2024-12-09)
- 🎉 Lanzamiento inicial
- ✅ Módulo de asistencias completo
- 📅 Módulo de permisos con aprobaciones
- 🏥 Módulo de incapacidades
- 💰 Módulo de cálculo de bonos
- 🔐 Sistema de autenticación multi-rol
- 📊 Dashboard y reportes

---

<div align="center">

**Desarrollado por [Martin Angel Carrizalez Piña]**

© 2026 Todos los derechos reservados

</div>
