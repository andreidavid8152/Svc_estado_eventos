import asyncio
import logging
from clients.backend_api import backend_client

logger = logging.getLogger(__name__)


async def process_events():
    """
    Job principal que ejecuta las tareas de eventos de forma secuencial.
    1. Primero inicia eventos programados
    2. Luego finaliza eventos en progreso
    """
    logger.info("=" * 80)
    logger.info("INICIANDO PROCESAMIENTO DE EVENTOS")
    logger.info("=" * 80)

    # =============================
    # PASO 1: Iniciar eventos programados
    # =============================
    logger.info("")
    logger.info("PASO 1/2: Verificando eventos pendientes de inicio...")
    logger.info("-" * 80)

    try:
        # Obtener eventos pendientes de inicio
        pending_start = await backend_client.get_pending_start_events()

        if not pending_start:
            logger.info("  No hay eventos pendientes de inicio")
        else:
            logger.info(
                f"   ✓ Se encontraron {len(pending_start)} evento(s) para iniciar"
            )

            # Iniciar cada evento
            for idx, event in enumerate(pending_start, 1):
                event_id = event.get("id")
                start_date = event.get("start_date")

                logger.info(
                    f"   [{idx}/{len(pending_start)}] Iniciando evento ID={event_id}"
                )
                logger.info(f"       - Fecha programada: {start_date}")

                success = await backend_client.start_event(event_id)

                if success:
                    logger.info(f"       Evento {event_id} iniciado correctamente")
                else:
                    logger.warning(f"       No se pudo iniciar el evento {event_id}")

        logger.info("-" * 80)
        logger.info("✓ PASO 1/2 COMPLETADO")

    except Exception as e:
        logger.error(f"Error en paso 1 (iniciar eventos): {e}", exc_info=True)

    # =============================
    # PASO 2: Finalizar eventos en progreso
    # =============================
    logger.info("")
    logger.info("PASO 2/2: Verificando eventos pendientes de finalización...")
    logger.info("-" * 80)

    try:
        # Obtener eventos pendientes de finalización
        pending_finish = await backend_client.get_pending_finish_events()

        if not pending_finish:
            logger.info("   No hay eventos pendientes de finalización")
        else:
            logger.info(
                f"   Se encontraron {len(pending_finish)} evento(s) para finalizar"
            )

            # Finalizar cada evento
            for idx, event in enumerate(pending_finish, 1):
                event_id = event.get("id")
                end_date = event.get("end_date")

                logger.info(
                    f"   [{idx}/{len(pending_finish)}] Finalizando evento ID={event_id}"
                )
                logger.info(f"       - Fecha programada: {end_date}")

                success = await backend_client.finish_event(event_id)

                if success:
                    logger.info(f"       Evento {event_id} finalizado correctamente")
                    
                    # Iniciar procesamiento de finalización (unión de videos y análisis)
                    logger.info(f"       Iniciando procesamiento de finalización para evento {event_id}")
                    processing_success = await backend_client.process_event_completion(event_id)
                    
                    if processing_success:
                        logger.info(f"       ✓ Procesamiento de finalización iniciado para evento {event_id}")
                    else:
                        logger.warning(f"       ✗ No se pudo iniciar el procesamiento de finalización para evento {event_id}")
                        
                else:
                    logger.warning(f"       No se pudo finalizar el evento {event_id}")

        logger.info("-" * 80)
        logger.info("✓ PASO 2/2 COMPLETADO")

    except Exception as e:
        logger.error(f"Error en paso 2 (finalizar eventos): {e}", exc_info=True)

    # =============================
    # Resumen final
    # =============================
    logger.info("")
    logger.info("=" * 80)
    logger.info("PROCESAMIENTO DE EVENTOS COMPLETADO")
    logger.info("=" * 80)
    logger.info("")


def process_events_sync():
    """
    Wrapper síncrono para el job asíncrono.
    APScheduler ejecutará esta función.
    """
    asyncio.run(process_events())
