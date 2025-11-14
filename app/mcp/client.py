"""
Cliente MCP para usar desde FastAPI
Permite hacer consultas al MCP Server usando Groq
Inspirado en la arquitectura del rag-mvp
"""

import json
import time
from typing import Dict, List, Any, Optional
from groq import Groq

from app.core.config import settings
from app.core.logging import get_logger
from app.core.monitoring import usage_tracker

logger = get_logger(__name__)


class MCPClient:
    """Cliente para interactuar con MCP Server a través de LLM"""

    def __init__(self):
        self.groq_client = Groq(api_key=settings.groq_api_key)
        self.model = settings.groq_model
        self.tools = []
        self._load_tools()
        logger.info(f"MCP Client inicializado con modelo: {self.model}")

    def _load_tools(self):
        """Carga las herramientas disponibles para Groq function calling"""
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "execute_query",
                    "description": "Ejecuta una consulta SQL SELECT de solo lectura en la base de datos del ERP. Devuelve los resultados en formato JSON. IMPORTANTE: Solo SELECT, no INSERT/UPDATE/DELETE.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Query SQL SELECT a ejecutar (SOLO lectura). Ejemplo: SELECT TOP 10 * FROM Clientes"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Límite de resultados a devolver (default: 100, máximo: 1000)",
                                "default": 100
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_table_schema",
                    "description": "Obtiene el schema completo de una tabla específica del ERP: columnas, tipos de datos, claves primarias, claves foráneas y relaciones.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "table_name": {
                                "type": "string",
                                "description": "Nombre EXACTO de la tabla (case-sensitive). Ejemplo: 'A_Facturas' o 'Clientes'"
                            }
                        },
                        "required": ["table_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_tables",
                    "description": "Lista TODAS las tablas disponibles en la base de datos del ERP. Usa esto primero si no sabes qué tablas existen.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_tables",
                    "description": "Busca tablas en la base de datos del ERP por nombre o patrón. Usa esto cuando no sepas el nombre exacto de una tabla.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "search_term": {
                                "type": "string",
                                "description": "Término de búsqueda (ej: 'factura', 'cliente', 'pedido'). NO case-sensitive."
                            }
                        },
                        "required": ["search_term"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_table_sample",
                    "description": "Obtiene una MUESTRA de datos de una tabla (primeras N filas) para entender su contenido y estructura.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "table_name": {
                                "type": "string",
                                "description": "Nombre de la tabla"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Número de filas a obtener (default: 5, máximo: 50)",
                                "default": 5
                            }
                        },
                        "required": ["table_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_database_summary",
                    "description": "Obtiene un resumen general de la base de datos: número total de tablas, tablas con más registros, estructura general.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            }
        ]

    async def _execute_mcp_tool(self, tool_name: str, arguments: Dict) -> Dict:
        """Ejecuta una herramienta MCP y retorna el resultado"""
        try:
            # Importar el servidor MCP
            from app.mcp.server import mcp_server

            logger.info(f"🔧 Ejecutando: {tool_name} con args: {arguments}")

            # Ejecutar la herramienta correspondiente
            if tool_name == "execute_query":
                result = await mcp_server._execute_query(
                    arguments.get("query"),
                    arguments.get("limit", 100)
                )
            elif tool_name == "get_table_schema":
                result = await mcp_server._get_table_schema(
                    arguments.get("table_name")
                )
            elif tool_name == "list_tables":
                # Listar todas las tablas
                from app.database.explorer import db_explorer
                tables = db_explorer.get_all_tables()
                result = {
                    "success": True,
                    "total_tables": len(tables),
                    "tables": tables
                }
            elif tool_name == "search_tables":
                result = await mcp_server._search_tables(
                    arguments.get("search_term")
                )
            elif tool_name == "get_table_sample":
                table_name = arguments.get("table_name")
                limit = arguments.get("limit", 5)
                # Obtener muestra usando execute_query
                query = f"SELECT TOP {limit} * FROM [{table_name}]"
                result = await mcp_server._execute_query(query, limit)
            elif tool_name == "get_database_summary":
                result = await mcp_server._get_database_summary()
            else:
                result = {"error": f"Herramienta desconocida: {tool_name}"}

            return result

        except Exception as e:
            logger.error(f"❌ Error ejecutando {tool_name}: {e}", exc_info=True)
            return {"error": str(e)}

    async def chat(
        self,
        message: str,
        conversation_history: Optional[List[Dict]] = None,
        max_iterations: int = 10
    ) -> Dict[str, Any]:
        """
        Procesa un mensaje usando Groq con acceso a herramientas MCP

        Args:
            message: Mensaje del usuario
            conversation_history: Historial de conversación previo
            max_iterations: Máximo de iteraciones para tool calling

        Returns:
            Dict con la respuesta y metadatos
        """
        start_time = time.time()

        try:
            # Preparar mensajes
            messages = conversation_history or []

            # System prompt mejorado (inspirado en rag-mvp)
            system_message = {
                "role": "system",
                "content": """Eres un asistente experto en bases de datos SQL Server y sistemas ERP de Gómez y Crespo.
Tienes acceso directo a la base de datos GOMEZYCRESPO_PRUEBAS mediante herramientas especializadas.

**Tu proceso de trabajo:**
1. **Primero**, si no conoces las tablas relevantes, usa `search_tables` o `list_tables`
2. **Luego**, obtén el schema con `get_table_schema` para entender la estructura y tipos de datos
3. **Opcionalmente**, usa `get_table_sample` para ver ejemplos de datos reales
4. **Después**, construye y ejecuta la query SQL con `execute_query`
5. **Finalmente**, presenta los resultados de forma clara y profesional

**Reglas CRÍTICAS de SQL Server:**
- SOLO puedes ejecutar consultas SELECT (lectura solamente)
- Los nombres de tabla en SQL Server son case-sensitive, usa corchetes: [Nombre_Tabla]
- Usa TOP N en lugar de LIMIT en SQL Server
- Para fechas: Usa formato ISO 'YYYY-MM-DD' y CAST si es necesario
- NUNCA uses BETWEEN con fechas VARCHAR, primero conviértelas con CONVERT o TRY_CONVERT
- Para campos de texto que parecen fechas: usa TRY_CONVERT(DATE, campo) o TRY_CAST(campo AS DATE)
- Si una columna es VARCHAR pero contiene fechas, SIEMPRE usa TRY_CONVERT antes de comparar
- Si una tabla no existe, busca alternativas similares
- Si hay un error de conversión de datos, revisa los tipos de columna y ajusta la query

**Ejemplo de manejo de fechas VARCHAR:**
```sql
-- MAL (causa error de conversión):
WHERE FechaFact BETWEEN '2023-01-01' AND '2023-12-31'

-- BIEN (convierte primero):
WHERE TRY_CONVERT(DATE, FechaFact, 103) BETWEEN '2023-01-01' AND '2023-12-31'
-- O verifica el schema primero para saber el tipo real
```

**Cuando encuentres un error:**
1. Lee el mensaje de error cuidadosamente
2. Si es error de conversión de tipos, revisa el schema de la tabla
3. Ajusta la query según los tipos de datos reales
4. Explica al usuario qué salió mal y cómo lo solucionaste

**Estilo de respuesta:**
- Sé conciso pero informativo
- Usa formato markdown para tablas y listas
- Muestra números con formato legible (ej: 1,234 en lugar de 1234)
- Si hay errores, explícalos claramente y muestra la solución

Base de datos: GOMEZYCRESPO_PRUEBAS (SQL Server)
"""
            }

            if not messages or messages[0].get("role") != "system":
                messages.insert(0, system_message)

            # Agregar mensaje del usuario
            messages.append({
                "role": "user",
                "content": message
            })

            # Tracking de herramientas usadas
            tools_used = []
            iterations = 0

            # Loop de tool calling
            while iterations < max_iterations:
                iterations += 1
                logger.info(f"📍 Iteración {iterations}/{max_iterations}")

                # Llamar a Groq
                response = self.groq_client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=self.tools,
                    tool_choice="auto",
                    temperature=settings.groq_temperature
                )

                response_message = response.choices[0].message

                # Si no hay tool calls, retornar respuesta
                if not response_message.tool_calls:
                    logger.info(f"✅ Respuesta final obtenida en iteración {iterations}")
                    duration_ms = (time.time() - start_time) * 1000

                    return {
                        "success": True,
                        "response": response_message.content,
                        "tools_used": tools_used,
                        "iterations": iterations,
                        "duration_ms": duration_ms,
                        "conversation_history": messages + [response_message.model_dump()]
                    }

                # Agregar mensaje del asistente
                messages.append(response_message.model_dump())

                # Log de herramientas que se van a llamar
                tool_names = [tc.function.name for tc in response_message.tool_calls]
                logger.info(f"🔧 Llamando {len(tool_names)} herramienta(s): {', '.join(tool_names)}")

                # Ejecutar tool calls
                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)

                    logger.info(f"🔧 LLM solicita: {function_name}({function_args})")

                    # Ejecutar herramienta MCP
                    tool_result = await self._execute_mcp_tool(function_name, function_args)

                    # Registrar uso
                    tools_used.append({
                        "name": function_name,
                        "arguments": function_args,
                        "result": tool_result
                    })

                    # Agregar resultado al historial
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": json.dumps(tool_result, ensure_ascii=False, default=str)
                    })

            # Límite de iteraciones alcanzado
            duration_ms = (time.time() - start_time) * 1000

            logger.warning(f"⚠️ Límite de {max_iterations} iteraciones alcanzado")
            logger.warning(f"Herramientas usadas: {[t['name'] for t in tools_used]}")

            return {
                "success": False,
                "error": f"Límite de {max_iterations} iteraciones alcanzado. La consulta requirió demasiados pasos. Intenta ser más específico o dividir la pregunta en partes más pequeñas.",
                "tools_used": tools_used,
                "iterations": iterations,
                "duration_ms": duration_ms
            }

        except Exception as e:
            logger.error(f"❌ Error en chat MCP: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "tools_used": [],
                "iterations": 0
            }


# Instancia global del cliente
mcp_client = MCPClient()
