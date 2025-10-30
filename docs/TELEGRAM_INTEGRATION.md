# Integración con Telegram

Este documento describe la integración del sistema de campañas de recaudación con Telegram Bot API para el envío automatizado de notificaciones de cobranza.

## Tabla de Contenidos

- [Descripción General](#descripción-general)
- [Arquitectura](#arquitectura)
- [Configuración](#configuración)
- [Uso](#uso)
- [Comparación: WhatsApp vs Telegram](#comparación-whatsapp-vs-telegram)
- [Casos de Uso](#casos-de-uso)
- [Solución de Problemas](#solución-de-problemas)

---

## Descripción General

La integración con Telegram permite enviar mensajes automatizados de cobranza a través de un bot de Telegram. Esta implementación sigue la misma arquitectura y lógica que la integración de WhatsApp, garantizando consistencia en el comportamiento del sistema.

### Características Principales

- ✅ Envío de mensajes de texto personalizados
- ✅ Botones interactivos con links de pago
- ✅ Soporte para placeholders dinámicos
- ✅ Reintentos automáticos en caso de fallo
- ✅ Logging detallado de operaciones
- ✅ Misma lógica que WhatsApp (consistencia)

### Ventajas de Telegram

- **Gratuito**: Sin costos por mensaje (vs WhatsApp Business API)
- **Botones nativos**: Soporte completo para botones inline con URLs
- **IDs únicos**: Cada usuario tiene un chat_id único
- **Sin aprobación**: No requiere aprobación de plantillas (vs WhatsApp)
- **Formato HTML**: Soporte nativo para formateo de mensajes

---

## Arquitectura

### Componentes Principales

```
┌─────────────────────────────────────────────────────────┐
│ TelegramService                                          │
│ (apps/core/services/chats/telegram.py)                  │
├─────────────────────────────────────────────────────────┤
│ - send_text_message(recipient_id, message)              │
│ - send_message_with_button(recipient_id, message,       │
│                             button_text, button_url)     │
│ - verify_bot()                                           │
│ - is_configured()                                        │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ python-telegram-bot (v21.7)                             │
│ Librería oficial de Telegram Bot API                    │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ Telegram Bot API                                         │
│ https://api.telegram.org/bot<token>/                    │
└─────────────────────────────────────────────────────────┘
```

### Flujo de Envío de Notificaciones

```
┌─────────────────────────────────────────────────────────┐
│ 1. CREAR CAMPAÑA                                         │
│    - Seleccionar grupo de socios                         │
│    - Definir fecha/hora de ejecución                     │
│    - Seleccionar canal: TELEGRAM                         │
│    - Estado: ACTIVE o SCHEDULED                          │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 2. PROCESAR CAMPAÑA                                      │
│    Task: process_campaign_notifications                 │
│    - Iterar socios del grupo                             │
│    - Calcular deuda para cada socio                      │
│    - Crear CampaignNotification con channel=TELEGRAM    │
│    - recipient_phone = chat_id o @username               │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 3. ENVÍO PROGRAMADO                                      │
│    Task: send_scheduled_notifications                   │
│    - Buscar notificaciones PENDING con scheduled_at ≤ now│
│    - Encolar: send_notification.delay(notification_id)  │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 4. ENVÍO INDIVIDUAL                                      │
│    Task: send_notification                               │
│    - Detectar canal: TELEGRAM                            │
│    - Cargar TelegramService                              │
│    - Obtener plantilla (si existe)                       │
│    - Renderizar mensaje con contexto                     │
│    - Enviar vía telegram_service.send_message_*()       │
│    - Marcar como SENT o FAILED                           │
│    - Reintentar hasta 3 veces si falla                   │
└─────────────────────────────────────────────────────────┘
```

---

## Configuración

### 1. Crear un Bot de Telegram

1. Abrir Telegram y buscar [@BotFather](https://t.me/botfather)
2. Enviar el comando `/newbot`
3. Seguir las instrucciones:
   - Asignar un nombre al bot (ej: "Xofi Recaudo Bot")
   - Asignar un username (debe terminar en 'bot', ej: "xofi_recaudo_bot")
4. BotFather te dará un **token** de acceso. Guárdalo de forma segura.

Ejemplo de token:
```
123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

### 2. Obtener el Chat ID de un Usuario

Para enviar mensajes a un usuario, necesitas su **chat_id**. Hay varias formas de obtenerlo:

#### Opción A: Método Manual

1. El usuario debe iniciar una conversación con tu bot (buscar @tu_bot_username y presionar START)
2. Visitar: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Buscar el campo `"chat":{"id": 123456789}`
4. Ese número es el chat_id del usuario

#### Opción B: Usar Username

Si el usuario tiene un username público (ej: @juanperez), puedes usar directamente:
```
recipient_phone = "@juanperez"
```

#### Opción C: Bot de Utilidad

1. El usuario puede enviar un mensaje a [@userinfobot](https://t.me/userinfobot)
2. El bot responderá con su chat_id

### 3. Configurar Variables de Entorno

Agregar a tu archivo `.env`:

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

### 4. Instalar Dependencias

La librería ya está incluida en `requirements/base.txt`:

```bash
pip install -r requirements/base.txt
```

### 5. Ejecutar Migraciones

No se requieren migraciones adicionales, ya que el modelo `CampaignNotification` ya soporta el canal TELEGRAM.

### 6. Verificar Configuración

Desde Django shell:

```python
from apps.core.services.chats.telegram import telegram_service

# Verificar que el servicio está configurado
telegram_service.is_configured()
# True

# Verificar credenciales del bot
telegram_service.verify_bot()
# {'success': True, 'bot_id': 123456789, 'username': 'xofi_recaudo_bot', 'first_name': 'Xofi Recaudo Bot'}
```

---

## Uso

### 1. Crear Plantilla de Mensaje (Opcional)

En el Admin de Django:

1. Ir a **Campaigns > Message Templates**
2. Crear nueva plantilla:
   - **Name**: Notificación de Cobranza Telegram
   - **Template Type**: Scheduled Notification
   - **Channel**: Telegram
   - **Message Body**:
     ```
     Hola {partner_name},

     Le recordamos que tiene una deuda pendiente de {debt_amount}.

     Detalle:
     {credit_debt}
     {contribution_debt}
     {social_security_debt}
     {penalty_debt}

     Para más información, contáctenos al {contact_phone}.

     Gracias,
     {company_name}
     ```
   - **Include Payment Button**: ✅ (si deseas incluir botón de pago)
   - **Payment Button Text**: "💳 Pagar Ahora"
   - **Is Active**: ✅

### 2. Agregar Chat IDs a los Socios

En el Admin, editar cada socio (Partner):

1. Ir a **Partners > Partners**
2. Editar socio
3. En el campo **Phone** (se reutiliza para Telegram):
   - Ingresar el chat_id: `123456789`
   - O ingresar el username: `@juanperez`

> **Nota**: Para diferenciar entre WhatsApp y Telegram, puedes:
> - Usar el campo `phone` para WhatsApp (números)
> - Crear un campo personalizado `telegram_chat_id` (recomendado para producción)
> - Por ahora, el sistema usa `recipient_phone` para ambos canales

### 3. Crear Campaña con Canal Telegram

1. Ir a **Campaigns > Campaigns**
2. Crear nueva campaña:
   - **Name**: Cobranza Mensual Telegram - Enero 2025
   - **Group**: Seleccionar grupo de socios
   - **Execution Date**: Fecha/hora de envío
   - **Use Payment Link**: ✅ (si deseas incluir links)
   - **Status**: ACTIVE o SCHEDULED

3. Al crear notificaciones, especificar:
   - **Channel**: TELEGRAM
   - **Recipient Phone**: Chat ID o @username del socio

### 4. Ejecutar Campaña

#### Opción A: Procesamiento Manual

Desde Django shell:

```python
from apps.campaigns.tasks import process_campaign_notifications

# Procesar campaña (crear notificaciones)
campaign_id = 1
result = process_campaign_notifications(campaign_id)
print(result)

# Enviar notificaciones pendientes
from apps.campaigns.tasks import send_scheduled_notifications
result = send_scheduled_notifications()
print(result)
```

#### Opción B: Automático con Celery Beat

El sistema enviará automáticamente las notificaciones programadas cada 10 minutos si tienes Celery Beat configurado:

```python
# settings.py
CELERY_BEAT_SCHEDULE = {
    'send-scheduled-notifications': {
        'task': 'campaigns.send_scheduled_notifications',
        'schedule': crontab(minute='*/10'),
    },
}
```

### 5. Monitorear Envíos

En el Admin:

1. Ir a **Campaigns > Campaign Notifications**
2. Filtrar por:
   - **Channel**: Telegram
   - **Status**: SENT / FAILED / PENDING
3. Ver detalles:
   - Mensaje enviado
   - Timestamp de envío
   - Errores (si aplica)
   - Número de intentos

---

## Comparación: WhatsApp vs Telegram

| Característica | WhatsApp | Telegram |
|----------------|----------|----------|
| **API Oficial** | Meta Cloud API | Telegram Bot API |
| **Librería** | heyoo | python-telegram-bot |
| **Costo** | Pago por mensaje | Gratuito |
| **Aprobación de Plantillas** | Requerida | No requerida |
| **Botones con URL** | Limitado* | Soporte completo |
| **Identificador** | Número telefónico | chat_id o @username |
| **Formato** | Texto plano | HTML/Markdown |
| **Delivery Status** | Vía webhooks | Vía webhooks |
| **Rate Limits** | 1000 msg/día (tier 1) | 30 msg/segundo |

*WhatsApp requiere plantillas aprobadas para botones de URL. El sistema actual envía el link en el texto.

### Cuándo Usar Cada Canal

**Usar WhatsApp cuando:**
- Tus socios usan principalmente WhatsApp
- Necesitas alta confiabilidad (números telefónicos)
- Tienes presupuesto para mensajería

**Usar Telegram cuando:**
- Tus socios tienen Telegram
- Quieres minimizar costos
- Necesitas botones interactivos avanzados
- Quieres implementar rápidamente sin aprobaciones

**Usar Ambos (recomendado):**
- Crear dos campañas paralelas
- Una campaña con canal WhatsApp
- Otra campaña con canal Telegram
- Llegar a más socios con diferentes preferencias

---

## Casos de Uso

### Caso 1: Campaña Solo Telegram

```python
from apps.campaigns.models import Campaign, Group
from apps.campaigns.choices import NotificationChannel, CampaignStatus

# Crear campaña
campaign = Campaign.objects.create(
    name="Cobranza Telegram - Enero 2025",
    group=Group.objects.get(id=1),
    execution_date=timezone.now() + timedelta(hours=1),
    status=CampaignStatus.ACTIVE,
    use_payment_link=True,
)

# Crear notificaciones con canal Telegram
from apps.campaigns.tasks import process_campaign_notifications
result = process_campaign_notifications(campaign.id)
```

### Caso 2: Campaña Multi-Canal (WhatsApp + Telegram)

```python
# Crear dos notificaciones por socio, una por cada canal
for partner in campaign.group.partners.all():
    # Notificación WhatsApp
    CampaignNotification.objects.create(
        campaign=campaign,
        partner=partner,
        notification_type=NotificationType.SCHEDULED,
        channel=NotificationChannel.WHATSAPP,
        recipient_phone=partner.phone,  # Número telefónico
        scheduled_at=campaign.execution_date,
    )

    # Notificación Telegram
    CampaignNotification.objects.create(
        campaign=campaign,
        partner=partner,
        notification_type=NotificationType.SCHEDULED,
        channel=NotificationChannel.TELEGRAM,
        recipient_phone=partner.telegram_chat_id,  # Chat ID
        scheduled_at=campaign.execution_date,
    )
```

### Caso 3: Mensaje Manual a un Socio

```python
from apps.core.services.chats.telegram import telegram_service

# Enviar mensaje simple
result = telegram_service.send_text_message(
    recipient_id="123456789",
    message="Hola Juan, te recordamos que tienes una deuda pendiente de S/ 500.00"
)

# Enviar mensaje con botón de pago
result = telegram_service.send_message_with_button(
    recipient_id="@juanperez",
    message="Tienes una deuda de S/ 500.00",
    button_text="💳 Pagar Ahora",
    button_url="https://pay.example.com?partner=1&amount=500"
)
```

---

## Solución de Problemas

### Error: "Telegram service is not configured"

**Causa**: La variable `TELEGRAM_BOT_TOKEN` no está configurada.

**Solución**:
1. Verificar que `.env` contenga `TELEGRAM_BOT_TOKEN`
2. Reiniciar el servidor Django
3. Verificar desde shell:
   ```python
   from django.conf import settings
   print(settings.TELEGRAM_BOT_TOKEN)
   ```

### Error: "Chat not found" o "Bad Request: chat not found"

**Causa**: El chat_id es incorrecto o el usuario no ha iniciado conversación con el bot.

**Solución**:
1. El usuario debe buscar el bot en Telegram
2. Presionar el botón "START"
3. Verificar el chat_id usando `getUpdates`

### Error: "Forbidden: bot was blocked by the user"

**Causa**: El usuario bloqueó el bot.

**Solución**:
- El sistema marcará la notificación como FAILED
- El usuario debe desbloquear el bot manualmente

### Mensaje No Se Envía (Status: PENDING)

**Causa**: Celery Beat no está corriendo o la tarea no se encola.

**Solución**:
1. Verificar que Celery Worker esté corriendo:
   ```bash
   celery -A config worker -l info
   ```
2. Verificar que Celery Beat esté corriendo:
   ```bash
   celery -A config beat -l info
   ```
3. Ejecutar manualmente:
   ```python
   from apps.campaigns.tasks import send_scheduled_notifications
   send_scheduled_notifications()
   ```

### Botones No Aparecen

**Causa**: El campo `include_payment_button` no está activado o `payment_link_url` está vacío.

**Solución**:
1. Verificar plantilla tiene `include_payment_button=True`
2. Verificar campaña tiene `use_payment_link=True`
3. Verificar notificación tiene `payment_link_url` poblado

### Formato de Mensaje Roto

**Causa**: Telegram requiere HTML válido para el formateo.

**Solución**:
- Usar formato HTML básico:
  - `<b>negrita</b>`
  - `<i>cursiva</i>`
  - `<code>código</code>`
  - `<a href="URL">link</a>`
- Evitar tags no soportados

---

## Mejoras Futuras

- [ ] Agregar campo dedicado `telegram_chat_id` al modelo Partner
- [ ] Implementar webhook para recibir mensajes de socios
- [ ] Soporte para imágenes y documentos
- [ ] Comandos del bot (/start, /help, /deuda)
- [ ] Teclados personalizados (ReplyKeyboardMarkup)
- [ ] Notificaciones inline (InlineQueryHandler)
- [ ] Estadísticas de apertura de mensajes
- [ ] Integración con grupos de Telegram
- [ ] Modo de conversación (respuestas automáticas)

---

## Referencias

- [Documentación Oficial de Telegram Bot API](https://core.telegram.org/bots/api)
- [python-telegram-bot Library](https://python-telegram-bot.readthedocs.io/)
- [BotFather - Crear y Configurar Bots](https://t.me/botfather)
- [Guía de Formateo de Mensajes](https://core.telegram.org/bots/api#formatting-options)

---

## Soporte

Para preguntas o problemas con la integración de Telegram:

1. Revisar logs del servidor: `apps/campaigns/tasks.py`
2. Verificar Admin de Django: Campaign Notifications
3. Consultar documentación de WhatsApp (misma lógica): `docs/WHATSAPP_INTEGRATION.md`

---

**Última Actualización**: Octubre 2025
**Versión**: 1.0
**Autor**: Sistema Xofi Recaudo
