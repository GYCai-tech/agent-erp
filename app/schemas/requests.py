"""
Pydantic schemas para requests
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request para ejecutar una consulta en lenguaje natural"""

    query: str = Field(
        ...,
        description="Consulta en lenguaje natural",
        min_length=3,
        max_length=1000,
        examples=["¿Cuántas facturas tenemos este mes?"]
    )

    force_mcp: bool = Field(
        default=False,
        description="Forzar uso de MCP en lugar de API"
    )

    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Contexto adicional para la consulta"
    )


class SQLQueryRequest(BaseModel):
    """Request para ejecutar SQL directo (modo avanzado)"""

    sql: str = Field(
        ...,
        description="Consulta SQL a ejecutar",
        min_length=5
    )

    params: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Parámetros de la consulta"
    )


class TableExploreRequest(BaseModel):
    """Request para explorar una tabla específica"""

    table_name: str = Field(
        ...,
        description="Nombre de la tabla a explorar"
    )

    include_sample: bool = Field(
        default=True,
        description="Incluir muestra de datos"
    )

    sample_size: int = Field(
        default=5,
        description="Número de filas de muestra",
        ge=1,
        le=100
    )
