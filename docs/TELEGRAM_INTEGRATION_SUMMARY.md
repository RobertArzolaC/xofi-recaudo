# Resumen de Integración con Telegram

## Cambios Implementados

Se ha implementado exitosamente la integración con Telegram Bot API para el sistema de campañas de recaudación, siguiendo la misma arquitectura y lógica que la integración existente de WhatsApp.

---

## Archivos Creados

### 1. Servicio de Telegram
**Archivo**: `apps/core/services/chats/telegram.py`

Servicio similar a `WhatsAppService` que encapsula la lógica de comunicación con Telegram Bot API.

**Métodos principales**:
- `send_text_message(recipient_id, message)` - Enviar mensajes de texto
- `send_message_with_button(recipient_id, message, button_text, button_url)` - Enviar mensajes con botones
- `is_configured()` - Verificar configuración
- `verify_bot()` - Obtener información del bot

**Características**:
- Usa librería oficial `python-telegram-bot` v21.7
- Soporte para botones inline con URLs
- Formato HTML para mensajes
- Manejo de errores robusto
- Logging detallado

---

### 2. Documentación
**Archivo**: `docs/TELEGRAM_INTEGRATION.md`

Documentación completa de la integración incluyendo:
- Arquitectura y componentes
- Guía de configuración paso a paso
- Ejemplos de uso
- Comparación WhatsApp vs Telegram
- Solución de problemas
- Mejoras futuras

---

### 3. Ejemplos de Código
**Archivo**: `docs/TELEGRAM_EXAMPLES.py`

19 ejemplos prácticos de código para:
- Verificar configuración del bot
- Enviar mensajes simples y con botones
- Crear plantillas y campañas
- Procesar notificaciones
- Manejo de errores y reintentos
- Campañas multi-canal (WhatsApp + Telegram)

---

## Archivos Modificados

### 1. Dependencias
**Archivo**: `requirements/base.txt`

```diff
+ # Telegram Bot API
+ python-telegram-bot==21.7
```

---

### 2. Choices/Enumeraciones
**Archivo**: `apps/campaigns/choices.py`

```python
class NotificationChannel(models.TextChoices):
    EMAIL = "EMAIL", _("Email")
    SMS = "SMS", _("SMS")
    WHATSAPP = "WHATSAPP", _("WhatsApp")
+   TELEGRAM = "TELEGRAM", _("Telegram")  # ← NUEVO
    PHONE_CALL = "PHONE_CALL", _("Phone Call")
```

---

### 3. Tarea de Envío de Notificaciones
**Archivo**: `apps/campaigns/tasks.py`

**Cambios principales**:

1. **Importación del servicio**:
```python
from apps.core.services.chats.telegram import telegram_service
```

2. **Selección dinámica de servicio**:
```python
# Determinar qué servicio usar según el canal
if notification.channel == choices.NotificationChannel.TELEGRAM:
    messaging_service = telegram_service
    channel_name = "Telegram"
elif notification.channel == choices.NotificationChannel.WHATSAPP:
    messaging_service = whatsapp_service
    channel_name = "WhatsApp"
```

3. **Búsqueda de plantilla por canal**:
```python
template = models.MessageTemplate.objects.get(
    template_type=notification.notification_type,
    channel=notification.channel,  # ← Usa el canal de la notificación
    is_active=True,
)
```

4. **Envío según canal**:
```python
# Envío con parámetros específicos según el servicio
if notification.channel == choices.NotificationChannel.WHATSAPP:
    result = messaging_service.send_message_with_button(
        recipient_phone=recipient_identifier,  # WhatsApp usa 'recipient_phone'
        message=message,
        button_text=payment_button_text,
        button_url=notification.payment_link_url,
    )
elif notification.channel == choices.NotificationChannel.TELEGRAM:
    result = messaging_service.send_message_with_button(
        recipient_id=recipient_identifier,  # Telegram usa 'recipient_id'
        message=message,
        button_text=payment_button_text,
        button_url=notification.payment_link_url,
    )
```

**Beneficios**:
- ✅ Código reutilizable para ambos canales
- ✅ Misma lógica de reintentos y manejo de errores
- ✅ Fácil agregar nuevos canales en el futuro

---

### 4. Variables de Entorno
**Archivo**: `.env.example`

