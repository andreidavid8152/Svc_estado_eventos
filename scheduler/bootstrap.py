import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from settings import settings
from scheduler.jobs.process_events import process_events_sync

logger = logging.getLogger(__name__)

# Instancia global del scheduler
scheduler: BackgroundScheduler = None


def init_scheduler():
    """
    Inicializa y configura el scheduler de APScheduler.
    Se ejecuta al arrancar la aplicación.
    """
    global scheduler

    if scheduler is not None:
        logger.warning("El scheduler ya está inicializado")
        return scheduler

    logger.info("Inicializando APScheduler...")

    scheduler = BackgroundScheduler()

    # Job unificado para procesar eventos (inicio y finalización) de forma secuencial
    scheduler.add_job(
        func=process_events_sync,
        trigger=IntervalTrigger(seconds=settings.SCHEDULER_INTERVAL_SECONDS),
        id="process_events",
        name="Procesar eventos (inicio y finalización)",
        replace_existing=True,
        coalesce=settings.SCHEDULER_COALESCE,
        misfire_grace_time=settings.SCHEDULER_MISFIRE_GRACE_SECONDS,
        max_instances=1,  # Solo permitir una instancia ejecutándose a la vez
    )
    logger.info(
        f"Job 'process_events' programado cada {settings.SCHEDULER_INTERVAL_SECONDS} segundos"
    )

    # Iniciar el scheduler
    scheduler.start()
    logger.info("✓ Scheduler iniciado correctamente")

    return scheduler


def shutdown_scheduler():
    """
    Detiene el scheduler de forma ordenada.
    Se ejecuta al apagar la aplicación.
    """
    global scheduler

    if scheduler is not None:
        logger.info("Deteniendo scheduler...")
        scheduler.shutdown(wait=True)
        scheduler = None
        logger.info("✓ Scheduler detenido")
    else:
        logger.warning("No hay scheduler activo para detener")


def get_scheduler() -> BackgroundScheduler:
    """
    Retorna la instancia del scheduler.
    """
    return scheduler
