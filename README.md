# Agente ERP - Sistema Híbrido de Consultas

Sistema de agentes inteligentes para consultar la base de datos del ERP AHORA mediante lenguaje natural, combinando API REST para consultas frecuentes y MCP (Model Context Protocol) para consultas complejas.

**Empresa**: Gómez y Crespo (Ourense, España)
**Desarrollado por**: Santiago Arce - Data & Automation Analyst
**Versión**: 1.0.0

---

## 🎯 Objetivo

Crear un sistema que permita:
1. ✅ Explorar y documentar la estructura de la base de datos
2. 🤖 Responder consultas en lenguaje natural
3. 💰 Optimizar costes usando API para consultas comunes
4. 🔬 Usar MCP para consultas complejas/exploratorias
5. 📊 Aprender progresivamente qué consultas son frecuentes

---

## 🏗️ Arquitectura

```
┌─────────────────┐
│   Usuario      │
└────────┬────────┘
         │
    ┌────▼─────┐
    │ FastAPI  │
    └────┬─────┘
         │
    ┌────▼──────────────┐
    │  Router Agent     │  ◄─ Decide: API o MCP
    └────┬──────────────┘
         │
    ┌────▼─────┬─────────┐
    │          │         │
┌───▼──┐   ┌──▼───┐  ┌──▼────┐
│ API  │   │ MCP  │  │ SQL   │
│ REST │   │Server│  │Server │
└──────┘   └──────┘  └───────┘
```

---

## 📁 Estructura del Proyecto

```
agente-erp/
├── app/
│   ├── main.py                 # FastAPI app principal
│   ├── api/                    # Endpoints REST
│   │   └── routes/
│   │       ├── health.py       # Health check
│   │       ├── database.py     # Exploración de BD
│   │       └── monitoring.py   # Estadísticas
│   ├── mcp/                    # MCP Server (Fase 2)
│   ├── agents/                 # Lógica de agentes (Fase 2)
│   ├── database/
│   │   ├── connection.py       # Pool de conexiones
│   │   └── explorer.py         # Exploración de BD
│   ├── core/
│   │   ├── config.py           # Configuración
│   │   ├── logging.py          # Sistema de logs
│   │   └── monitoring.py       # Tracking de uso
│   └── schemas/                # Pydantic models
│       ├── requests.py
│       └── responses.py
├── scripts/
│   └── explore_database.py     # Script de exploración
├── docs/
│   └── database_schema.md      # Documentación auto-generada
├── tests/
├── .env                        # Variables de entorno
├── .env.example
├── .gitignore
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 🚀 Instalación y Configuración

### Opción 1: Instalación Local

#### 1. Requisitos previos

- Python 3.11+
- ODBC Driver 18 para SQL Server
- Acceso a base de datos GOMEZYCRESPO_PRUEBAS

#### 2. Instalar dependencias

```bash
cd P:/agente-erp
pip install -r requirements.txt
```

#### 3. Configurar .env

El archivo `.env` ya está configurado con las credenciales correctas para desarrollo.

Verifica que contenga:
- `DB_SERVER=SRVAHORA`
- `DB_DATABASE=GOMEZYCRESPO_PRUEBAS`
- `OPENAI_API_KEY=tu-api-key`

#### 4. Probar conexión

```bash
python -c "from app.database.connection import test_connection; test_connection()"
```

### Opción 2: Docker

```bash
docker-compose up -d
```

---

## 📊 Fase 1: Exploración de Base de Datos

### Ejecutar exploración completa

```bash
python scripts/explore_database.py
```

Este script:
- ✅ Conecta a la base de datos
- ✅ Lista todas las tablas
- ✅ Analiza columnas, tipos, PKs, FKs
- ✅ Cuenta registros por tabla
- ✅ Genera `docs/database_schema.md`

**Output esperado:**
```
================================================================================
EXPLORADOR DE BASE DE DATOS
================================================================================

Obteniendo información de todas las tablas...
  Documentando tabla: A_Facturas
  Documentando tabla: Clientes
  ...

================================================================================
✓ EXPLORACIÓN COMPLETADA
================================================================================
  Tablas documentadas: 150
  Archivo generado: P:/agente-erp/docs/database_schema.md
================================================================================
```

---

## 🔥 Iniciar FastAPI

### Desarrollo (con auto-reload)

```bash
cd P:/agente-erp
python app/main.py
```

O usando uvicorn directamente:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Producción

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**La API estará disponible en:**
- 📖 Docs interactiva: http://localhost:8000/docs
- 📘 ReDoc: http://localhost:8000/redoc
- ⚡ API: http://localhost:8000/api/v1/

---

## 🔍 Endpoints Disponibles (Fase 1)

### Health Check

```bash
# Verificar estado
GET /api/v1/health

# Ping simple
GET /api/v1/ping
```

### Exploración de Base de Datos

```bash
# Resumen general
GET /api/v1/database/summary

# Listar todas las tablas
GET /api/v1/database/tables

# Info de una tabla específica
GET /api/v1/database/tables/{table_name}

# Buscar tablas por nombre
GET /api/v1/database/search/tables/{search_term}

# Buscar columnas
GET /api/v1/database/search/columns/{search_term}

# Ver relaciones de una tabla
GET /api/v1/database/tables/{table_name}/relationships

