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
        self.superadmin_email = settings.BACKEND_SUPERADMIN_EMAIL
        self.superadmin_password = settings.BACKEND_SUPERADMIN_PASSWORD
        self._token = settings.BACKEND_SUPERADMIN_TOKEN

    def _get_headers(self) -> Dict[str, str]:
        """Construye los headers para las peticiones."""
        headers = {
            "Content-Type": "application/json",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    async def login_superadmin(self) -> bool:
        """Inicia sesion con superadmin para obtener un token fresco."""
        if not self.superadmin_email or not self.superadmin_password:
            logger.error("Credenciales superadmin no configuradas")
            return False

        try:
            url = f"{self.base_url}/auth/login/"
            payload = {
                "email": self.superadmin_email,
                "password": self.superadmin_password,
            }
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url, json=payload, headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                data = response.json()
                token = data.get("token")
                if token:
                    self._token = token
                    return True
                logger.error("Login superadmin no retorno token")
                return False
        except httpx.HTTPError as e:
            logger.error(f"Error al iniciar sesion superadmin: {e}")
            return False
        except Exception as e:
            logger.error(f"Error inesperado al iniciar sesion superadmin: {e}")
            return False

    async def refresh_superadmin_token(self) -> bool:
        """Renueva el token superadmin usando refresh-token o login."""
        if not self._token:
            return await self.login_superadmin()

        try:
            url = f"{self.base_url}/auth/refresh-token/"
            payload = {"token": self._token}
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url, json=payload, headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                data = response.json()
                token = data.get("token")
                if token:
                    self._token = token
                    return True
                logger.warning("Refresh token no retorno token, intentando login")
        except httpx.HTTPError as e:
            logger.warning(f"Error al renovar token superadmin: {e}")
        except Exception as e:
            logger.warning(f"Error inesperado al renovar token superadmin: {e}")

        return await self.login_superadmin()

    async def ensure_superadmin_token(self) -> bool:
        """Garantiza un token valido para endpoints protegidos."""
        return await self.refresh_superadmin_token()

    async def get_pending_start_events(self) -> List[Dict[str, Any]]:
        """
        Obtiene los eventos pendientes de iniciar.

        Returns:
            Lista de eventos en estado 'programado' cuyo start_date ya pasó.
        """
        try:
            url = f"{self.base_url}/events/api/events-status/pending-start/"
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=self._get_headers())
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
                response = await client.get(url, headers=self._get_headers())
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

    async def get_expired_events(self) -> List[Dict[str, Any]]:
        """
        Obtiene los eventos cuyo start_date ya excede el umbral de expiracion.

        Returns:
            Lista de eventos expirados con su ID.
        """
        try:
            url = f"{self.base_url}/events/api/events-status/expired/"
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=self._get_headers())
                response.raise_for_status()
                data = response.json()
                return data.get("results", [])
        except httpx.HTTPError as e:
            logger.error(f"Error al obtener eventos expirados: {e}")
            return []
        except Exception as e:
            logger.error(f"Error inesperado al obtener eventos expirados: {e}")
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
                response = await client.post(url, headers=self._get_headers())
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
                response = await client.post(url, headers=self._get_headers())
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
                response = await client.post(url, json=payload, headers=self._get_headers())
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


    async def delete_event(self, event_id: int) -> bool:
        """
        Elimina un evento en el backend.

        Args:
            event_id: ID del evento a eliminar

        Returns:
            True si se elimin¢ correctamente, False en caso contrario.
        """
        try:
            url = f"{self.base_url}/events/api/events/{event_id}"
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.delete(url, headers=self._get_headers())
                response.raise_for_status()
                try:
                    data = response.json()
                except ValueError:
                    data = {}
                return bool(data.get("success", True))
        except httpx.HTTPError as e:
            logger.error(f"Error al eliminar evento {event_id}: {e}")
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_data = e.response.json()
                    logger.error(
                        f"Detalle del error: {error_data.get('error', 'Sin detalles')}"
                    )
                except Exception:
                    pass
            return False
        except Exception as e:
            logger.error(f"Error inesperado al eliminar evento {event_id}: {e}")
            return False


# Singleton del cliente
backend_client = BackendAPIClient()
