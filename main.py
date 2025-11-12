import logging
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from settings import settings
from routers import health
from scheduler.bootstrap import init_scheduler, shutdown_scheduler

# Configurar logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Contexto de vida de la aplicación.
    Se ejecuta al iniciar y al cerrar el servidor.
    """
    # Startup
    logger.info("=== Iniciando servicio de estado de eventos ===")
    logger.info(f"Backend URL: {settings.BACKEND_URL}")
    logger.info(
        f"Intervalo del scheduler: {settings.SCHEDULER_INTERVAL_SECONDS} segundos"
    )

    # Inicializar el scheduler
    init_scheduler()

    logger.info("=== Servicio iniciado correctamente ===")

    yield

    # Shutdown
    logger.info("=== Deteniendo servicio de estado de eventos ===")
    shutdown_scheduler()
    logger.info("=== Servicio detenido ===")


# Crear aplicación FastAPI
app = FastAPI(
    title="Servicio de Estado de Eventos",
    description="Microservicio para actualizar automáticamente los estados de los eventos",
    version="1.0.0",
    lifespan=lifespan,
)

# Registrar routers
app.include_router(health.router, tags=["Health"])


@app.get("/")
async def root():
    """Endpoint raíz."""
    return {
        "service": "Estado de Eventos",
        "version": "1.0.0",
        "status": "running",
        "scheduler_interval_seconds": settings.SCHEDULER_INTERVAL_SECONDS,
    }


if __name__ == "__main__":

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False,  # No usar reload con APScheduler
        log_level=settings.LOG_LEVEL.lower(),
    )
