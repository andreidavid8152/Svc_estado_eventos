from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Configuración del servicio de estado de eventos."""

    # URL del backend Django (se obtiene de la variable de entorno `BACKEND_URL`)
    BACKEND_URL: str = Field(env="BACKEND_URL")

    # Configuración del scheduler
    SCHEDULER_INTERVAL_SECONDS: int = 60  # Por defecto cada minuto
    SCHEDULER_MISFIRE_GRACE_SECONDS: int = 5
    SCHEDULER_COALESCE: bool = True

    # Configuración del servidor
    HOST: str = "0.0.0.0"
    PORT: int = 8001

    # Timeout para requests HTTP
    HTTP_TIMEOUT: int = 30

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
