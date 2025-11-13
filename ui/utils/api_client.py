"""
Cliente para conectar con la API FastAPI del Agente ERP
"""
import requests
from typing import Dict, List, Any, Optional


class ERPApiClient:
    """Cliente simple para la API del ERP"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.api_base = f"{self.base_url}/api/v1"

    def health_check(self) -> Dict:
        """Verificar estado de la API"""
        try:
            response = requests.get(f"{self.api_base}/health", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def get_database_summary(self) -> Dict:
        """Obtener resumen de la base de datos"""
        try:
            response = requests.get(f"{self.api_base}/database/summary", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def get_tables(self) -> List[str]:
        """Obtener lista de tablas"""
        try:
            response = requests.get(f"{self.api_base}/database/tables", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return []

    def get_table_info(self, table_name: str) -> Dict:
        """Obtener información de una tabla específica"""
        try:
            response = requests.get(f"{self.api_base}/database/tables/{table_name}", timeout=10)
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
                timeout=10
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
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return []

    def get_monitoring_stats(self) -> Dict:
        """Obtener estadísticas de uso"""
        try:
            response = requests.get(f"{self.api_base}/monitoring/stats", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}


# Instancia global del cliente
api_client = ERPApiClient()
