"""
Configuración central de la aplicación usando Pydantic Settings
"""
from typing import List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    """Configuración de la aplicación"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Proyecto
    project_name: str = Field(default="Agente ERP", env="PROJECT_NAME")
    version: str = Field(default="1.0.0", env="VERSION")
    environment: str = Field(default="development", env="ENVIRONMENT")

    # FastAPI
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_reload: bool = Field(default=True, env="API_RELOAD")
    api_debug: bool = Field(default=True, env="API_DEBUG")

    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        env="CORS_ORIGINS"
    )
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")

    # Base de datos
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    db_server: str = Field(default="SRVAHORA", env="DB_SERVER")
    db_database: str = Field(default="GOMEZYCRESPO_PRUEBAS", env="DB_DATABASE")
    db_username: str = Field(default="sa", env="DB_USERNAME")
    db_password: str = Field(default="", env="DB_PASSWORD")
    db_driver: str = Field(default="ODBC Driver 18 for SQL Server", env="DB_DRIVER")
    db_trust_certificate: bool = Field(default=True, env="DB_TRUST_CERTIFICATE")
    db_read_only: bool = Field(default=True, env="DB_READ_ONLY")

    # OpenAI
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4-turbo-preview", env="OPENAI_MODEL")
    openai_temperature: float = Field(default=0.1, env="OPENAI_TEMPERATURE")

    # Anthropic (opcional)
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-3-opus-20240229", env="ANTHROPIC_MODEL")

    # MCP
    mcp_enabled: bool = Field(default=True, env="MCP_ENABLED")
    mcp_port: int = Field(default=8001, env="MCP_PORT")
    mcp_host: str = Field(default="0.0.0.0", env="MCP_HOST")

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs/agente_erp.log", env="LOG_FILE")
    log_format: str = Field(default="json", env="LOG_FORMAT")

    # Monitoreo
    enable_monitoring: bool = Field(default=True, env="ENABLE_MONITORING")
    track_token_usage: bool = Field(default=True, env="TRACK_TOKEN_USAGE")

    # Límites
    max_tokens_per_request: int = Field(default=4000, env="MAX_TOKENS_PER_REQUEST")
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")

    # Seguridad
    api_key_required: bool = Field(default=False, env="API_KEY_REQUIRED")
    api_key: Optional[str] = Field(default=None, env="API_KEY")

    # Caché
    enable_cache: bool = Field(default=False, env="ENABLE_CACHE")
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")

    # Qdrant (futuro)
    qdrant_host: str = Field(default="localhost", env="QDRANT_HOST")
    qdrant_port: int = Field(default=6333, env="QDRANT_PORT")
    qdrant_collection: str = Field(default="erp_schemas", env="QDRANT_COLLECTION")

    @validator("log_level")
    def validate_log_level(cls, v):
        """Valida que el nivel de log sea válido"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level debe ser uno de: {', '.join(valid_levels)}")
        return v.upper()

    @validator("environment")
    def validate_environment(cls, v):
        """Valida que el entorno sea válido"""
        valid_envs = ["development", "staging", "production"]
        if v.lower() not in valid_envs:
            raise ValueError(f"environment debe ser uno de: {', '.join(valid_envs)}")
        return v.lower()

    @property
    def database_connection_string(self) -> str:
        """Construye la cadena de conexión a la base de datos"""
        if self.database_url:
            return self.database_url

        # Construir desde componentes individuales
        trust_cert = "yes" if self.db_trust_certificate else "no"
        return (
            f"mssql+pyodbc://{self.db_username}:{self.db_password}"
            f"@{self.db_server}/{self.db_database}"
            f"?driver={self.db_driver.replace(' ', '+')}"
            f"&TrustServerCertificate={trust_cert}"
        )

    @property
    def pyodbc_connection_string(self) -> str:
        """Cadena de conexión para pyodbc directo"""
        trust_cert = "yes" if self.db_trust_certificate else "no"
        return (
            f"DRIVER={{{self.db_driver}}};"
            f"SERVER={self.db_server};"
            f"DATABASE={self.db_database};"
            f"UID={self.db_username};"
            f"PWD={self.db_password};"
            f"TrustServerCertificate={trust_cert};"
        )

    @property
    def is_production(self) -> bool:
        """Indica si estamos en producción"""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Indica si estamos en desarrollo"""
        return self.environment == "development"

    def get_log_file_path(self) -> Path:
        """Retorna Path del archivo de log"""
        log_path = Path(self.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        return log_path


# Instancia global de configuración
settings = Settings()


# Validación de configuración crítica al importar
def validate_critical_config():
    """Valida que la configuración crítica esté presente"""
    errors = []

    if not settings.db_password:
        errors.append("DB_PASSWORD no está configurada")

    if not settings.openai_api_key and not settings.anthropic_api_key:
        errors.append("Debe configurar OPENAI_API_KEY o ANTHROPIC_API_KEY")

    if settings.db_read_only is False and settings.is_production:
        errors.append("ADVERTENCIA: DB_READ_ONLY está desactivado en producción")

    if errors:
        error_msg = "\n".join(f"  - {err}" for err in errors)
        raise ValueError(
            f"Errores de configuración:\n{error_msg}\n\n"
            f"Por favor, revisa tu archivo .env"
        )


# Ejecutar validación al importar (en desarrollo)
if not settings.is_production:
    try:
        validate_critical_config()
    except ValueError as e:
        print(f"\n⚠️  {str(e)}\n")
