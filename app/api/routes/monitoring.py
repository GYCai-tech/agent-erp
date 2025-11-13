"""
Endpoints para monitoreo y estadísticas de uso
"""
from fastapi import APIRouter

from app.core.monitoring import usage_tracker
from app.schemas.responses import UsageStats
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/monitoring/stats", response_model=UsageStats, tags=["Monitoring"])
async def get_usage_stats():
    """
    Obtiene estadísticas de uso del sistema

    Returns:
        Estadísticas de uso de API vs MCP, tokens, etc.
    """
    stats = usage_tracker.get_stats()
    return UsageStats(**stats) if stats.get("total_queries", 0) > 0 else UsageStats(
        total_queries=0,
        api_queries=0,
        mcp_queries=0,
        api_percentage=0,
        mcp_percentage=0,
        total_tokens=0,
        avg_tokens_per_query=0,
        avg_duration_ms=0,
        success_rate=0
    )


@router.get("/monitoring/recent", tags=["Monitoring"])
async def get_recent_queries(limit: int = 10):
    """
    Obtiene las consultas más recientes

    Args:
        limit: Número de consultas a retornar (default: 10, max: 100)

    Returns:
        Lista de consultas recientes
    """
    if limit > 100:
        limit = 100

    recent = usage_tracker.get_recent_queries(limit)
    return {"count": len(recent), "queries": recent}


@router.post("/monitoring/reset", tags=["Monitoring"])
async def reset_stats():
    """
    Resetea las estadísticas de uso

    Returns:
        Confirmación de reset
    """
    usage_tracker.reset()
    logger.info("Estadísticas de uso reseteadas")
    return {"message": "Estadísticas reseteadas exitosamente"}
