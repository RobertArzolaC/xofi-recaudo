# Chatbot Module

Sistema de chatbot multicanal para gestionar conversaciones con socios a través de diferentes plataformas de mensajería.

## Estructura Modular

```
apps/chatbot/
├── channels/          # Integraciones con canales de comunicación
│   └── telegram/     # Canal de Telegram
├── conversation/     # Lógica de conversaciones
│   ├── service.py
│   ├── intent_detector.py
│   └── message_formatter.py
├── services/         # Servicios auxiliares
└── management/       # Comandos de Django
```

## Componentes Principales

### Channels (Canales)

Cada canal de comunicación tiene su propia carpeta con handlers específicos:

- **`channels/telegram/`**: Integración con Telegram Bot API
  - `handlers.py`: Manejo de comandos y mensajes de Telegram
  
Para agregar un nuevo canal (ej: WhatsApp), crea una nueva carpeta `channels/whatsapp/` con su propia implementación.

### Conversation (Conversaciones)

Lógica de conversaciones compartida entre todos los canales:

- **`conversation/service.py`**: Gestión de conversaciones independiente del canal (ConversationService)
- **`conversation/intent_detector.py`**: Detección de intenciones con NLP y reglas
- **`conversation/message_formatter.py`**: Formateo de mensajes para respuestas

### Services (Servicios)

Servicios auxiliares utilizados por el chatbot:

- **`gemini.py`**: Integración con Google Gemini AI para análisis de intenciones y respuestas complejas
- **`authentication.py`**: Autenticación de socios mediante DNI y año de nacimiento
- **`partner_api.py`**: Cliente para comunicación con API REST de gestión de socios
- **`receipt_extraction.py`**: Extracción inteligente de datos de recibos de pago

## Uso

### Ejecutar bot de Telegram

```bash
# Modo polling (desarrollo)
python manage.py run_telegram_bot --polling

# Modo webhook (producción)
python manage.py run_telegram_bot --webhook-url https://tu-dominio.com/webhook
```

### Agregar nuevo canal

1. Crear carpeta `channels/nuevo_canal/`
2. Implementar `handlers.py` con lógica específica
3. Importar y usar `conversation.ConversationService`
4. Crear comando de management si es necesario

## Arquitectura

La separación en módulos permite:

- ✅ Agregar nuevos canales sin modificar la lógica central
- ✅ Reutilizar servicios entre diferentes canales
- ✅ Mantener código limpio y organizado
- ✅ Escalar fácilmente a múltiples plataformas

## Flujo de Datos

```
Usuario → Canal (Telegram/WhatsApp) → Handler → ConversationService → Servicios → Respuesta
```

Cada canal tiene su handler específico, pero todos usan el mismo `ConversationService` para la lógica de negocio.
