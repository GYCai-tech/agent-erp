"""
MCP Server para consultas al ERP
Proporciona herramientas especializadas para interactuar con la base de datos
"""

import asyncio
import json
from typing import Any, Dict, List, Optional
from datetime import datetime

from mcp.server import Server
from mcp.types import Tool, TextContent

from app.database.connection import get_db_session
from app.database.explorer import db_explorer
from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class ERPMCPServer:
    """Servidor MCP para el ERP con herramientas especializadas"""

    def __init__(self):
        self.server = Server("erp-agent-mcp")
        self._setup_handlers()
        logger.info("MCP Server inicializado")

    def _setup_handlers(self):
        """Configura los handlers del servidor MCP"""

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """Lista todas las herramientas disponibles"""
            return [
                Tool(
                    name="execute_query",
                    description="Ejecuta una consulta SQL SELECT de solo lectura en la base de datos del ERP. "
                                "Devuelve los resultados en formato JSON. Solo permite consultas SELECT.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Query SQL SELECT a ejecutar (solo lectura)"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Límite de resultados a devolver (default: 100, max: 1000)",
                                "default": 100
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="get_table_schema",
                    description="Obtiene el esquema completo de una tabla: columnas, tipos de datos, "
                                "claves primarias, claves foráneas, y relaciones con otras tablas.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "table_name": {
                                "type": "string",
                                "description": "Nombre exacto de la tabla (case-sensitive)"
                            }
                        },
                        "required": ["table_name"]
                    }
                ),
                Tool(
                    name="search_tables",
                    description="Busca tablas en la base de datos por nombre o patrón. "
                                "Útil cuando no conoces el nombre exacto de una tabla.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "search_term": {
                                "type": "string",
                                "description": "Término de búsqueda (ej: 'factura', 'cliente', 'pedido')"
                            }
                        },
                        "required": ["search_term"]
                    }
                ),
                Tool(
                    name="get_table_relationships",
                    description="Obtiene las relaciones de una tabla con otras tablas a través de "
                                "claves foráneas. Muestra tanto las relaciones salientes (FK) como entrantes.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "table_name": {
                                "type": "string",
                                "description": "Nombre de la tabla"
                            }
                        },
                        "required": ["table_name"]
                    }
                ),
                Tool(
                    name="get_database_summary",
                    description="Obtiene un resumen general de la base de datos: número de tablas, "
                                "tablas con más registros, estructura general.",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="analyze_table_data",
                    description="Analiza los datos de una tabla: cuenta registros, identifica valores nulos, "
                                "obtiene estadísticas básicas de columnas numéricas.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "table_name": {
                                "type": "string",
                                "description": "Nombre de la tabla a analizar"
                            },
                            "sample_size": {
                                "type": "integer",
                                "description": "Número de filas a analizar (default: 1000)",
                                "default": 1000
                            }
                        },
                        "required": ["table_name"]
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> List[TextContent]:
            """Ejecuta una herramienta"""
            try:
                logger.info(f"Ejecutando herramienta MCP: {name}")
                logger.debug(f"Argumentos: {arguments}")

                if name == "execute_query":
                    result = await self._execute_query(
                        arguments.get("query"),
                        arguments.get("limit", 100)
                    )
                elif name == "get_table_schema":
                    result = await self._get_table_schema(arguments.get("table_name"))
                elif name == "search_tables":
                    result = await self._search_tables(arguments.get("search_term"))
                elif name == "get_table_relationships":
                    result = await self._get_table_relationships(arguments.get("table_name"))
                elif name == "get_database_summary":
                    result = await self._get_database_summary()
                elif name == "analyze_table_data":
                    result = await self._analyze_table_data(
                        arguments.get("table_name"),
                        arguments.get("sample_size", 1000)
                    )
                else:
                    result = {"error": f"Herramienta desconocida: {name}"}

                return [TextContent(
                    type="text",
                    text=json.dumps(result, ensure_ascii=False, indent=2, default=str)
                )]

            except Exception as e:
                logger.error(f"Error ejecutando herramienta {name}: {e}", exc_info=True)
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": str(e)}, ensure_ascii=False)
                )]

    async def _execute_query(self, query: str, limit: int) -> Dict:
        """Ejecuta una consulta SQL SELECT"""
        try:
            # Validar que sea SELECT
            query_upper = query.strip().upper()
            if not query_upper.startswith("SELECT"):
                return {
                    "error": "Solo se permiten consultas SELECT",
                    "query": query
                }

            # Validar que no tenga operaciones peligrosas
            dangerous_keywords = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE", "TRUNCATE"]
            for keyword in dangerous_keywords:
                if keyword in query_upper:
                    return {
                        "error": f"Palabra clave no permitida: {keyword}",
                        "query": query
                    }

            # Aplicar límite
            if limit > 1000:
                limit = 1000

            # Agregar TOP si no lo tiene
            if "TOP" not in query_upper and "LIMIT" not in query_upper:
                query = query.strip()
                if query.upper().startswith("SELECT"):
                    query = f"SELECT TOP {limit} " + query[6:].strip()

            # Ejecutar query
            with get_db_session() as session:
                from sqlalchemy import text
                result = session.execute(text(query))
                rows = result.fetchall()
                columns = result.keys()

                # Convertir a lista de diccionarios
                data = []
                for row in rows:
                    data.append(dict(zip(columns, row)))

                return {
                    "success": True,
                    "query": query,
                    "rows_returned": len(data),
                    "columns": list(columns),
                    "data": data
                }

        except Exception as e:
            logger.error(f"Error ejecutando query: {e}")
            return {
                "error": str(e),
                "query": query
            }

    async def _get_table_schema(self, table_name: str) -> Dict:
        """Obtiene el esquema de una tabla"""
        try:
            # Buscar tabla (case-insensitive)
            all_tables = db_explorer.get_all_tables()
            actual_table_name = None

            for table in all_tables:
                if table.lower() == table_name.lower():
                    actual_table_name = table
                    break

            if not actual_table_name:
                return {
                    "error": f"Tabla '{table_name}' no encontrada. Usa search_tables o list_tables para ver las tablas disponibles.",
                    "table_name": table_name,
                    "suggestion": f"Intenta buscar con: search_tables('{table_name}')"
                }

            # Obtener info de la tabla
            columns = db_explorer.get_table_columns(actual_table_name)
            pks = db_explorer.get_primary_keys(actual_table_name)
            fks = db_explorer.get_foreign_keys(actual_table_name)
            row_count = db_explorer.get_table_row_count(actual_table_name, use_stats=True)

            return {
                "success": True,
                "table_name": actual_table_name,
                "row_count": row_count or 0,
                "columns": columns,
                "primary_keys": pks,
                "foreign_keys": fks,
                "note": "Revisa los tipos de datos antes de hacer queries. Columnas VARCHAR con fechas necesitan TRY_CONVERT."
            }

        except Exception as e:
            logger.error(f"Error obteniendo esquema de {table_name}: {e}", exc_info=True)
            return {
                "error": f"Error al obtener esquema: {str(e)}",
                "table_name": table_name
            }

    async def _search_tables(self, search_term: str) -> Dict:
        """Busca tablas por término"""
        try:
            all_tables = db_explorer.get_all_tables()
            search_lower = search_term.lower()

            # Buscar coincidencias
            matches = [
                table for table in all_tables
                if search_lower in table.lower()
            ]

            return {
                "success": True,
                "search_term": search_term,
                "matches_found": len(matches),
                "tables": matches[:50]  # Limitar a 50 resultados
            }

        except Exception as e:
            logger.error(f"Error buscando tablas: {e}")
            return {
                "error": str(e),
                "search_term": search_term
            }

    async def _get_table_relationships(self, table_name: str) -> Dict:
        """Obtiene relaciones de una tabla"""
        try:
            relationships = db_explorer.get_table_relationships(table_name)

            return {
                "success": True,
                "table_name": table_name,
                "relationships": relationships
            }

        except Exception as e:
            logger.error(f"Error obteniendo relaciones de {table_name}: {e}")
            return {
                "error": str(e),
                "table_name": table_name
            }

    async def _get_database_summary(self) -> Dict:
        """Obtiene resumen de la base de datos"""
        try:
            summary = db_explorer.get_database_summary()

            return {
                "success": True,
                "summary": summary
            }

        except Exception as e:
            logger.error(f"Error obteniendo resumen de BD: {e}")
            return {
                "error": str(e)
            }

    async def _analyze_table_data(self, table_name: str, sample_size: int) -> Dict:
        """Analiza datos de una tabla"""
        try:
            from sqlalchemy import text

            with get_db_session() as session:
                # Contar registros totales
                count_query = text(f"SELECT COUNT(*) as total FROM [{table_name}]")
                total_rows = session.execute(count_query).scalar()

                # Obtener muestra de datos
                sample_query = text(f"SELECT TOP {sample_size} * FROM [{table_name}]")
                result = session.execute(sample_query)
                columns = result.keys()
                sample_data = result.fetchall()

                # Análisis básico por columna
                column_analysis = {}
                for col in columns:
                    col_values = [row[col] for row in sample_data]
                    null_count = sum(1 for v in col_values if v is None)

                    column_analysis[col] = {
                        "null_count": null_count,
                        "null_percentage": (null_count / len(col_values) * 100) if col_values else 0,
                        "non_null_count": len(col_values) - null_count
                    }

                return {
                    "success": True,
                    "table_name": table_name,
                    "total_rows": total_rows,
                    "sample_size": len(sample_data),
                    "columns": list(columns),
                    "column_analysis": column_analysis
                }

        except Exception as e:
            logger.error(f"Error analizando tabla {table_name}: {e}")
            return {
                "error": str(e),
                "table_name": table_name
            }

    async def run(self, transport_type: str = "stdio"):
        """Ejecuta el servidor MCP"""
        try:
            logger.info(f"Iniciando MCP Server en modo {transport_type}")

            if transport_type == "stdio":
                from mcp.server.stdio import stdio_server
                async with stdio_server() as (read_stream, write_stream):
                    await self.server.run(
                        read_stream,
                        write_stream,
                        self.server.create_initialization_options()
                    )
            else:
                raise ValueError(f"Tipo de transporte no soportado: {transport_type}")

        except Exception as e:
            logger.error(f"Error ejecutando MCP Server: {e}", exc_info=True)
            raise


# Instancia global del servidor MCP
mcp_server = ERPMCPServer()


# Función para iniciar el servidor (usado por el CLI)
async def start_mcp_server():
    """Inicia el servidor MCP"""
    await mcp_server.run()


if __name__ == "__main__":
    # Ejecutar servidor MCP
    asyncio.run(start_mcp_server())
