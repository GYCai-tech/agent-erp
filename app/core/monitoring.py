"""
Sistema de monitoreo y tracking de uso
Rastrea uso de API vs MCP, tokens consumidos, tiempos de respuesta, etc.
"""
import time
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import threading

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class QueryMetrics:
    """Métricas de una consulta"""
    timestamp: datetime
    query_type: str  # "api" o "mcp"
    query: str
    duration_ms: float
    tokens_used: Optional[int] = None
    success: bool = True
    error: Optional[str] = None
    model: Optional[str] = None


class UsageTracker:
    """
    Tracker de uso del sistema
    Thread-safe para uso concurrente
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._metrics: List[QueryMetrics] = []
        self._counters: Dict[str, int] = defaultdict(int)
        self._total_tokens: int = 0
        self._total_duration_ms: float = 0.0

    def track_query(
        self,
        query_type: str,
        query: str,
        duration_ms: float,
        tokens_used: Optional[int] = None,
        success: bool = True,
        error: Optional[str] = None,
        model: Optional[str] = None
    ):
        """
        Registra una consulta

        Args:
            query_type: Tipo de consulta ("api" o "mcp")
            query: La consulta realizada
            duration_ms: Duración en milisegundos
            tokens_used: Tokens consumidos (si aplica)
            success: Si fue exitosa
            error: Mensaje de error (si hubo)
            model: Modelo usado (gpt-4, claude, etc.)
        """
        with self._lock:
            metric = QueryMetrics(
                timestamp=datetime.now(),
                query_type=query_type,
                query=query,
                duration_ms=duration_ms,
                tokens_used=tokens_used,
                success=success,
                error=error,
                model=model
            )

            self._metrics.append(metric)
            self._counters[f"{query_type}_total"] += 1

            if success:
                self._counters[f"{query_type}_success"] += 1
            else:
                self._counters[f"{query_type}_failed"] += 1

            if tokens_used:
                self._total_tokens += tokens_used
                self._counters[f"{query_type}_tokens"] += tokens_used

            self._total_duration_ms += duration_ms

            # Log
            logger.info(
                f"Query tracked: {query_type}",
                extra={
                    "query_type": query_type,
                    "duration_ms": duration_ms,
                    "tokens": tokens_used,
                    "success": success
                }
            )

    def get_stats(self) -> Dict:
        """
        Obtiene estadísticas de uso

        Returns:
            Diccionario con estadísticas
        """
        with self._lock:
            if not self._metrics:
                return {
                    "total_queries": 0,
                    "message": "No hay datos de uso todavía"
                }

            total_queries = len(self._metrics)
            api_queries = self._counters["api_total"]
            mcp_queries = self._counters["mcp_total"]

            return {
                "total_queries": total_queries,
                "api_queries": api_queries,
                "mcp_queries": mcp_queries,
                "api_percentage": round((api_queries / total_queries) * 100, 2) if total_queries > 0 else 0,
                "mcp_percentage": round((mcp_queries / total_queries) * 100, 2) if total_queries > 0 else 0,
                "total_tokens": self._total_tokens,
                "avg_tokens_per_query": round(self._total_tokens / total_queries, 2) if total_queries > 0 else 0,
                "avg_duration_ms": round(self._total_duration_ms / total_queries, 2) if total_queries > 0 else 0,
                "success_rate": round(
                    ((self._counters["api_success"] + self._counters["mcp_success"]) / total_queries) * 100,
                    2
                ) if total_queries > 0 else 0,
                "counters": dict(self._counters)
            }

    def get_recent_queries(self, limit: int = 10) -> List[Dict]:
        """
        Obtiene las consultas más recientes

        Args:
            limit: Número máximo de consultas a retornar

        Returns:
            Lista de consultas recientes
        """
        with self._lock:
            recent = self._metrics[-limit:]
            return [
                {
                    "timestamp": m.timestamp.isoformat(),
                    "query_type": m.query_type,
                    "query": m.query[:100] + "..." if len(m.query) > 100 else m.query,
                    "duration_ms": m.duration_ms,
                    "tokens_used": m.tokens_used,
                    "success": m.success,
                    "model": m.model
                }
                for m in recent
            ]

    def reset(self):
        """Resetea todas las métricas"""
        with self._lock:
            self._metrics.clear()
            self._counters.clear()
            self._total_tokens = 0
            self._total_duration_ms = 0.0
            logger.info("Métricas reseteadas")


# Instancia global del tracker
usage_tracker = UsageTracker()


# Context manager para tracking automático
class track_query_time:
    """
    Context manager para medir automáticamente el tiempo de una query

    Ejemplo:
        with track_query_time("api", "SELECT * FROM table") as tracker:
            result = execute_query(...)
            tracker.set_tokens(result.tokens_used)
    """

    def __init__(self, query_type: str, query: str, model: Optional[str] = None):
        self.query_type = query_type
        self.query = query
        self.model = model
        self.start_time = None
        self.tokens_used = None
        self.success = True
        self.error = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000

        if exc_type is not None:
            self.success = False
            self.error = str(exc_val)

        usage_tracker.track_query(
            query_type=self.query_type,
            query=self.query,
            duration_ms=duration_ms,
            tokens_used=self.tokens_used,
            success=self.success,
            error=self.error,
            model=self.model
        )

        # No suprimimos la excepción
        return False

    def set_tokens(self, tokens: int):
        """Establece el número de tokens usados"""
        self.tokens_used = tokens

    def set_model(self, model: str):
        """Establece el modelo usado"""
        self.model = model