```diff
# WhatsApp Business API Configuration
WHATSAPP_API_TOKEN=your_whatsapp_access_token_here
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id_here
WHATSAPP_BUSINESS_ACCOUNT_ID=your_business_account_id_here
WHATSAPP_API_VERSION=v21.0

+ # Telegram Bot API Configuration
+ # Crear bot con @BotFather en Telegram: https://t.me/botfather
+ TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
```

---

## Modelos (Sin Cambios)

Los modelos existentes **ya soportan Telegram** sin necesidad de migraciones:

### CampaignNotification
- ✅ Campo `channel` acepta `NotificationChannel.TELEGRAM`
- ✅ Campo `recipient_phone` se reutiliza para almacenar `chat_id` o `@username`
- ✅ Constraint único incluye `channel` para evitar duplicados

### MessageTemplate
- ✅ Campo `channel` acepta `NotificationChannel.TELEGRAM`
- ✅ Campo `message_body` soporta placeholders estándar
- ✅ Campo `include_payment_button` funciona para ambos canales

### Campaign
- ✅ No requiere cambios, funciona con cualquier canal

---

## Configuración Requerida

### 1. Instalar Dependencias

```bash
pip install -r requirements/base.txt
```

### 2. Crear Bot en Telegram

1. Abrir Telegram y buscar [@BotFather](https://t.me/botfather)
2. Enviar comando `/newbot`
3. Seguir instrucciones para crear el bot
4. Copiar el token de acceso proporcionado

### 3. Configurar Variables de Entorno

Agregar al archivo `.env`:

```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

### 4. Reiniciar Servicios

```bash
# Reiniciar Django
python manage.py runserver

# Reiniciar Celery Worker
celery -A config worker -l info

# Reiniciar Celery Beat
celery -A config beat -l info
```

---

## Cómo Usar

### Opción 1: Usando el Admin de Django

1. **Crear Plantilla**:
   - Ir a **Campaigns > Message Templates**
   - Crear plantilla con **Channel = Telegram**

2. **Crear Campaña**:
   - Ir a **Campaigns > Campaigns**
   - Seleccionar grupo de socios
   - Configurar fecha de ejecución

3. **Procesar Campaña**:
   - Ejecutar desde shell: `process_campaign_notifications(campaign_id)`

4. **Enviar Notificaciones**:
   - Automático vía Celery Beat cada 10 minutos
   - O manual: `send_scheduled_notifications()`

### Opción 2: Programáticamente

```python
from apps.campaigns.models import Campaign, CampaignNotification
from apps.campaigns.choices import NotificationChannel, NotificationType

# Crear notificación Telegram
notification = CampaignNotification.objects.create(
    campaign=campaign,
    partner=partner,
    notification_type=NotificationType.SCHEDULED,
    channel=NotificationChannel.TELEGRAM,  # ← Especificar canal
    recipient_phone="123456789",  # Chat ID del socio
    scheduled_at=timezone.now(),
)

# Enviar
from apps.campaigns.tasks import send_notification
send_notification(notification.id)
```

### Opción 3: Mensaje Directo

```python
from apps.core.services.chats.telegram import telegram_service

# Enviar mensaje simple
telegram_service.send_text_message(
    recipient_id="123456789",
    message="Hola, tienes una deuda pendiente de S/ 500.00"
)

# Enviar con botón
telegram_service.send_message_with_button(
    recipient_id="@juanperez",
    message="Deuda: S/ 500.00",
    button_text="💳 Pagar Ahora",
    button_url="https://pay.example.com?partner=1"
)
```

---

## Obtener Chat IDs de Usuarios

### Método 1: Bot @userinfobot
El usuario envía un mensaje a [@userinfobot](https://t.me/userinfobot) y recibe su chat_id.

### Método 2: getUpdates API
1. Usuario inicia conversación con tu bot (botón START)
2. Visitar: `https://api.telegram.org/bot<TOKEN>/getUpdates`
3. Buscar: `"chat":{"id": 123456789}`

### Método 3: Username Público
Si el usuario tiene username público (ej: @juanperez), usar directamente:
```python
recipient_id = "@juanperez"
```

---

## Ventajas de Esta Implementación

### 1. Consistencia
- ✅ Misma arquitectura que WhatsApp
- ✅ Reutiliza servicios, tareas y modelos existentes
- ✅ Misma lógica de reintentos y manejo de errores

### 2. Flexibilidad
- ✅ Fácil agregar nuevos canales (SMS, Email)
- ✅ Soporte para múltiples canales simultáneos
- ✅ Plantillas personalizables por canal

### 3. Robustez
- ✅ Reintentos automáticos (hasta 3 intentos)
- ✅ Logging detallado
- ✅ Manejo de errores granular
- ✅ Validación de configuración

### 4. Escalabilidad
- ✅ Procesamiento asíncrono con Celery
- ✅ Singleton pattern para servicios
- ✅ Índices de base de datos optimizados

---

## Comparación: WhatsApp vs Telegram

| Característica | WhatsApp | Telegram |
|----------------|----------|----------|
| **Costo** | Pago por mensaje | Gratuito |
| **Botones URL** | Limitado* | Nativo |
| **Aprobación** | Plantillas requieren aprobación | No requiere |
| **Formato** | Texto plano | HTML/Markdown |
| **Identificador** | Número telefónico | chat_id o @username |
| **Rate Limit** | 1000 msg/día (tier 1) | 30 msg/segundo |

*WhatsApp requiere plantillas aprobadas para botones. El sistema actual envía el link en el texto.

---

## Testing

### 1. Verificar Configuración

```python
from apps.core.services.chats.telegram import telegram_service

# Verificar servicio
print(telegram_service.is_configured())  # True

# Verificar bot
print(telegram_service.verify_bot())
# {'success': True, 'bot_id': 123456789, ...}
```

### 2. Enviar Mensaje de Prueba

```python
# Usar tu propio chat_id para testing
result = telegram_service.send_text_message(
    recipient_id="TU_CHAT_ID",
    message="Mensaje de prueba"
)
print(result)  # {'success': True, 'message_id': 123, ...}
```

### 3. Crear Campaña de Prueba

Ver ejemplos completos en `docs/TELEGRAM_EXAMPLES.py` (19 ejemplos).

---

## Solución de Problemas Comunes

### Error: "Telegram service is not configured"
**Solución**: Verificar que `TELEGRAM_BOT_TOKEN` esté en `.env` y reiniciar servidor.

### Error: "Chat not found"
**Solución**: El usuario debe iniciar conversación con el bot primero (botón START).

### Error: "Forbidden: bot was blocked"
**Solución**: El usuario bloqueó el bot. Debe desbloquearlo manualmente.

### Mensaje no se envía (status PENDING)
**Solución**: Verificar que Celery Worker y Beat estén corriendo.

---

## Próximos Pasos Recomendados

### Para Desarrollo
- [ ] Agregar campo `telegram_chat_id` dedicado al modelo `Partner`
- [ ] Crear formulario en Admin para obtener chat_ids
- [ ] Agregar tests unitarios e integración
- [ ] Implementar webhook para recibir mensajes

### Para Producción
- [ ] Configurar Celery Beat en servidor
- [ ] Configurar logging persistente
- [ ] Agregar monitoreo y alertas
- [ ] Implementar rate limiting
- [ ] Documentar proceso de obtención de chat_ids para usuarios finales

---

## Recursos Adicionales

- **Documentación completa**: [docs/TELEGRAM_INTEGRATION.md](docs/TELEGRAM_INTEGRATION.md)
- **Ejemplos de código**: [docs/TELEGRAM_EXAMPLES.py](docs/TELEGRAM_EXAMPLES.py)
- **Documentación de WhatsApp**: [docs/WHATSAPP_INTEGRATION.md](docs/WHATSAPP_INTEGRATION.md)
- **Telegram Bot API**: https://core.telegram.org/bots/api
- **python-telegram-bot**: https://python-telegram-bot.readthedocs.io/
- **BotFather**: https://t.me/botfather

---

## Soporte

Para preguntas o problemas:
1. Revisar logs del servidor: `apps/campaigns/tasks.py`
2. Consultar documentación en `docs/TELEGRAM_INTEGRATION.md`
3. Ver ejemplos en `docs/TELEGRAM_EXAMPLES.py`
4. Revisar Admin de Django: Campaign Notifications

---

**Fecha de Implementación**: Octubre 2025
**Versión**: 1.0
**Estado**: ✅ Completado y Listo para Uso
