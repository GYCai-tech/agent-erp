"""
Manejo de conexiones a la base de datos SQL Server
Usa SQLAlchemy para ORM y pyodbc para conexiones directas
"""
from typing import Generator, Optional
from sqlalchemy import create_engine, text, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import pyodbc

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


# ============================================================================
# SQLALCHEMY ENGINE
# ============================================================================

class DatabaseManager:
    """Gestor de conexiones a la base de datos"""

    def __init__(self):
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None

    def get_engine(self) -> Engine:
        """
        Obtiene o crea el engine de SQLAlchemy

        Returns:
            Engine configurado
        """
        if self._engine is None:
            logger.info("Creando engine de base de datos")

            try:
                self._engine = create_engine(
                    settings.database_connection_string,
                    poolclass=QueuePool,
                    pool_size=5,
                    max_overflow=10,
                    pool_timeout=30,
                    pool_recycle=3600,
                    echo=settings.is_development,  # SQL logging en desarrollo
                )

                # Event listener para logging
                @event.listens_for(self._engine, "connect")
                def receive_connect(dbapi_conn, connection_record):
                    logger.debug("Nueva conexión a la base de datos establecida")

                # Verificar conexión
                with self._engine.connect() as conn:
                    conn.execute(text("SELECT 1"))

                logger.info("✓ Engine de base de datos creado exitosamente")

            except Exception as e:
                logger.error(f"✗ Error al crear engine de base de datos: {e}")
                raise

        return self._engine

    def get_session_factory(self) -> sessionmaker:
        """
        Obtiene el factory de sesiones

        Returns:
            Session factory
        """
        if self._session_factory is None:
            engine = self.get_engine()
            self._session_factory = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=engine
            )
            logger.info("Session factory creado")

        return self._session_factory

    def close(self):
        """Cierra todas las conexiones"""
        if self._engine:
            self._engine.dispose()
            logger.info("Engine de base de datos cerrado")
            self._engine = None
            self._session_factory = None


# Instancia global
db_manager = DatabaseManager()


# ============================================================================
# DEPENDENCY INJECTION PARA FASTAPI
# ============================================================================

def get_db() -> Generator[Session, None, None]:
    """
    Dependency para obtener sesión de base de datos en FastAPI

    Yields:
        Session de SQLAlchemy

    Ejemplo:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            result = db.execute(text("SELECT * FROM table"))
    """
    session_factory = db_manager.get_session_factory()
    session = session_factory()

    try:
        yield session
    finally:
        session.close()


# ============================================================================
# CONTEXT MANAGERS
# ============================================================================

@contextmanager
def get_db_session():
    """
    Context manager para obtener sesión de base de datos

    Yields:
        Session de SQLAlchemy

    Ejemplo:
        with get_db_session() as session:
            result = session.execute(text("SELECT * FROM table"))
    """
    session_factory = db_manager.get_session_factory()
    session = session_factory()

    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error en sesión de base de datos: {e}")
        raise
    finally:
        session.close()


# ============================================================================
# CONEXIONES PYODBC DIRECTAS
# ============================================================================

def get_pyodbc_connection() -> pyodbc.Connection:
    """
    Obtiene una conexión pyodbc directa
    Útil para operaciones que no requieren ORM

    Returns:
        Conexión pyodbc

    Ejemplo:
        conn = get_pyodbc_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM table")
            rows = cursor.fetchall()
        finally:
            conn.close()
    """
    try:
        conn = pyodbc.connect(settings.pyodbc_connection_string)
        logger.debug("Conexión pyodbc establecida")
        return conn
    except Exception as e:
        logger.error(f"Error al conectar con pyodbc: {e}")
        raise


@contextmanager
def get_pyodbc_session():
    """
    Context manager para conexión pyodbc

    Yields:
        Conexión pyodbc

    Ejemplo:
        with get_pyodbc_session() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM table")
            rows = cursor.fetchall()
    """
    conn = None
    try:
        conn = get_pyodbc_connection()
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error en conexión pyodbc: {e}")
        raise
    finally:
        if conn:
            conn.close()
            logger.debug("Conexión pyodbc cerrada")


# ============================================================================
# UTILIDADES
# ============================================================================

def test_connection() -> bool:
    """
    Prueba la conexión a la base de datos

    Returns:
        True si la conexión fue exitosa, False en caso contrario
    """
    try:
        logger.info("Probando conexión a la base de datos...")

        with get_db_session() as session:
            result = session.execute(text("SELECT @@VERSION"))
            version = result.scalar()

            logger.info(f"✓ Conexión exitosa")
            logger.info(f"  SQL Server Version: {version[:100]}...")

        return True

    except Exception as e:
        logger.error(f"✗ Error al probar conexión: {e}")
        return False


def execute_query(query: str, params: Optional[dict] = None) -> list:
    """
    Ejecuta una consulta SQL y retorna resultados

    Args:
        query: Consulta SQL
        params: Parámetros de la consulta (opcional)

    Returns:
        Lista de filas (como tuplas)

    Example:
        rows = execute_query("SELECT * FROM table WHERE id = :id", {"id": 123})
    """
    try:
        with get_db_session() as session:
            if params:
                result = session.execute(text(query), params)
            else:
                result = session.execute(text(query))

            rows = result.fetchall()
            logger.debug(f"Query ejecutada: {len(rows)} filas retornadas")

            return rows

    except Exception as e:
        logger.error(f"Error al ejecutar query: {e}")
        raise


# ============================================================================
# STARTUP Y SHUTDOWN
# ============================================================================

async def startup_db():
    """Inicializa la conexión a la base de datos al arrancar"""
    logger.info("Inicializando conexión a base de datos...")

    try:
        db_manager.get_engine()
        success = test_connection()

        if success:
            logger.info("✓ Base de datos inicializada correctamente")
        else:
            logger.warning("⚠ Conexión a base de datos falló en startup")

    except Exception as e:
        logger.warning(f"⚠ No se pudo conectar a la base de datos: {e}")
        logger.warning("⚠ La aplicación continuará sin base de datos")


async def shutdown_db():
    """Cierra las conexiones al apagar"""
    logger.info("Cerrando conexiones a base de datos...")
    db_manager.close()
    logger.info("✓ Conexiones cerradas")
