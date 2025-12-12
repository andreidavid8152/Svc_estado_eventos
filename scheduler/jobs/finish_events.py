import asyncio
import logging
from clients.backend_api import backend_client

logger = logging.getLogger(__name__)


async def finish_pending_events():
    """
    Job que se ejecuta periódicamente para finalizar eventos en progreso
    cuyo end_date ya llegó.
    """
    logger.info("Ejecutando job: finish_pending_events")

    try:
        # Obtener eventos pendientes de finalización
        pending_events = await backend_client.get_pending_finish_events()

        if not pending_events:
            logger.info("No hay eventos pendientes de finalización")
            return

        logger.info(
            f"Se encontraron {len(pending_events)} evento(s) pendiente(s) de finalización"
        )

        # Finalizar cada evento
        for event in pending_events:
            event_id = event.get("id")
            end_date = event.get("end_date")

            logger.info(
                f"Intentando finalizar evento {event_id} (fecha fin: {end_date})"
            )

            success = await backend_client.finish_event(event_id)

            if success:
                logger.info(f"✓ Evento {event_id} finalizado exitosamente")
                
                # Iniciar procesamiento de finalización (unión de videos y análisis)
                logger.info(f"Iniciando procesamiento de finalización para evento {event_id}")
                processing_success = await backend_client.process_event_completion(event_id)
                
                if processing_success:
                    logger.info(f"✓ Procesamiento de finalización iniciado para evento {event_id}")
                else:
                    logger.warning(f"✗ No se pudo iniciar el procesamiento de finalización para evento {event_id}")
                    
            else:
                logger.warning(f"✗ No se pudo finalizar el evento {event_id}")

        logger.info("Job finish_pending_events completado")

    except Exception as e:
        logger.error(f"Error en job finish_pending_events: {e}", exc_info=True)


def finish_pending_events_sync():
    """
    Wrapper síncrono para el job asíncrono.
    APScheduler ejecutará esta función.
    """
    asyncio.run(finish_pending_events())
