import asyncio
import logging
from clients.backend_api import backend_client

logger = logging.getLogger(__name__)


async def start_pending_events():
    """
    Job que se ejecuta periódicamente para iniciar eventos programados
    cuyo start_date ya llegó.
    """
    logger.info("Ejecutando job: start_pending_events")

    try:
        # Obtener eventos pendientes de inicio
        pending_events = await backend_client.get_pending_start_events()

        if not pending_events:
            logger.info("No hay eventos pendientes de inicio")
            return

        logger.info(
            f"Se encontraron {len(pending_events)} evento(s) pendiente(s) de inicio"
        )

        # Iniciar cada evento
        for event in pending_events:
            event_id = event.get("id")
            start_date = event.get("start_date")

            logger.info(
                f"Intentando iniciar evento {event_id} (fecha inicio: {start_date})"
            )

            success = await backend_client.start_event(event_id)

            if success:
                logger.info(f"✓ Evento {event_id} iniciado exitosamente")
            else:
                logger.warning(f"✗ No se pudo iniciar el evento {event_id}")

        logger.info("Job start_pending_events completado")

    except Exception as e:
        logger.error(f"Error en job start_pending_events: {e}", exc_info=True)


def start_pending_events_sync():
    """
    Wrapper síncrono para el job asíncrono.
    APScheduler ejecutará esta función.
    """
    asyncio.run(start_pending_events())
