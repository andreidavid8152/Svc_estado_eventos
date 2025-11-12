from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración del servicio de estado de eventos."""

    # URL del backend Django
    BACKEND_URL: str = "http://localhost:8000"

    # Configuración del scheduler
    SCHEDULER_INTERVAL_SECONDS: int = 60  # Por defecto cada minuto

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
