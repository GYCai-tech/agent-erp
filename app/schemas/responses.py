"""
Pydantic schemas para responses
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class HealthResponse(BaseModel):
    """Response del health check"""

    status: str = Field(default="ok")
    timestamp: datetime = Field(default_factory=datetime.now)
    version: str
    database: str
    environment: str


class QueryResponse(BaseModel):
    """Response de una consulta"""

    success: bool
    query_type: str = Field(description="'api' o 'mcp'")
    result: Any
    tokens_used: Optional[int] = None
    duration_ms: float
    error: Optional[str] = None


class TableInfo(BaseModel):
    """Información de una tabla"""

    name: str
    columns: List[Dict[str, Any]]
    primary_keys: List[str]
    foreign_keys: List[Dict[str, Any]]
    row_count: Optional[int]


class DatabaseSummary(BaseModel):
    """Resumen de la base de datos"""

    total_tables: int
    tables_with_data: int
    total_rows: int
    tables: List[str]


class UsageStats(BaseModel):
    """Estadísticas de uso"""

    total_queries: int
    api_queries: int
    mcp_queries: int
    api_percentage: float
    mcp_percentage: float
    total_tokens: int
    avg_tokens_per_query: float
    avg_duration_ms: float
    success_rate: float
