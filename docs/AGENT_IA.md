# AI Agent para Gestión de Conversaciones con Socios

Sistema de agente IA para gestionar conversaciones con socios a través de Telegram, utilizando procesamiento de lenguaje natural y modelos de Google Gemini.

## Características

### Autenticación
- Autenticación de socios mediante número de documento y año de nacimiento
- Validación contra la base de datos de socios
- Gestión de sesiones de conversación

### Funcionalidades Disponibles

1. **Consultas de Información**
   - Obtener detalles del socio
   - Consultar estado de cuenta
   - Listar préstamos activos
   - Ver detalle de un préstamo específico

2. **Soporte**
   - Crear tickets de soporte
   - Cargar comprobantes de pago

3. **Procesamiento Inteligente**
   - Detección de intenciones con NLP (spaCy)
   - Respuestas automáticas para consultas comunes
   - Integración con Google Gemini para consultas complejas
   - Soporte para CrewAI (opcional)

## Instalación

### 1. Instalar dependencias

```bash
source venv/bin/activate
pip install -r requirements/base.txt
```

### 2. Descargar modelo de spaCy (opcional)

Para mejorar el procesamiento de lenguaje natural:

```bash
python -m spacy download es_core_news_sm
```

### 3. Configurar variables de entorno

Agrega las siguientes variables a tu archivo `.env`:

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Google Gemini AI
GOOGLE_GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL_NAME=gemini-pro

# AI Agent Settings
USE_CREW_AI=False
AI_AGENT_API_TOKEN=your_api_token_here
AI_AGENT_API_BASE_URL=http://localhost:8000
```

### 4. Ejecutar migraciones

```bash
python manage.py migrate
```

### 5. Crear un superusuario (si es necesario)

```bash
python manage.py createsuperuser
```

## Uso

### Iniciar el bot de Telegram

#### Modo Polling (desarrollo)

```bash
python manage.py run_telegram_bot --polling
```

#### Modo Webhook (producción)

```bash
python manage.py run_telegram_bot --webhook-url https://tu-dominio.com/webhook/telegram
```

### Comandos disponibles en Telegram

- `/start` - Iniciar conversación y autenticarse
- `/help` - Ver ayuda y comandos disponibles
- `/menu` - Ver menú de opciones
- `/micuenta` - Ver información personal
- `/prestamos` - Ver listado de préstamos
- `/saldo` - Ver estado de cuenta

### Ejemplos de uso

#### Autenticación

```
Usuario: /start
Bot: Bienvenido! Por favor envía tu documento y año de nacimiento.
     Ejemplo: 12345678 1990

Usuario: 12345678 1990
Bot: ✅ Bienvenido Juan Pérez!
```

#### Consultas en lenguaje natural

```
Usuario: Cuál es mi estado de cuenta?
Bot: [Muestra estado de cuenta con saldo, préstamos activos, etc.]

Usuario: Detalle del préstamo 123
Bot: [Muestra información detallada del préstamo 123]

Usuario: Necesito ayuda con un pago
Bot: Voy a ayudarte a crear un ticket de soporte.
     Por favor, describe brevemente el asunto:
```

## Arquitectura

### Estructura de Directorios

```
apps/ai_agent/
├── __init__.py
├── admin.py              # Configuración del admin de Django
├── apps.py               # Configuración de la aplicación
├── choices.py            # Choices para modelos (estados, tipos, etc.)
├── handlers.py           # Handlers de Telegram
├── models.py             # Modelos de datos (Conversations, Messages)
├── management/
│   └── commands/
│       └── run_telegram_bot.py  # Comando para ejecutar el bot
├── services/
│   ├── __init__.py
│   ├── authentication_service.py    # Autenticación de socios
│   ├── conversation_service.py      # Gestión de conversaciones
│   ├── partner_api_service.py       # Cliente API REST
│   └── ai_agent_service.py          # Integración Gemini/CrewAI
├── utils/
│   ├── __init__.py
│   ├── intent_detector.py           # Detección de intenciones
│   └── message_formatter.py         # Formato de mensajes
└── README.md
```

### Flujo de Procesamiento

1. **Usuario envía mensaje** → Telegram
2. **Handler recibe mensaje** → `handlers.py`
3. **ConversationService procesa** → `conversation_service.py`
   - Si no está autenticado → Flujo de autenticación
   - Si está autenticado → Detecta intención
4. **IntentDetector clasifica** → `intent_detector.py`
   - Usa reglas + spaCy para intenciones comunes
   - Fallback a Gemini para consultas complejas
5. **Ejecuta acción apropiada**
   - Consulta API REST (`partner_api_service.py`)
   - Genera respuesta formateada
6. **Envía respuesta** → Telegram

### Modelos de Datos

#### AgentConversation
- Gestiona sesión de conversación
- Almacena partner asociado
- Mantiene estado de autenticación
- Guarda contexto (para flujos multi-paso)

#### ConversationMessage
- Registra cada mensaje intercambiado
- Almacena intent detectado
- Guarda metadata adicional

## Configuración Avanzada

### Usar CrewAI para consultas complejas

1. Instalar CrewAI:
```bash
pip install crewai
```

2. Habilitar en `.env`:
```env
USE_CREW_AI=True
```

3. CrewAI creará agentes especializados:
   - **Partner Support Specialist**: Atiende consultas de socios
   - **Financial Data Analyst**: Analiza datos financieros

### Ajustar modelo de Gemini

Puedes usar diferentes modelos de Gemini según tus necesidades:

```env
# Modelo más ligero (más rápido, menor costo)
GEMINI_MODEL_NAME=gemini-pro

