"""
FastAPI Application Principal
Agente ERP - Sistema híbrido de consultas con MCP y API REST
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logging import app_logger as logger
from app.database.connection import startup_db, shutdown_db

# Importar routers
from app.api.routes import health, database, monitoring


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle events para FastAPI

    Maneja startup y shutdown de la aplicación
    """
    # Startup
    logger.info("=" * 80)
    logger.info(f"Iniciando {settings.project_name} v{settings.version}")
    logger.info(f"Entorno: {settings.environment}")
    logger.info("=" * 80)

    # Inicializar base de datos
    await startup_db()

    logger.info("✓ Aplicación iniciada correctamente")
    logger.info(f"  API: http://{settings.api_host}:{settings.api_port}")
    logger.info(f"  Docs: http://{settings.api_host}:{settings.api_port}/docs")

    yield

    # Shutdown
    logger.info("Cerrando aplicación...")
    await shutdown_db()
    logger.info("✓ Aplicación cerrada correctamente")


# Crear aplicación FastAPI
app = FastAPI(
    title=settings.project_name,
    description="Sistema híbrido de consultas a base de datos ERP con MCP y API REST",
    version=settings.version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Incluir routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(database.router, prefix="/api/v1")
app.include_router(monitoring.router, prefix="/api/v1")


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint de la API

    Returns:
        Información básica de la API
    """
    return {
        "project": settings.project_name,
        "version": settings.version,
        "environment": settings.environment,
        "docs": f"http://{settings.api_host}:{settings.api_port}/docs",
        "health": f"http://{settings.api_host}:{settings.api_port}/api/v1/health"
    }


# Error handler global
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Handler global de excepciones

    Captura errores no manejados y los registra
    """
    logger.error(
        f"Error no manejado: {exc}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "error": str(exc)
        }
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Error interno del servidor",
            "error": str(exc) if settings.is_development else "Internal server error"
        }
    )


# Ejecutar con: uvicorn app.main:app --reload
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower()
    )