# Obtener muestra de datos
GET /api/v1/database/tables/{table_name}/sample?limit=5
```

### Monitoreo

```bash
# Estadísticas de uso
GET /api/v1/monitoring/stats

# Consultas recientes
GET /api/v1/monitoring/recent?limit=10

# Resetear estadísticas
POST /api/v1/monitoring/reset
```

---

## 💡 Ejemplos de Uso

### Ejemplo 1: Explorar tabla A_Facturas

```bash
curl http://localhost:8000/api/v1/database/tables/A_Facturas
```

**Response:**
```json
{
  "name": "A_Facturas",
  "columns": [
    {"name": "Id Factura", "type": "BIGINT", "nullable": false},
    {"name": "Cliente", "type": "VARCHAR", "nullable": true},
    {"name": "Total", "type": "FLOAT", "nullable": true}
  ],
  "primary_keys": ["Id Factura"],
  "foreign_keys": [],
  "row_count": 112
}
```

### Ejemplo 2: Buscar tablas relacionadas con clientes

```bash
curl http://localhost:8000/api/v1/database/search/tables/cliente
```

### Ejemplo 3: Ver muestra de datos

```bash
curl http://localhost:8000/api/v1/database/tables/A_Facturas/sample?limit=3
```

---

## 🔧 Configuración Avanzada

### Variables de Entorno Clave

| Variable | Descripción | Default |
|----------|-------------|---------|
| `DB_SERVER` | Servidor SQL Server | SRVAHORA |
| `DB_DATABASE` | Base de datos | GOMEZYCRESPO_PRUEBAS |
| `DB_READ_ONLY` | Modo solo lectura | true |
| `OPENAI_API_KEY` | API key de OpenAI | - |
| `LOG_LEVEL` | Nivel de logging | INFO |
| `LOG_FORMAT` | Formato logs (text/json) | text |
| `ENABLE_MONITORING` | Activar tracking | true |

### Logging

Los logs se guardan en `logs/agente_erp.log`

Configurar nivel:
```bash
export LOG_LEVEL=DEBUG
```

Formato JSON para producción:
```bash
export LOG_FORMAT=json
```

---

## 🧪 Testing

```bash
# Instalar dependencias de testing
pip install pytest pytest-asyncio httpx

# Ejecutar tests
pytest tests/

# Con cobertura
pytest --cov=app tests/
```

---

## 🚦 Roadmap

### ✅ Fase 1: Setup y Exploración (COMPLETADA)
- [x] Estructura del proyecto
- [x] Conexión a base de datos
- [x] Exploración de esquema
- [x] FastAPI básica
- [x] Endpoints de exploración
- [x] Sistema de logging
- [x] Monitoreo básico

### 🔄 Fase 2: MCP Server (SIGUIENTE)
- [ ] Implementar MCP Server
- [ ] Tools para consultas SQL
- [ ] Tools para análisis de esquema
- [ ] Integración con OpenAI/Claude

### 📋 Fase 3: Agente Router
- [ ] Agente que decide API vs MCP
- [ ] Sistema de caché para consultas frecuentes
- [ ] Optimización de costes

### 🎯 Fase 4: NLQ (Natural Language Query)
- [ ] Traducción de lenguaje natural a SQL
- [ ] Validación de consultas
- [ ] Explicación de resultados

### 📈 Fase 5: Aprendizaje
- [ ] Tracking de consultas frecuentes
- [ ] Generación automática de endpoints
- [ ] Embeddings con Qdrant

---

## 📚 Documentación Adicional

- **Database Schema**: Ver `docs/database_schema.md` (generado automáticamente)
- **API Docs**: http://localhost:8000/docs
- **Architecture**: Ver diagramas en `docs/architecture/`

---

## 🔒 Seguridad

**IMPORTANTE:**
- ✅ Base de datos en modo **SOLO LECTURA** por defecto
- ✅ Credenciales en `.env` (no committear a Git)
- ✅ Validación de entrada en todos los endpoints
- ✅ Sanitización de consultas SQL

Para cambiar a modo escritura (NO RECOMENDADO):
```bash
export DB_READ_ONLY=false
```

---

## 🐛 Troubleshooting

### Error: "ODBC Driver not found"

```bash
# Windows: Instalar ODBC Driver 18
# https://go.microsoft.com/fwlink/?linkid=2249004

# Linux:
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
sudo apt-get install msodbcsql18
```

### Error: "Connection timeout"

Verificar:
1. Que SQL Server esté en ejecución
2. Que el servidor `SRVAHORA` sea accesible
3. Que las credenciales sean correctas

```bash
# Probar conexión
python -c "from app.database.connection import test_connection; test_connection()"
```

### Error: "Module not found"

```bash
pip install -r requirements.txt
```

---

## 👥 Contribuir

Este es un proyecto interno de Gómez y Crespo.

Para contribuir:
1. Crear rama feature: `git checkout -b feature/nueva-funcionalidad`
2. Commit cambios: `git commit -m "Descripción"`
3. Push: `git push origin feature/nueva-funcionalidad`
4. Crear Pull Request

---

## 📞 Contacto

**Santiago Arce**
Data & Automation Analyst
Gómez y Crespo - Ourense, España

---

## 📄 Licencia

Uso interno - Gómez y Crespo

---

**Estado del Proyecto**: 🟢 Fase 1 Completada | 🔄 Fase 2 En Desarrollo
