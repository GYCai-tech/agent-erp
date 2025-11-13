"""
Explorador de base de datos
Permite descubrir la estructura de la BD: tablas, columnas, relaciones, etc.
"""
from typing import List, Dict, Optional, Tuple
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
import pandas as pd

from app.database.connection import db_manager, get_db_session
from app.core.logging import get_logger

logger = get_logger(__name__)


class DatabaseExplorer:
    """Explorador de estructura de base de datos"""

    def __init__(self):
        self.engine: Engine = db_manager.get_engine()
        self.inspector = inspect(self.engine)

    def get_all_tables(self) -> List[str]:
        """
        Obtiene lista de todas las tablas

        Returns:
            Lista de nombres de tablas
        """
        try:
            tables = self.inspector.get_table_names()
            logger.info(f"Encontradas {len(tables)} tablas")
            return sorted(tables)
        except Exception as e:
            logger.error(f"Error al obtener tablas: {e}")
            return []

    def get_table_columns(self, table_name: str) -> List[Dict]:
        """
        Obtiene información de las columnas de una tabla

        Args:
            table_name: Nombre de la tabla

        Returns:
            Lista de diccionarios con info de columnas
        """
        try:
            columns = self.inspector.get_columns(table_name)

            result = []
            for col in columns:
                result.append({
                    'name': col['name'],
                    'type': str(col['type']),
                    'nullable': col['nullable'],
                    'default': col.get('default'),
                    'autoincrement': col.get('autoincrement', False)
                })

            return result
        except Exception as e:
            logger.error(f"Error al obtener columnas de {table_name}: {e}")
            return []

    def get_primary_keys(self, table_name: str) -> List[str]:
        """
        Obtiene las primary keys de una tabla

        Args:
            table_name: Nombre de la tabla

        Returns:
            Lista de nombres de columnas que son PK
        """
        try:
            pk = self.inspector.get_pk_constraint(table_name)
            return pk.get('constrained_columns', [])
        except Exception as e:
            logger.error(f"Error al obtener PK de {table_name}: {e}")
            return []

    def get_foreign_keys(self, table_name: str) -> List[Dict]:
        """
        Obtiene las foreign keys de una tabla

        Args:
            table_name: Nombre de la tabla

        Returns:
            Lista de diccionarios con info de FK
        """
        try:
            fks = self.inspector.get_foreign_keys(table_name)

            result = []
            for fk in fks:
                result.append({
                    'name': fk.get('name'),
                    'constrained_columns': fk.get('constrained_columns', []),
                    'referred_table': fk.get('referred_table'),
                    'referred_columns': fk.get('referred_columns', [])
                })

            return result
        except Exception as e:
            logger.error(f"Error al obtener FK de {table_name}: {e}")
            return []

    def get_table_row_count(self, table_name: str) -> Optional[int]:
        """
        Cuenta el número de filas en una tabla

        Args:
            table_name: Nombre de la tabla

        Returns:
            Número de filas o None si hay error
        """
        try:
            with get_db_session() as session:
                result = session.execute(
                    text(f"SELECT COUNT(*) FROM [{table_name}]")
                )
                count = result.scalar()
                return count
        except Exception as e:
            logger.error(f"Error al contar filas de {table_name}: {e}")
            return None

    def get_table_sample(
        self,
        table_name: str,
        limit: int = 5
    ) -> Optional[pd.DataFrame]:
        """
        Obtiene una muestra de datos de una tabla

        Args:
            table_name: Nombre de la tabla
            limit: Número de filas a obtener

        Returns:
            DataFrame con muestra de datos
        """
        try:
            with get_db_session() as session:
                query = f"SELECT TOP {limit} * FROM [{table_name}]"
                df = pd.read_sql(text(query), session.bind)
                return df
        except Exception as e:
            logger.error(f"Error al obtener muestra de {table_name}: {e}")
            return None

    def get_table_info(self, table_name: str) -> Dict:
        """
        Obtiene información completa de una tabla

        Args:
            table_name: Nombre de la tabla

        Returns:
            Diccionario con toda la información de la tabla
        """
        logger.info(f"Obteniendo información de tabla: {table_name}")

        info = {
            'name': table_name,
            'columns': self.get_table_columns(table_name),
            'primary_keys': self.get_primary_keys(table_name),
            'foreign_keys': self.get_foreign_keys(table_name),
            'row_count': self.get_table_row_count(table_name)
        }

        return info

    def get_all_tables_info(self) -> List[Dict]:
        """
        Obtiene información de todas las tablas

        Returns:
            Lista con información de todas las tablas
        """
        logger.info("Explorando todas las tablas...")

        tables = self.get_all_tables()
        tables_info = []

        for table_name in tables:
            info = self.get_table_info(table_name)
            tables_info.append(info)

        logger.info(f"Exploración completada: {len(tables_info)} tablas")
        return tables_info

    def search_tables_by_name(self, search_term: str) -> List[str]:
        """
        Busca tablas por nombre

        Args:
            search_term: Término de búsqueda

        Returns:
            Lista de tablas que coinciden
        """
        all_tables = self.get_all_tables()
        matching = [
            table for table in all_tables
            if search_term.lower() in table.lower()
        ]
        return matching

    def search_columns(self, search_term: str) -> List[Dict]:
        """
        Busca columnas por nombre en todas las tablas

        Args:
            search_term: Término de búsqueda

        Returns:
            Lista de diccionarios con tabla y columna
        """
        logger.info(f"Buscando columnas con término: {search_term}")

        results = []
        tables = self.get_all_tables()

        for table in tables:
            columns = self.get_table_columns(table)
            for col in columns:
                if search_term.lower() in col['name'].lower():
                    results.append({
                        'table': table,
                        'column': col['name'],
                        'type': col['type'],
                        'nullable': col['nullable']
                    })

        logger.info(f"Encontradas {len(results)} coincidencias")
        return results

    def get_table_relationships(self, table_name: str) -> Dict:
        """
        Obtiene las relaciones de una tabla (incoming y outgoing)

        Args:
            table_name: Nombre de la tabla

        Returns:
            Diccionario con relaciones
        """
        # Relaciones salientes (esta tabla -> otras tablas)
        outgoing = self.get_foreign_keys(table_name)

        # Relaciones entrantes (otras tablas -> esta tabla)
        incoming = []
        all_tables = self.get_all_tables()

        for other_table in all_tables:
            if other_table == table_name:
                continue

            fks = self.get_foreign_keys(other_table)
            for fk in fks:
                if fk['referred_table'] == table_name:
                    incoming.append({
                        'from_table': other_table,
                        'from_columns': fk['constrained_columns'],
                        'to_columns': fk['referred_columns']
                    })

        return {
            'table': table_name,
            'outgoing_relationships': outgoing,
            'incoming_relationships': incoming
        }

    def get_database_summary(self) -> Dict:
        """
        Obtiene un resumen general de la base de datos

        Returns:
            Diccionario con resumen
        """
        logger.info("Generando resumen de base de datos...")

        tables = self.get_all_tables()

        total_rows = 0
        tables_with_data = 0

        for table in tables:
            count = self.get_table_row_count(table)
            if count and count > 0:
                tables_with_data += 1
                total_rows += count

        summary = {
            'total_tables': len(tables),
            'tables_with_data': tables_with_data,
            'total_rows': total_rows,
            'tables': tables[:10]  # Primeras 10 tablas
        }

        logger.info(f"Base de datos: {len(tables)} tablas, {total_rows:,} filas totales")

        return summary


# Instancia global del explorador
db_explorer = DatabaseExplorer()
