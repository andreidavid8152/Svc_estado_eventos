import asyncio
import logging
from clients.backend_api import backend_client

logger = logging.getLogger(__name__)


async def cleanup_expired_events():
    """
    Job que elimina eventos cuyo start_date ya excede el umbral de expiracion.
    """
    logger.info("Ejecutando job: cleanup_expired_events")
    try:
        token_ok = await backend_client.ensure_superadmin_token()
        if not token_ok:
            logger.warning("No se pudo obtener token superadmin; se omite limpieza")
            return

        expired_events = await backend_client.get_expired_events()

        if not expired_events:
            logger.info("No hay eventos expirados")
            return

        logger.info(f"Se encontraron {len(expired_events)} evento(s) expirado(s)")
        for event in expired_events:
            event_id = event.get("id")
            start_date = event.get("start_date")
            logger.info(
                f"Intentando eliminar evento {event_id} (fecha inicio: {start_date})"
            )
            success = await backend_client.delete_event(event_id)
            if success:
                logger.info(f"Evento {event_id} eliminado correctamente")
            else:
                logger.warning(f"No se pudo eliminar el evento {event_id}")
    except Exception as e:
        logger.error(f"Error en job cleanup_expired_events: {e}", exc_info=True)


def cleanup_expired_events_sync():
    """
    Wrapper sincrono para ejecutar el job desde APScheduler.
    """
    asyncio.run(cleanup_expired_events())
