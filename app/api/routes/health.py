"""
Health check endpoint
"""
from fastapi import APIRouter
from datetime import datetime

from app.core.config import settings
from app.schemas.responses import HealthResponse
from app.database.connection import test_connection

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint

    Verifica que la API esté funcionando y que la base de datos esté accesible

    Returns:
        HealthResponse con estado del sistema
    """
    # Verificar conexión a BD
    db_status = "connected" if test_connection() else "disconnected"

    return HealthResponse(
        status="ok",
        timestamp=datetime.now(),
        version=settings.version,
        database=db_status,
        environment=settings.environment
    )


@router.get("/ping", tags=["Health"])
async def ping():
    """
    Simple ping endpoint

    Returns:
        Mensaje simple para verificar que la API responde
    """
    return {"message": "pong", "timestamp": datetime.now().isoformat()}
