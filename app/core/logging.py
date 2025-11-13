"""
Sistema de logging configurado para la aplicación
Soporta logging estructurado (JSON) y formato tradicional
"""
import logging
import sys
from pathlib import Path
from typing import Optional
from pythonjsonlogger import jsonlogger

from app.core.config import settings


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Formateador JSON personalizado para logs"""

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)

        # Agregar campos personalizados
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno

        # Agregar información del proyecto
        log_record['project'] = settings.project_name
        log_record['environment'] = settings.environment


def setup_logging(
    name: Optional[str] = None,
    level: Optional[str] = None,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Configura el sistema de logging

    Args:
        name: Nombre del logger (si None, usa el root logger)
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Archivo donde guardar logs (si None, usa settings.log_file)

    Returns:
        Logger configurado
    """
    # Obtener logger
    logger = logging.getLogger(name)

    # Limpiar handlers existentes
    logger.handlers = []

    # Configurar nivel
    log_level = level or settings.log_level
    logger.setLevel(getattr(logging, log_level))

    # Evitar propagación para no duplicar logs
    logger.propagate = False

    # === Handler para consola ===
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level))

    if settings.log_format == "json":
        # Formato JSON para producción
        json_formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(message)s'
        )
        console_handler.setFormatter(json_formatter)
    else:
        # Formato tradicional para desarrollo
        console_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)

    logger.addHandler(console_handler)

    # === Handler para archivo ===
    if log_file or settings.log_file:
        file_path = Path(log_file or settings.log_file)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(file_path, encoding='utf-8')
        file_handler.setLevel(getattr(logging, log_level))

        if settings.log_format == "json":
            file_handler.setFormatter(json_formatter)
        else:
            file_handler.setFormatter(console_format)

        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger con el nombre especificado

    Args:
        name: Nombre del logger (típicamente __name__)

    Returns:
        Logger configurado
    """
    return logging.getLogger(name)


# Logger principal de la aplicación
app_logger = setup_logging("agente_erp")


# Función helper para logging con contexto
def log_with_context(
    logger: logging.Logger,
    level: str,
    message: str,
    **context
):
    """
    Log con contexto adicional

    Args:
        logger: Logger a usar
        level: Nivel del log (info, warning, error, etc.)
        message: Mensaje del log
        **context: Contexto adicional como key-value pairs
    """
    log_method = getattr(logger, level.lower())

    if settings.log_format == "json":
        log_method(message, extra=context)
    else:
        context_str = " | ".join(f"{k}={v}" for k, v in context.items())
        log_method(f"{message} | {context_str}")


# Ejemplo de uso
if __name__ == "__main__":
    # Test de logging
    test_logger = setup_logging("test")

    test_logger.debug("Mensaje de debug")
    test_logger.info("Mensaje de info")
    test_logger.warning("Mensaje de advertencia")
    test_logger.error("Mensaje de error")

    # Con contexto
    log_with_context(
        test_logger,
        "info",
        "Query ejecutada",
        query="SELECT * FROM table",
        duration_ms=125,
        rows=50
    )
