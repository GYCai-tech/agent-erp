"""
Cliente para conectar con la API FastAPI del Agente ERP
"""
import os
import requests
from typing import Dict, List, Any, Optional


class ERPApiClient:
    """Cliente simple para la API del ERP"""

    def __init__(self, base_url: str = None):
        if base_url is None:
            base_url = os.getenv("API_URL", "http://localhost:8000")
        self.base_url = base_url.rstrip("/")
        self.api_base = f"{self.base_url}/api/v1"

    def health_check(self) -> Dict:
        """Verificar estado de la API"""
        try:
            response = requests.get(f"{self.api_base}/health", timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def get_database_summary(self) -> Dict:
        """Obtener resumen de la base de datos"""
        try:
            response = requests.get(f"{self.api_base}/database/summary", timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def get_tables(self) -> List[str]:
        """Obtener lista de tablas"""
        try:
            response = requests.get(f"{self.api_base}/database/tables", timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return []

    def get_table_info(self, table_name: str) -> Dict:
        """Obtener información de una tabla específica"""
        try:
            response = requests.get(f"{self.api_base}/database/tables/{table_name}", timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def get_table_sample(self, table_name: str, limit: int = 10) -> Dict:
        """Obtener muestra de datos de una tabla"""
        try:
            response = requests.get(
                f"{self.api_base}/database/tables/{table_name}/sample",
                params={"limit": limit},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def search_tables(self, search_term: str) -> List[str]:
        """Buscar tablas por nombre"""
        try:
            response = requests.get(
                f"{self.api_base}/database/search/tables/{search_term}",
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return []

    def get_monitoring_stats(self) -> Dict:
        """Obtener estadísticas de uso"""
        try:
            response = requests.get(f"{self.api_base}/monitoring/stats", timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def chat_with_agent(self, message: str, conversation_history: Optional[List] = None) -> Dict:
        """Chat con el agente ERP usando MCP"""
        try:
            payload = {
                "message": message,
                "conversation_history": conversation_history or []
            }
            response = requests.post(
                f"{self.api_base}/chat/",
                json=payload,
                timeout=60  # Chat puede tomar más tiempo
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    def check_chat_health(self) -> Dict:
        """Verificar salud del chat MCP"""
        try:
            response = requests.get(f"{self.api_base}/chat/health", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e), "mcp_enabled": False}


# Instancia global del cliente
api_client = ERPApiClient()
