# Integración con BulkGate

Esta documentación describe la integración con BulkGate para envío de mensajes a través de múltiples canales: SMS, Viber, WhatsApp y RCS.

## Tabla de Contenidos

1. [Descripción General](#descripción-general)
2. [Configuración](#configuración)
3. [Uso Básico](#uso-básico)
4. [Funcionalidades Avanzadas](#funcionalidades-avanzadas)
5. [Ejemplos de Uso](#ejemplos-de-uso)
6. [Troubleshooting](#troubleshooting)

## Descripción General

BulkGate es un proveedor de mensajería multi-canal que permite enviar notificaciones a través de:

- **SMS**: Mensajería de texto tradicional (canal principal)
- **Viber**: Mensajería empresarial con mejor engagement
- **WhatsApp**: Integración con WhatsApp Business
- **RCS**: Rich Communication Services (mensajes enriquecidos)

### Características Principales

- ✅ Envío de SMS individual y masivo
- ✅ Mensajes personalizados con variables
- ✅ Programación de envíos
- ✅ Cascade de canales (fallback automático)
- ✅ Soporte para mensajes Unicode (hasta 268 caracteres)
- ✅ Mensajes largos (hasta 612 caracteres estándar)
- ✅ Tracking de mensajes con tags
- ✅ Sender ID personalizable

## Configuración

### 1. Obtener Credenciales

1. Crear cuenta en [BulkGate](https://www.bulkgate.com/)
2. Ir a la sección de configuración de aplicación
3. Obtener el `Application ID` y `Application Token`

### 2. Configurar Variables de Entorno

Agregar las siguientes variables al archivo `.env`:

```bash
# BulkGate - Configuración Básica (Requerido)
BULKGATE_APPLICATION_ID=your_application_id_here
BULKGATE_APPLICATION_TOKEN=your_application_token_here

# BulkGate - Configuración Opcional
BULKGATE_DEFAULT_SENDER=YourCompany      # Nombre/ID del remitente
BULKGATE_DEFAULT_COUNTRY=PE               # Código de país por defecto (ISO 3166-1)

# Canales Adicionales (Opcional)
BULKGATE_ENABLE_VIBER=False              # Habilitar Viber
BULKGATE_ENABLE_WHATSAPP=False           # Habilitar WhatsApp
BULKGATE_ENABLE_RCS=False                # Habilitar RCS

# Proveedor SMS por defecto
SMS_PROVIDER=bulkgate
```

### 3. Verificar Instalación

El proveedor se registra automáticamente al iniciar la aplicación. Para verificar:

```python
from apps.notifications.providers.factory import ProviderFactory
from apps.campaigns.choices import NotificationChannel

# Obtener información del proveedor
provider_info = ProviderFactory.get_available_providers(
    NotificationChannel.SMS
)
print(provider_info)
```

## Uso Básico

### Envío de SMS Simple

```python
from apps.notifications.providers.factory import ProviderFactory
from apps.campaigns.choices import NotificationChannel

# Obtener el proveedor
provider = ProviderFactory.get_provider(NotificationChannel.SMS)

# Enviar mensaje
result = provider.send_text_message(
    recipient="51987654321",  # Número en formato internacional
    message="Hola, este es un mensaje de prueba"
)

if result.get("success"):
    print(f"Mensaje enviado. ID: {result.get('message_id')}")
else:
    print(f"Error: {result.get('error')}")
```

### Envío con Enlace de Pago

```python
result = provider.send_message_with_button(
    recipient="51987654321",
    message="Tu deuda pendiente es S/ 100.00",
    button_text="Pagar Ahora",
    button_url="https://tusitio.com/pagar/12345"
)
```

**Nota**: En SMS, el botón se convierte en texto con el enlace al final del mensaje.

## Funcionalidades Avanzadas

### 1. Envío Masivo (Bulk SMS)

```python
# Enviar el mismo mensaje a múltiples destinatarios
result = provider.send_bulk_sms(
    recipients=[
        "51987654321",
        "51987654322",
        "51987654323"
    ],
    message="Mensaje para todos",
    tag="campaign_2024_01"  # Tag para tracking
)

print(f"Enviados: {result.get('total_sent')}")
print(f"Errores: {result.get('total_error')}")
```

### 2. Mensajes Personalizados

Enviar mensajes diferentes con variables dinámicas:

```python
recipients = [
    {
        "number": "51987654321",
        "variables": {
            "name": "Juan Pérez",
            "amount": "150.00",
            "due_date": "2024-01-31"
        }
    },
    {
        "number": "51987654322",
        "variables": {
            "name": "María García",
            "amount": "200.00",
            "due_date": "2024-01-31"
        }
    }
]

template = "Hola {name}, tu deuda de S/ {amount} vence el {due_date}. Paga pronto!"

result = provider.send_personalized_messages(
    recipients=recipients,
    template=template,
    tag="debt_reminder"
)
```

### 3. Programación de Envíos

```python
from datetime import datetime, timedelta

# Programar para envío en 24 horas
schedule_time = datetime.now() + timedelta(hours=24)
schedule_timestamp = int(schedule_time.timestamp())

result = provider.send_text_message(
    recipient="51987654321",
    message="Recordatorio programado",
    schedule=schedule_timestamp
)
```

### 4. Cascade de Canales (Multi-canal)

Enviar con fallback automático de Viber/WhatsApp a SMS:

```python
# Primero configurar en .env:
# BULKGATE_ENABLE_VIBER=True
# BULKGATE_ENABLE_WHATSAPP=True

result = provider.send_text_message(
    recipient="51987654321",
    message="Mensaje multi-canal",
    use_cascade=True  # Intenta Viber/WhatsApp primero, luego SMS
)
```

### 5. Sender ID Personalizado

```python
result = provider.send_text_message(
    recipient="51987654321",
    message="Mensaje con remitente personalizado",
    sender="MiEmpresa"  # Texto hasta 11 caracteres
)
```

## Ejemplos de Uso

### Integración con el Sistema de Notificaciones

El proveedor se integra automáticamente con el sistema de notificaciones de campañas:

```python
from apps.campaigns.models import CampaignNotification
from apps.campaigns.choices import NotificationChannel
from apps.notifications.services.sender_service import NotificationSenderService

# Crear notificación SMS
notification = CampaignNotification.objects.create(
    campaign=my_campaign,
    recipient=partner,
    channel=NotificationChannel.SMS,
    recipient_phone="51987654321",
    notification_type="SCHEDULED"
)

# Enviar usando el servicio
result = NotificationSenderService.send_notification(notification)
```

### Uso Directo del Proveedor

```python
from apps.notifications.providers.sms import BulkGateProvider

# Crear instancia directa
provider = BulkGateProvider()

# Verificar configuración
if provider.is_configured():
    # Enviar mensaje
    result = provider.send_text_message(
        recipient="51987654321",
        message="Mensaje directo",
        country="PE"  # Código de país
    )

    # Ver respuesta completa
    print(result.get("raw_response"))
```

### Análisis de Resultados

```python
result = provider.send_bulk_sms(
    recipients=["51987654321", "51987654322", "51987654323"],
    message="Test"
)

# Estadísticas
print(f"Total enviados: {result.get('total_sent')}")
print(f"Total aceptados: {result.get('total_accepted')}")
print(f"Total programados: {result.get('total_scheduled')}")
print(f"Total errores: {result.get('total_error')}")
print(f"Total inválidos: {result.get('total_invalid')}")
print(f"Total en lista negra: {result.get('total_blacklisted')}")

# IDs de mensajes
message_ids = result.get('message_ids', [])
for msg_id in message_ids:
    print(f"Mensaje enviado con ID: {msg_id}")

# Respuestas individuales
for response in result.get('responses', []):
    print(f"Número: {response.get('number')}")
    print(f"Canal: {response.get('channel')}")
    print(f"Estado: {response.get('status')}")
```

## Estructura del Código

### Archivos Creados

```
apps/notifications/providers/
├── sms/
│   ├── __init__.py
│   └── bulkgate.py          # Proveedor principal de BulkGate
└── factory.py               # Actualizado para incluir SMS
```

### Métodos Disponibles

#### `send_text_message(recipient, message, **kwargs)`
Envía un SMS de texto simple.

**Parámetros**:
- `recipient`: Número de teléfono en formato internacional
- `message`: Texto del mensaje (max 612 caracteres)
- `sender`: (opcional) ID del remitente
- `country`: (opcional) Código de país
- `schedule`: (opcional) Timestamp para programar
- `tag`: (opcional) Etiqueta para tracking
- `use_cascade`: (opcional) Habilitar multi-canal

#### `send_message_with_button(recipient, message, button_text, button_url, **kwargs)`
Envía mensaje con enlace (formato texto en SMS).

#### `send_bulk_sms(recipients, message, **kwargs)`
Envía el mismo mensaje a múltiples destinatarios.

#### `send_personalized_messages(recipients, template, **kwargs)`
Envía mensajes personalizados con variables.

#### `is_configured()`
Verifica si el proveedor está configurado correctamente.

#### `get_provider_info()`
Obtiene información sobre el proveedor y sus capacidades.

## Troubleshooting

### Error: "BulkGate provider is not configured"

**Causa**: Faltan las credenciales en `.env`

**Solución**:
```bash
# Verificar que estén configuradas:
BULKGATE_APPLICATION_ID=your_id
BULKGATE_APPLICATION_TOKEN=your_token
```

### Números de Teléfono Inválidos

**Formato correcto**: Sin `+`, sin espacios, formato internacional
- ✅ Correcto: `51987654321` (Perú)
- ❌ Incorrecto: `+51 987 654 321`
- ❌ Incorrecto: `987654321` (falta código de país)

El proveedor limpia automáticamente los números, pero para mejor resultado use formato internacional.

### Mensajes No Entregados

1. Verificar créditos en cuenta de BulkGate
2. Revisar que el número no esté en lista negra
3. Verificar formato del número
4. Revisar logs con `total_error` y `total_invalid`

### Error: "Request timeout"

**Causa**: Problemas de conectividad con API

**Solución**:
- Verificar conexión a internet
- El timeout por defecto es 30 segundos
- BulkGate API debe estar disponible

### Caracteres Especiales

Para mensajes con tildes, ñ, emojis:
- Se usa automáticamente codificación Unicode
- Límite: 268 caracteres (en lugar de 612)
- El proveedor maneja esto automáticamente

## Información Adicional

### Límites y Restricciones

- **SMS estándar**: 612 caracteres
- **SMS Unicode**: 268 caracteres
- **Rate limits**: Dependen de tu plan de BulkGate
- **Uso**: Solo para notificaciones transaccionales (no marketing masivo)

### Costos

Los costos dependen del plan contratado en BulkGate. Factores que afectan:
- País de destino
- Canal usado (SMS, Viber, WhatsApp, RCS)
- Volumen de mensajes

### Soporte

- **Documentación API**: https://help.bulkgate.com/
- **Soporte BulkGate**: https://www.bulkgate.com/en/support/

### Próximas Mejoras

- [ ] Webhooks para delivery reports
- [ ] Templates pre-aprobados de WhatsApp
- [ ] Mensajes RCS enriquecidos con botones
- [ ] Panel de estadísticas en tiempo real
