# WhatsApp Chatbot Integration

Este documento describe la integración del chatbot de WhatsApp para el sistema Xofi Recaudo, proporcionando la misma funcionalidad que el chatbot de Telegram.

## Tabla de Contenidos

1. [Visión General](#visión-general)
2. [Arquitectura](#arquitectura)
3. [Configuración](#configuración)
4. [Componentes](#componentes)
5. [Funcionalidades](#funcionalidades)
6. [Flujo de Mensajes](#flujo-de-mensajes)
7. [Webhook](#webhook)
8. [Despliegue](#despliegue)
9. [Pruebas](#pruebas)
10. [Troubleshooting](#troubleshooting)

---

## Visión General

El chatbot de WhatsApp proporciona una interfaz conversacional para que los socios puedan:

- Autenticarse de forma segura
- Consultar su información personal
- Ver su estado de cuenta
- Listar sus préstamos
- Obtener detalles de préstamos específicos
- Crear tickets de soporte
- Subir comprobantes de pago
- Recibir ayuda y asistencia

La implementación reutiliza toda la lógica de negocio del chatbot de Telegram, adaptando únicamente la capa de comunicación para WhatsApp.

---

## Arquitectura

### Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────┐
│                    WhatsApp Business API                     │
│                   (Meta Cloud API / WHAPI)                   │
└───────────────────────────┬─────────────────────────────────┘
                            │ Webhooks
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              WhatsAppWebhookView (Django View)               │
│                    apps/chatbot/views.py                     │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│               WhatsAppBotHandler (Handler)                   │
│         apps/chatbot/channels/whatsapp/handlers.py           │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│          ConversationService (Lógica de Negocio)             │
│           apps/chatbot/conversation/service.py               │
└────┬────────────────────┬────────────────────┬──────────────┘
     │                    │                    │
     ▼                    ▼                    ▼
┌─────────────┐  ┌──────────────────┐  ┌─────────────────┐
│   Intent    │  │  Authentication  │  │   Partner API   │
│  Detector   │  │     Service      │  │    Service      │
└─────────────┘  └──────────────────┘  └─────────────────┘
```

### Capas de la Arquitectura

1. **Capa de Comunicación**: WhatsApp Business API / WHAPI
2. **Capa de Webhook**: Recepción y validación de mensajes entrantes
3. **Capa de Handlers**: Procesamiento específico de WhatsApp
4. **Capa de Lógica de Negocio**: Servicios compartidos (reutilizados de Telegram)
5. **Capa de Datos**: Modelos y base de datos

---

## Configuración

### Variables de Entorno

Agrega las siguientes variables al archivo `.env`:

```bash
# WhatsApp API Configuration (usando WHAPI como proveedor)
WHATSAPP_API_TOKEN=your_whapi_token_here
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id_here

# WHAPI Base URL (opcional, por defecto usa https://gate.whapi.cloud)
WHAPI_BASE_URL=https://gate.whapi.cloud

# Base URL para webhooks (debe ser accesible públicamente)
BASE_URL=https://your-domain.com
```

### Obtener Credenciales con WHAPI (Recomendado)

La implementación está optimizada para usar **WHAPI** como proveedor, que simplifica significativamente la integración:

1. **Crea una cuenta en WHAPI**:
   - Ve a [WHAPI.cloud](https://whapi.cloud/)
   - Registra una cuenta

2. **Crea un canal**:
   - Escanea el código QR con WhatsApp
   - Esto vincula tu número de WhatsApp con WHAPI

3. **Obtén las credenciales**:
   - En el panel de WHAPI, ve a tu canal
   - Copia el **API Token** → `WHATSAPP_API_TOKEN`
   - Copia el **Phone Number ID** → `WHATSAPP_PHONE_NUMBER_ID`

4. **Configura el webhook**:
   - En WHAPI, ve a Settings → Webhooks
   - Agrega la URL: `https://tu-dominio.com/chatbot/webhook/whatsapp/`
   - Selecciona el evento "messages"
   - Guarda la configuración

**Ventajas de WHAPI**:
- ✅ No requiere Meta Business Manager
- ✅ No requiere verificación de negocio
- ✅ Configuración en minutos
- ✅ Webhooks simplificados
- ✅ Sin necesidad de templates aprobados para mensajes básicos

### Verificar Configuración

Ejecuta el siguiente comando para verificar que todo está configurado correctamente:

```bash
python manage.py verify_whatsapp_config
```

Este comando verificará:
- Si las credenciales están configuradas
- Si el servicio de WhatsApp se puede inicializar
- La URL del webhook
- Instrucciones para configurar el webhook en Meta

---

## Componentes

### 1. Modelo de Base de Datos

**Archivo**: [`apps/chatbot/models.py`](../apps/chatbot/models.py)

#### AgentConversation

El modelo se actualizó para soportar múltiples canales:

```python
class AgentConversation(BaseUserTracked, TimeStampedModel):
    partner = models.ForeignKey("partners.Partner", ...)
    channel = models.CharField(
        max_length=20,
        choices=ChannelType.choices,
        default=ChannelType.TELEGRAM
    )
    telegram_chat_id = models.CharField(max_length=100, null=True, blank=True)
    telegram_username = models.CharField(max_length=100, blank=True)
    whatsapp_phone = models.CharField(max_length=20, null=True, blank=True)
    status = models.IntegerField(...)
    authenticated = models.BooleanField(default=False)
    context_data = models.JSONField(default=dict)
```

**Constraints**:
- Cada canal debe tener su identificador correspondiente
- Los identificadores son únicos por canal

### 2. WhatsApp Bot Handler

**Archivo**: [`apps/chatbot/channels/whatsapp/handlers.py`](../apps/chatbot/channels/whatsapp/handlers.py)

Responsabilidades:
- Procesar webhooks entrantes de WhatsApp
- Manejar diferentes tipos de mensajes (texto, imágenes, interactivos)
- Descargar archivos multimedia
- Enviar respuestas a través del servicio de WhatsApp

**Métodos principales**:

- `handle_webhook(webhook_data)`: Punto de entrada para webhooks
- `_handle_text_message(message)`: Procesa mensajes de texto
- `_handle_image_message(message)`: Procesa imágenes (comprobantes)
- `_send_text_message(phone, message)`: Envía mensajes de texto

### 3. Webhook View

**Archivo**: [`apps/chatbot/views.py`](../apps/chatbot/views.py)

```python
class WhatsAppWebhookView(View):
    def get(self, request):
        # Verifica el webhook con Meta

    def post(self, request):
        # Procesa mensajes entrantes
```

**Endpoints**:
- `GET /chatbot/webhook/whatsapp/`: Verificación del webhook
- `POST /chatbot/webhook/whatsapp/`: Recepción de mensajes

### 4. Conversation Service (Extendido)

**Archivo**: [`apps/chatbot/conversation/service.py`](../apps/chatbot/conversation/service.py)

Nuevos métodos para WhatsApp:

- `get_or_create_conversation_whatsapp(phone)`: Obtiene o crea conversación por teléfono
- `aget_or_create_conversation_whatsapp(phone)`: Versión async
- `aprocess_message_whatsapp(phone, message)`: Procesa mensajes de WhatsApp

### 5. WhatsApp Service

**Archivo**: [`apps/core/services/chats/whatsapp.py`](../apps/core/services/chats/whatsapp.py)

Servicio para comunicación con WhatsApp API usando la librería `heyoo`:

```python
class WhatsAppService:
    def send_text_message(phone, message)
    def send_template_message(phone, template_name, ...)
    def send_message_with_button(phone, message, button_text, button_url)
```

---

## Funcionalidades

El chatbot de WhatsApp proporciona exactamente las mismas funcionalidades que el de Telegram:

### 1. Autenticación

**Formato**: `DNI [número] año [año]`

**Ejemplo**: `DNI 12345678 año 1990`

El socio debe proporcionar:
- Número de DNI
- Año de nacimiento

### 2. Comandos Disponibles

Una vez autenticado, el socio puede:

| Comando/Mensaje | Descripción |
|----------------|-------------|
| "Hola" / "Buenos días" | Saludo y menú de opciones |
| "Ayuda" / "Help" | Muestra lista de comandos |
| "Mi información" / "Mis datos" | Muestra información personal |
| "Estado de cuenta" / "Mi deuda" | Muestra resumen de deudas |
| "Mis préstamos" / "Listar créditos" | Lista todos los préstamos |
| "Detalle de préstamo [ID]" | Detalle de un préstamo específico |
| "Crear ticket" / "Soporte" | Inicia creación de ticket |
| "Subir boleta" / "Comprobante" | Instrucciones para subir boleta |
| "Adiós" / "Chao" | Despedida |

### 3. Subida de Comprobantes

El socio puede enviar una imagen del comprobante de pago con el siguiente formato en el caption:

```
Monto: 500
Fecha: 2025-01-15
```

El sistema:
1. Descarga la imagen
2. Extrae monto y fecha del caption
3. Sube el comprobante a la API
4. Confirma la recepción

---

## Flujo de Mensajes

### Diagrama de Flujo

```
┌─────────────────┐
│ Usuario envía   │
│ mensaje por WA  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ WhatsApp Business API   │
│ envía webhook           │
└────────┬────────────────┘
         │
         ▼
┌──────────────────────────┐
│ WhatsAppWebhookView      │
│ recibe y valida          │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ WhatsAppBotHandler       │
│ procesa mensaje          │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ ConversationService      │
│ - Obtiene/crea conv.     │
│ - Verifica auth          │
│ - Detecta intent         │
│ - Ejecuta handler        │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ Genera respuesta         │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ WhatsAppService envía    │
│ respuesta al usuario     │
└──────────────────────────┘
```

### Flujo de Autenticación

```
1. Usuario: "DNI 12345678 año 1990"
2. Sistema: Extrae datos con regex
3. Sistema: Valida contra base de datos
4. Sistema: Marca conversación como autenticada
5. Sistema: Responde con saludo personalizado y menú
```

### Flujo Multi-Paso (Ejemplo: Crear Ticket)

```
1. Usuario: "crear ticket"
2. Sistema: Solicita asunto
   context_data = {"pending_action": "create_ticket", "step": "subject"}

3. Usuario: "Problema con pago"
4. Sistema: Guarda asunto, solicita descripción
   context_data = {"pending_action": "create_ticket",
                   "step": "description",
                   "ticket_subject": "Problema con pago"}

5. Usuario: "No puedo pagar mi cuota"
6. Sistema: Crea ticket via API, limpia contexto
   context_data = {}
7. Sistema: Confirma creación con número de ticket
```

---

## Webhook

### Configuración del Webhook en WHAPI

1. Ve a tu panel de WHAPI: [https://whapi.cloud/](https://whapi.cloud/)
2. Selecciona tu canal
3. Ve a **Settings > Webhooks**
4. Configura el webhook:
   - **Webhook URL**: `https://your-domain.com/chatbot/webhook/whatsapp/`
   - **Events**: Selecciona `messages`
5. Haz clic en **Save**

**Nota**: A diferencia de Meta, WHAPI no requiere un proceso de verificación con tokens. El webhook se activa inmediatamente.

### Verificación del Webhook

Para verificar que el webhook está funcionando:

1. **Health Check**:
   ```bash
   curl https://your-domain.com/chatbot/webhook/whatsapp/
   ```

   Deberías recibir:
   ```json
   {"status": "ok", "service": "whatsapp_chatbot"}
   ```

2. **Envía un mensaje de prueba**:
   - Envía "Hola" desde WhatsApp al número configurado
   - Verifica los logs del servidor
   - Deberías ver el webhook entrante en los logs

### Estructura de Webhook Entrante (WHAPI)

WHAPI usa una estructura simplificada en comparación con Meta:

```json
{
    "messages": [
        {
            "id": "rAmjVf1bsR7Vv32teVuI2A-hV0RKygAsKs",
            "from_me": false,
            "type": "text",
            "chat_id": "51902376744@s.whatsapp.net",
            "timestamp": 1762876458,
            "source": "mobile",
            "text": {
                "body": "Hola"
            },
            "from": "51902376744",
            "from_name": "Usuario"
        }
    ],
    "event": {
        "type": "messages",
        "event": "post"
    },
    "channel_id": "CHANNEL-ID"
}
```

**Campos importantes**:
- `messages`: Array de mensajes recibidos
- `from`: Número de teléfono del remitente (sin código de país en algunos casos)
- `from_me`: `false` para mensajes recibidos, `true` para mensajes enviados por el bot
- `type`: Tipo de mensaje (`text`, `image`, `video`, `document`, etc.)
- `text.body`: Contenido del mensaje de texto

**Nota**: El handler ignora automáticamente los mensajes donde `from_me` es `true` para evitar bucles.

---

## Despliegue

### Requisitos

1. **Servidor con acceso público**:
   - El webhook debe ser accesible desde internet
   - Debe tener certificado SSL válido (HTTPS requerido)

2. **Base de datos**:
   - PostgreSQL (recomendado)
   - Con migraciones aplicadas

3. **Dependencias**:
   ```bash
   pip install heyoo requests
   ```

### Pasos de Despliegue

1. **Aplicar migraciones**:
   ```bash
   python manage.py migrate chatbot
   ```

2. **Configurar variables de entorno** (ver sección Configuración)

3. **Verificar configuración**:
   ```bash
   python manage.py verify_whatsapp_config
   ```

4. **Configurar webhook en Meta** (ver sección Webhook)

5. **Reiniciar servidor**:
   ```bash
   # Si usas systemd
   sudo systemctl restart your-django-app

   # Si usas supervisor
   supervisorctl restart your-django-app
   ```

6. **Verificar logs**:
   ```bash
   tail -f /var/log/your-app/django.log
   ```

### Consideraciones de Producción

- **Rate Limiting**: WhatsApp tiene límites de mensajes por segundo
- **Logging**: Asegúrate de tener logs adecuados para debugging
- **Monitoring**: Implementa monitoreo de webhooks
- **Backup**: Respalda las conversaciones regularmente
- **Security**: Valida siempre el verify token en webhooks

---

## Pruebas

### Prueba Local con ngrok

Para probar el webhook localmente:

1. **Instala ngrok**:
   ```bash
   brew install ngrok  # macOS
   # o descarga de https://ngrok.com/
   ```

2. **Inicia el servidor Django**:
   ```bash
   python manage.py runserver 8000
   ```

3. **Inicia ngrok**:
   ```bash
   ngrok http 8000
   ```

4. **Configura el webhook** con la URL de ngrok:
   ```
   https://your-id.ngrok.io/chatbot/webhook/whatsapp/
   ```

### Casos de Prueba

| Caso | Input | Resultado Esperado |
|------|-------|-------------------|
| Autenticación exitosa | `DNI 12345678 año 1990` | Mensaje de bienvenida + menú |
| Autenticación fallida | `DNI 00000000 año 1900` | Mensaje de error |
| Consulta estado cuenta | `estado de cuenta` | Resumen de deudas |
| Subir comprobante | [Imagen] + caption | Confirmación de recibo |
| Crear ticket | `crear ticket` → `Asunto` → `Descripción` | Confirmación con número |

### Testing Automatizado

```python
# Ejemplo de test
from apps.chatbot.channels.whatsapp.handlers import WhatsAppBotHandler

class TestWhatsAppHandler(TestCase):
    def test_handle_text_message(self):
        handler = WhatsAppBotHandler()
        webhook_data = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": "51987654321",
                            "type": "text",
                            "text": {"body": "Hola"}
                        }]
                    }
                }]
            }]
        }

        result = await handler.handle_webhook(webhook_data)
        self.assertEqual(result["status"], "success")
```

---

## Troubleshooting

### Problema: Webhook no recibe mensajes

**Diagnóstico**:
1. Verifica que el webhook esté configurado correctamente en Meta
2. Verifica que la URL sea accesible desde internet
3. Revisa los logs del servidor

**Solución**:
```bash
# Verifica conectividad
curl https://your-domain.com/chatbot/webhook/whatsapp/

# Verifica logs
tail -f /var/log/django.log
```

### Problema: Error 403 en verificación de webhook

**Causa**: El verify token no coincide

**Solución**:
1. Verifica que `WHATSAPP_WEBHOOK_VERIFY_TOKEN` esté configurado
2. Asegúrate de que coincida con el token en Meta
3. Reinicia el servidor

### Problema: Mensajes no se envían

**Diagnóstico**:
1. Verifica las credenciales de la API
2. Verifica el saldo/límites de tu cuenta de WhatsApp
3. Revisa los logs de error

**Solución**:
```python
# Test manual
from apps.core.services.chats.whatsapp import WhatsAppService

service = WhatsAppService()
result = service.send_text_message("51987654321", "Test message")
print(result)
```

### Problema: Error al descargar imágenes

**Causa**: Token de API inválido o expirado

**Solución**:
1. Renueva el token de acceso en Meta
2. Actualiza `WHATSAPP_API_TOKEN` en el .env
3. Reinicia el servidor

### Logs Útiles

```python
# Habilita logging detallado
import logging
logging.basicConfig(level=logging.DEBUG)

# En settings.py
LOGGING = {
    'version': 1,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/var/log/chatbot-whatsapp.log',
        },
    },
    'loggers': {
        'apps.chatbot': {
            'handlers': ['file'],
            'level': 'DEBUG',
        },
    },
}
```

---

## Diferencias con Telegram

| Aspecto | Telegram | WhatsApp |
|---------|----------|----------|
| **Conexión** | Polling o Webhook | Solo Webhook |
| **Identificador** | chat_id (número) | Número de teléfono |
| **Formato de mensajes** | HTML/Markdown | Texto plano (limitado) |
| **Botones** | Inline/Reply keyboards | Templates aprobados |
| **Ejecución** | Comando Django (polling) | Webhook automático |
| **Multimedia** | Descarga directa | API de Meta |

---

## Referencias

- [Meta WhatsApp Business API](https://developers.facebook.com/docs/whatsapp)
- [WHAPI Documentation](https://whapi.cloud/docs)
- [heyoo Library](https://github.com/Neurotech-HQ/heyoo)
- [Telegram Integration Doc](./TELEGRAM_INTEGRATION.md)

---

## Próximos Pasos

- [ ] Implementar templates de WhatsApp para respuestas frecuentes
- [ ] Agregar soporte para botones interactivos
- [ ] Implementar rate limiting
- [ ] Agregar métricas y analytics
- [ ] Implementar tests automatizados completos
- [ ] Documentar flujos de error y recuperación

---

**Última actualización**: 2025-01-11
**Versión**: 1.0.0
