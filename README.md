# Servicio de Estado de Eventos

Microservicio FastAPI que actualiza automáticamente los estados de los eventos mediante APScheduler.

## Características

- **Actualización automática de eventos**: El servicio consulta periódicamente el backend Django para:

  - Iniciar eventos programados cuando llega su `start_date`
  - Finalizar eventos en progreso cuando llega su `end_date`

- **Ejecución programada**: Utiliza APScheduler para ejecutar tareas cada minuto (configurable)

- **API REST**: Expone endpoints para monitoreo y health checks

## Requisitos

- Python 3.8+
- Backend Django ejecutándose
- Token JWT válido de un usuario admin/superadmin

## Instalación

1. Instalar dependencias:

```bash
pip install -r requirements.txt
```

2. Configurar variables de entorno:

Copiar `.env.example` a `.env` y configurar:

```bash
copy .env.example .env
```

Editar `.env` con tus valores:

```env
BACKEND_URL=http://localhost:8000
BACKEND_JWT_TOKEN=your_jwt_token_here
SCHEDULER_INTERVAL_SECONDS=60
```

### Obtener el JWT Token

Para obtener un token JWT válido:

1. Iniciar sesión en el backend Django con un usuario admin/superadmin
2. El token se devuelve en la respuesta del login
3. Copiar el token y configurarlo en `BACKEND_JWT_TOKEN`

## Ejecución

### Modo desarrollo

```bash
python main.py
```

### Modo producción con Uvicorn

```bash
uvicorn main:app --host 0.0.0.0 --port 8001
```

## Endpoints

### Health Check

```
GET /health
```

Respuesta:

```json
{
  "status": "ok"
}
```

### Información del servicio

```
GET /
```

Respuesta:

```json
{
  "service": "Estado de Eventos",
  "version": "1.0.0",
  "status": "running",
  "scheduler_interval_seconds": 60
}
```

## Arquitectura

### Componentes

1. **main.py**: Aplicación FastAPI principal con lifecycle management
2. **settings.py**: Configuración centralizada usando Pydantic Settings
3. **clients/backend_api.py**: Cliente HTTP para consumir el backend Django
4. **scheduler/bootstrap.py**: Inicialización y configuración de APScheduler
5. **scheduler/jobs/start_events.py**: Job para iniciar eventos programados
6. **scheduler/jobs/finish_events.py**: Job para finalizar eventos en progreso

### Flujo de trabajo

```
┌─────────────────────┐
│   FastAPI Server    │
│     (main.py)       │
└──────────┬──────────┘
           │
           │ Inicia
           ▼
┌─────────────────────┐
│   APScheduler       │
│  (bootstrap.py)     │
└──────────┬──────────┘
           │
           │ Ejecuta cada minuto
           │
     ┌─────┴─────┐
     │           │
     ▼           ▼
┌─────────┐ ┌──────────┐
│ Start   │ │ Finish   │
│ Events  │ │ Events   │
│  Job    │ │   Job    │
└────┬────┘ └────┬─────┘
     │           │
     │ Consume   │ Consume
     │ API       │ API
     ▼           ▼
┌─────────────────────┐
│   Backend Django    │
│   (eventos API)     │
└─────────────────────┘
```

### Jobs programados

#### Start Events Job

- **Frecuencia**: Cada minuto (configurable)
- **Acción**:
  1. Consulta `GET /api/events-status/pending-start/`
  2. Para cada evento retornado, llama a `POST /api/events-status/{event_id}/start/`
  3. Cambia el estado de `programado` → `en_progreso`

#### Finish Events Job

- **Frecuencia**: Cada minuto (configurable)
- **Acción**:
  1. Consulta `GET /api/events-status/pending-finish/`
  2. Para cada evento retornado, llama a `POST /api/events-status/{event_id}/finish/`
  3. Cambia el estado de `en_progreso` → `completado`

## Configuración

### Variables de entorno

| Variable                     | Descripción                       | Valor por defecto       |
| ---------------------------- | --------------------------------- | ----------------------- |
| `BACKEND_URL`                | URL del backend Django            | `http://localhost:8000` |
| `BACKEND_JWT_TOKEN`          | Token JWT para autenticación      | -                       |
| `SCHEDULER_INTERVAL_SECONDS` | Intervalo de ejecución (segundos) | `60`                    |
| `HOST`                       | Host del servidor FastAPI         | `0.0.0.0`               |
| `PORT`                       | Puerto del servidor FastAPI       | `8001`                  |
| `HTTP_TIMEOUT`               | Timeout para requests HTTP        | `30`                    |
| `LOG_LEVEL`                  | Nivel de logging                  | `INFO`                  |

## Logging

El servicio registra información detallada sobre:

- Inicio y detención del scheduler
- Ejecución de cada job
- Eventos procesados (iniciados/finalizados)
- Errores y excepciones

Ejemplo de logs:

```
2025-11-11 10:00:00 - INFO - Ejecutando job: start_pending_events
2025-11-11 10:00:00 - INFO - Se encontraron 2 evento(s) pendiente(s) de inicio
2025-11-11 10:00:01 - INFO - Intentando iniciar evento 123 (fecha inicio: 2025-11-11T10:00:00)
2025-11-11 10:00:01 - INFO - ✓ Evento 123 iniciado exitosamente
```

## Desarrollo

### Estructura del proyecto

```
svc-estado-eventos/
├── main.py                 # Aplicación FastAPI
├── settings.py             # Configuración
├── requirements.txt        # Dependencias
├── .env                    # Variables de entorno
├── .env.example           # Ejemplo de variables
├── README.md              # Documentación
├── clients/
│   ├── __init__.py
│   └── backend_api.py     # Cliente HTTP
├── routers/
│   ├── __init__.py
│   └── health.py          # Health check endpoint
└── scheduler/
    ├── __init__.py
    ├── bootstrap.py       # Configuración del scheduler
    └── jobs/
        ├── __init__.py
        ├── start_events.py    # Job inicio eventos
        └── finish_events.py   # Job fin eventos
```

## Troubleshooting

### El scheduler no ejecuta los jobs

Verificar:

- Que el servicio esté corriendo (`GET /`)
- Los logs del servidor para ver errores
- La configuración de `SCHEDULER_INTERVAL_SECONDS`

### Error de autenticación con el backend

Verificar:

- Que `BACKEND_JWT_TOKEN` esté configurado
- Que el token sea válido y no haya expirado
- Que el usuario tenga permisos admin/superadmin

### No se actualizan los eventos

Verificar:

- Que el backend Django esté corriendo en `BACKEND_URL`
- Los endpoints `/api/events-status/` estén disponibles
- Los eventos tengan las fechas correctas
- Los logs del servicio para ver errores específicos

## Producción

### Consideraciones

1. **No usar reload**: APScheduler no es compatible con el auto-reload de Uvicorn
2. **Manejo de errores**: Los jobs capturan excepciones y continúan ejecutándose
3. **Tokens JWT**: Renovar el token antes de que expire
4. **Monitoreo**: Usar los logs para monitorear la ejecución

### Docker (opcional)

Si se desea containerizar el servicio, crear un `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
```

## Licencia

Este servicio es parte del proyecto EvalTech Administrador.
