"""
Endpoints para exploración de base de datos
"""
from fastapi import APIRouter, HTTPException
from typing import List

from app.database.explorer import db_explorer
from app.schemas.responses import TableInfo, DatabaseSummary
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/database/summary", response_model=DatabaseSummary, tags=["Database"])
async def get_database_summary():
    """
    Obtiene un resumen general de la base de datos

    Returns:
        Resumen con número de tablas, filas totales, etc.
    """
    try:
        summary = db_explorer.get_database_summary()
        return DatabaseSummary(**summary)
    except Exception as e:
        logger.error(f"Error al obtener resumen: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/database/tables", response_model=List[str], tags=["Database"])
async def list_tables():
    """
    Lista todas las tablas de la base de datos

    Returns:
        Lista de nombres de tablas
    """
    try:
        tables = db_explorer.get_all_tables()
        return tables
    except Exception as e:
        logger.error(f"Error al listar tablas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/database/tables/{table_name}", response_model=TableInfo, tags=["Database"])
async def get_table_info(table_name: str):
    """
    Obtiene información detallada de una tabla

    Args:
        table_name: Nombre de la tabla

    Returns:
        Información completa de la tabla
    """
    try:
        info = db_explorer.get_table_info(table_name)
        return TableInfo(**info)
    except Exception as e:
        logger.error(f"Error al obtener info de tabla {table_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/database/search/tables/{search_term}", tags=["Database"])
async def search_tables(search_term: str):
    """
    Busca tablas por nombre

    Args:
        search_term: Término de búsqueda

    Returns:
        Lista de tablas que coinciden
    """
    try:
        results = db_explorer.search_tables_by_name(search_term)
        return {"search_term": search_term, "results": results, "count": len(results)}
    except Exception as e:
        logger.error(f"Error al buscar tablas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/database/search/columns/{search_term}", tags=["Database"])
async def search_columns(search_term: str):
    """
    Busca columnas por nombre en todas las tablas

    Args:
        search_term: Término de búsqueda

    Returns:
        Lista de columnas que coinciden
    """
    try:
        results = db_explorer.search_columns(search_term)
        return {"search_term": search_term, "results": results, "count": len(results)}
    except Exception as e:
        logger.error(f"Error al buscar columnas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/database/tables/{table_name}/relationships", tags=["Database"])
async def get_table_relationships(table_name: str):
    """
    Obtiene las relaciones de una tabla

    Args:
        table_name: Nombre de la tabla

    Returns:
        Relaciones entrantes y salientes
    """
    try:
        relationships = db_explorer.get_table_relationships(table_name)
        return relationships
    except Exception as e:
        logger.error(f"Error al obtener relaciones de {table_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/database/tables/{table_name}/sample", tags=["Database"])
async def get_table_sample(table_name: str, limit: int = 5):
    """
    Obtiene una muestra de datos de una tabla

    Args:
        table_name: Nombre de la tabla
        limit: Número de filas (default: 5, max: 100)

    Returns:
        Muestra de datos en formato JSON
    """
    try:
        if limit > 100:
            raise HTTPException(status_code=400, detail="Límite máximo es 100 filas")

        df = db_explorer.get_table_sample(table_name, limit)

        if df is None:
            raise HTTPException(status_code=404, detail=f"Tabla {table_name} no encontrada")

        return {
            "table": table_name,
            "rows": len(df),
            "columns": df.columns.tolist(),
            "data": df.to_dict(orient="records")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener muestra de {table_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
