"""
Endpoints para chat con el agente ERP usando MCP
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from app.schemas.requests import ChatRequest
from app.mcp.client import mcp_client
from app.core.logging import get_logger
from app.core.monitoring import usage_tracker

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/", response_model=Dict[str, Any])
async def chat_with_agent(request: ChatRequest) -> Dict[str, Any]:
    """
    Chat con el agente ERP usando MCP

    El agente puede:
    - Consultar la base de datos
    - Analizar tablas y esquemas
    - Generar consultas SQL
    - Explicar resultados

    Example:
        ```python
        {
            "message": "¿Cuántas facturas tenemos en total?",
            "conversation_history": [],
            "session_id": "abc123"
        }
        ```
    """
    try:
        logger.info(f"Chat request: {request.message[:100]}...")

        # Procesar mensaje con MCP
        result = await mcp_client.chat(
            message=request.message,
            conversation_history=request.conversation_history
        )

        if not result.get("success"):
            # Si el error es por límite de iteraciones o algo no crítico,
            # aún así retornamos la respuesta (no un 500)
            error_msg = result.get("error", "Error desconocido")

            return {
                "success": False,
                "message": f"No pude completar la consulta: {error_msg}",
                "tools_used": result.get("tools_used", []),
                "iterations": result.get("iterations", 0),
                "error": error_msg
            }

        # Tracking
        usage_tracker.track_query(
            query_type="chat_mcp",
            query=request.message,
            duration_ms=0,  # Por ahora
            success=True
        )

        return {
            "success": True,
            "message": result.get("response"),
            "tools_used": result.get("tools_used", []),
            "iterations": result.get("iterations", 0),
            "conversation_history": result.get("conversation_history", [])
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en chat endpoint: {e}", exc_info=True)
        usage_tracker.track_query(
            query_type="chat_mcp",
            query=request.message,
            duration_ms=0,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def chat_health() -> Dict[str, Any]:
    """Verifica que el chat MCP esté disponible"""
    try:
        # Verificar que el cliente MCP esté configurado
        if not mcp_client.openai_client:
            return {
                "status": "error",
                "message": "OpenAI client no configurado"
            }

        return {
            "status": "ok",
            "model": mcp_client.model,
            "mcp_enabled": True
        }

    except Exception as e:
        logger.error(f"Error en health check de chat: {e}")
        return {
            "status": "error",
            "message": str(e)
        }