# Modelo con visión (para procesar imágenes)
GEMINI_MODEL_NAME=gemini-pro-vision
```

### Personalizar detección de intenciones

Edita `apps/ai_agent/utils/intent_detector.py` para agregar más keywords:

```python
INTENT_KEYWORDS = {
    IntentType.ACCOUNT_STATEMENT: [
        "estado de cuenta",
        "mi cuenta",
        "saldo",
        "balance",
        "cuanto debo",
        # Agrega más keywords aquí
    ],
}
```

## API REST

El agente utiliza los siguientes endpoints:

- `GET /api/v1/partners/partners/{id}/` - Detalle del socio
- `GET /api/v1/partners/partners/{id}/account-statement/` - Estado de cuenta
- `GET /api/v1/partners/partners/{id}/credits/` - Lista de créditos
- `GET /api/v1/partners/partners/{id}/credits/{credit_id}/` - Detalle de crédito
- `POST /api/v1/support/tickets/` - Crear ticket de soporte

### Autenticación API

El agente usa Bearer Token authentication:

```python
headers = {"Authorization": f"Bearer {AI_AGENT_API_TOKEN}"}
```

## Administración

Accede al admin de Django para:

- Ver conversaciones activas
- Revisar historial de mensajes
- Analizar intenciones detectadas
- Monitorear autenticaciones

URL: `http://localhost:8000/admin/ai_agent/`

## Monitoreo y Logs

Los logs se generan con el logger `apps.ai_agent`:

```python
import logging
logger = logging.getLogger(__name__)
```

Eventos registrados:
- Autenticaciones exitosas/fallidas
- Mensajes procesados
- Errores de API
- Respuestas de IA generadas

## Troubleshooting

### El bot no responde

1. Verifica que `TELEGRAM_BOT_TOKEN` esté configurado
2. Revisa los logs: `python manage.py run_telegram_bot --polling`
3. Verifica conectividad con Telegram API

### Errores de autenticación

1. Verifica que el socio exista en la base de datos
2. Confirma que el año de nacimiento sea correcto
3. Revisa logs de autenticación

### API no responde

1. Verifica `AI_AGENT_API_BASE_URL`
2. Confirma que `AI_AGENT_API_TOKEN` sea válido
3. Revisa que los endpoints estén disponibles

### Gemini no funciona

1. Verifica `GOOGLE_GEMINI_API_KEY`
2. Confirma cuota de API disponible
3. Revisa que el modelo esté activo

## Desarrollo

### Tests

```bash
python manage.py test apps.ai_agent
```

### Agregar nueva intención

1. Agregar choice en `choices.py`
2. Agregar keywords en `utils/intent_detector.py`
3. Crear handler en `services/conversation_service.py`
4. Agregar formato de respuesta en `utils/message_formatter.py`

### Extender funcionalidad

Para agregar nuevas capacidades:

1. Crear nuevo servicio en `services/`
2. Integrar en `conversation_service.py`
3. Actualizar handlers si es necesario

## Seguridad

- Las credenciales nunca se almacenan en logs
- La autenticación requiere documento + año de nacimiento
- Las sesiones se gestionan por chat_id de Telegram
- Los datos sensibles se cifran en tránsito (HTTPS)

## Licencia

Copyright © 2025 XoFi ERP
