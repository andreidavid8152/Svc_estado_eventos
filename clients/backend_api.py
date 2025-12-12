import httpx
import logging
from typing import List, Dict, Any
from settings import settings

logger = logging.getLogger(__name__)


class BackendAPIClient:
    """Cliente para consumir los endpoints del backend Django."""

    def __init__(self):
        self.base_url = settings.BACKEND_URL
        self.timeout = settings.HTTP_TIMEOUT
        self.headers = self._get_headers()

    def _get_headers(self) -> Dict[str, str]:
        """Construye los headers para las peticiones."""
        headers = {
            "Content-Type": "application/json",
        }
        return headers

    async def get_pending_start_events(self) -> List[Dict[str, Any]]:
        """
        Obtiene los eventos pendientes de iniciar.

        Returns:
            Lista de eventos en estado 'programado' cuyo start_date ya pasó.
        """
        try:
            url = f"{self.base_url}/events/api/events-status/pending-start/"
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                return data.get("results", [])
        except httpx.HTTPError as e:
            logger.error(f"Error al obtener eventos pendientes de inicio: {e}")
            return []
        except Exception as e:
            logger.error(
                f"Error inesperado al obtener eventos pendientes de inicio: {e}"
            )
            return []

    async def get_pending_finish_events(self) -> List[Dict[str, Any]]:
        """
        Obtiene los eventos pendientes de finalizar.

        Returns:
            Lista de eventos en estado 'en_progreso' cuyo end_date ya pasó.
        """
        try:
            url = f"{self.base_url}/events/api/events-status/pending-finish/"
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                return data.get("results", [])
        except httpx.HTTPError as e:
            logger.error(f"Error al obtener eventos pendientes de finalización: {e}")
            return []
        except Exception as e:
            logger.error(
                f"Error inesperado al obtener eventos pendientes de finalización: {e}"
            )
            return []

    async def start_event(self, event_id: int) -> bool:
        """
        Inicia un evento (cambia estado de 'programado' a 'en_progreso').

        Args:
            event_id: ID del evento a iniciar

        Returns:
            True si se inició correctamente, False en caso contrario.
        """
        try:
            url = f"{self.base_url}/events/api/events-status/{event_id}/start/"
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                if data.get("success"):
                    logger.info(
                        f"Evento {event_id} iniciado correctamente. Nuevo estado: {data.get('status')}"
                    )
                    return True
                return False
        except httpx.HTTPError as e:
            logger.error(f"Error al iniciar evento {event_id}: {e}")
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_data = e.response.json()
                    logger.error(
                        f"Detalle del error: {error_data.get('error', 'Sin detalles')}"
                    )
                except:
                    pass
            return False
        except Exception as e:
            logger.error(f"Error inesperado al iniciar evento {event_id}: {e}")
            return False

    async def finish_event(self, event_id: int) -> bool:
        """
        Finaliza un evento (cambia estado de 'en_progreso' a 'completado').

        Args:
            event_id: ID del evento a finalizar

        Returns:
            True si se finalizó correctamente, False en caso contrario.
        """
        try:
            url = f"{self.base_url}/events/api/events-status/{event_id}/finish/"
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                if data.get("success"):
                    logger.info(
                        f"Evento {event_id} finalizado correctamente. Nuevo estado: {data.get('status')}"
                    )
                    return True
                return False
        except httpx.HTTPError as e:
            logger.error(f"Error al finalizar evento {event_id}: {e}")
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_data = e.response.json()
                    logger.error(
                        f"Detalle del error: {error_data.get('error', 'Sin detalles')}"
                    )
                except:
                    pass
            return False
        except Exception as e:
            logger.error(f"Error inesperado al finalizar evento {event_id}: {e}")
            return False

    async def process_event_completion(self, event_id: int) -> bool:
        """
        Procesa la finalización de un evento: une videos y ejecuta análisis de comportamiento.
        
        Args:
            event_id: ID del evento que ha finalizado
            
        Returns:
            True si el procesamiento se inició correctamente, False en caso contrario.
        """
        try:
            url = f"{self.base_url}/analysis/process-event-completion/"
            payload = {"event_id": event_id}
            
            async with httpx.AsyncClient(timeout=60) as client:  # Timeout más largo para este proceso
                response = await client.post(url, json=payload, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                
                if "message" in data:
                    logger.info(f"Procesamiento de finalización iniciado para evento {event_id}")
                    logger.info(f"Total participantes: {data.get('total_participants', 0)}")
                    logger.info(f"Exitosos: {data.get('successful', 0)}, Fallidos: {data.get('failed', 0)}")
                    
                    # Log detalles de participantes que fallaron
                    if data.get('failed', 0) > 0:
                        for result in data.get('results', []):
                            if not result.get('success'):
                                logger.warning(f"Falló procesamiento para participante {result.get('participant_name')}: {result.get('error')}")
                    
                    return True
                    
                return False
                
        except httpx.HTTPError as e:
            logger.error(f"Error HTTP al procesar finalización del evento {event_id}: {e}")
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_data = e.response.json()
                    logger.error(f"Detalle del error: {error_data.get('error', 'Sin detalles')}")
                except:
                    pass
            return False
        except Exception as e:
            logger.error(f"Error inesperado al procesar finalización del evento {event_id}: {e}")
            return False


# Singleton del cliente
backend_client = BackendAPIClient()
