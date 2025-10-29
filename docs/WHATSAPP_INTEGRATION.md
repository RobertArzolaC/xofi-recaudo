# Integración con Meta WhatsApp Business API

Este documento describe la integración implementada para enviar mensajes automatizados de WhatsApp mediante campañas de cobranza.

## Características Implementadas

### 1. Servicio de WhatsApp
- **Ubicación**: `apps/core/utils/whatsapp.py`
- **Funcionalidades**:
  - Envío de mensajes de texto
  - Envío de mensajes con plantillas aprobadas de Meta
  - Envío de mensajes con botones/links de pago
  - Limpieza y validación de números telefónicos (formato Perú)

### 2. Modelo de Plantillas de Mensajes
- **Ubicación**: `apps/campaigns/models.py` (clase `MessageTemplate`)
- **Características**:
  - Tipo de notificación simplificado: `SCHEDULED` (Notificación Programada)
  - Soporte para múltiples canales (WhatsApp, Email, SMS)
  - Sistema de placeholders para personalización
  - Configuración de botones de pago
  - Vinculación con plantillas aprobadas de WhatsApp Business

#### Placeholders Disponibles:
- `{partner_name}`: Nombre del socio
- `{debt_amount}`: Monto total de deuda
- `{credit_debt}`: Deuda de créditos
- `{credit_debt_count}`: Cantidad de cuotas pendientes
- `{contribution_debt}`: Deuda de aportaciones
- `{contribution_debt_count}`: Cantidad de aportaciones pendientes
- `{social_security_debt}`: Deuda de seguridad social
- `{social_security_debt_count}`: Cantidad de obligaciones de SS pendientes
- `{penalty_debt}`: Deuda de penalidades
- `{penalty_debt_count}`: Cantidad de penalidades pendientes
- `{payment_link}`: Link de pago generado
- `{campaign_name}`: Nombre de la campaña
- `{company_name}`: Nombre de la empresa
- `{contact_phone}`: Teléfono de contacto

### 3. Servicio de Links de Pago
- **Ubicación**: `apps/payments/utils/payment_links.py`
- **Funcionalidades**:
  - Generación de links de pago genéricos
  - Tokens de seguridad para validación
  - Links específicos para deudas de socios
  - Preparado para integración futura con proveedores de pago

### 4. Tareas de Celery
- **Ubicación**: `apps/campaigns/tasks.py`

#### Tareas Disponibles:

##### `send_whatsapp_notification(notification_id)`
- Envía una notificación de WhatsApp individual
- Incluye reintentos automáticos (máx. 3 intentos)
- Genera mensaje detallado con desglose por concepto de deuda
- Registra intentos y errores

##### `process_campaign_notifications(campaign_id)`
- Procesa una campaña completa
- Crea notificaciones para todos los socios del grupo
- Genera links de pago si está configurado
- Programa notificaciones según la fecha de ejecución de la campaña (`execution_date`)
- Valida que la campaña tenga una fecha de ejecución configurada

##### `send_scheduled_notifications()`
- Revisa y envía notificaciones programadas
- Debe ejecutarse periódicamente (cada 5-10 minutos)
- Valida que las campañas estén activas antes de enviar

### 5. Configuración en el Admin de Django
- **Ubicación**: `apps/campaigns/admin.py`
- Interfaces administrativas para:
  - Gestión de campañas
  - Gestión de grupos de socios
  - Gestión de plantillas de mensajes
  - Monitoreo de notificaciones enviadas

## Configuración

### 1. Variables de Entorno

Agregar al archivo `.env`:

```env
# WhatsApp Business API Configuration
WHATSAPP_API_TOKEN=your_whatsapp_token_here
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id_here
WHATSAPP_BUSINESS_ACCOUNT_ID=your_business_account_id_here
WHATSAPP_API_VERSION=v21.0

# Payment Link Configuration
PAYMENT_LINK_BASE_URL=https://pay.example.com
```

### 2. Instalación de Dependencias

```bash
pip install -r requirements/base.txt
```

La dependencia nueva agregada es:
- `heyoo==0.1.8`: Librería oficial para WhatsApp Business Cloud API

### 3. Migraciones de Base de Datos

```bash
python manage.py makemigrations campaigns
python manage.py migrate
```

### 4. Configuración de Celery Beat

Para ejecutar las notificaciones programadas automáticamente, configurar una tarea periódica en Celery Beat:

```python
# Opción 1: Via Django Admin
# Ir a: Admin > Periodic Tasks > Add
# - Name: Send Scheduled Campaign Notifications
# - Task: campaigns.send_scheduled_notifications
# - Interval: Every 10 minutes

# Opción 2: Via código en settings
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'send-scheduled-notifications': {
        'task': 'campaigns.send_scheduled_notifications',
        'schedule': crontab(minute='*/10'),  # Cada 10 minutos
    },
}
```

## Flujo de Uso

### 1. Crear Plantillas de Mensajes

1. Ir al Admin de Django
2. Navegar a "Message Templates"
3. Crear plantilla de tipo "SCHEDULED" (Notificación Programada)

**Nota**: El sistema ahora utiliza un único tipo de notificación programada que se envía en la fecha y hora especificada en la campaña.

Ejemplo de plantilla:
```
Hola {partner_name},

Le recordamos que tiene obligaciones pendientes por un total de {debt_amount}.

📋 Detalle de sus obligaciones:
💳 Cuotas de crédito: {credit_debt} ({credit_debt_count} cuota(s))
📊 Aportaciones: {contribution_debt} ({contribution_debt_count} aportación(es))
🏥 Seguridad Social: {social_security_debt} ({social_security_debt_count} obligación(es))
⚠️ Penalidades: {penalty_debt} ({penalty_debt_count} penalidad(es))

💰 Puede realizar su pago aquí:
{payment_link}

Gracias por su atención.
Atentamente, {company_name}
```

### 2. Crear Grupos de Socios

1. Navegar a "Groups" en el Admin
2. Crear un grupo y agregar los socios objetivo
3. Configurar la prioridad del grupo

### 3. Crear y Configurar Campaña

1. Navegar a "Campaigns" en el Admin (o usar la interfaz web)
2. Crear nueva campaña:
   - **Nombre**: Asignar nombre descriptivo a la campaña
   - **Descripción**: Descripción detallada (opcional)
   - **Grupo**: Seleccionar grupo de socios objetivo
   - **Fecha de Ejecución** (`execution_date`): Establecer fecha y hora exacta para enviar las notificaciones
   - **Estado**: Configurar como "ACTIVE" para activar la campaña
   - **Monto Objetivo** (`target_amount`): Monto total de recaudación esperado (se auto-calcula desde el grupo)
   - **Costo Promedio** (`average_cost`): Costo promedio por notificación (opcional, para tracking)
   - **Usar Link de Pago**: ☑️ Marcar para incluir links de pago en las notificaciones

**Cambios importantes**:
- Ya no se utilizan fechas de inicio/fin separadas
- Se reemplazaron múltiples tipos de notificación por una única fecha de ejecución
- La configuración es más simple y directa

### 4. Procesar Campaña

Existen dos formas de procesar una campaña:

#### Opción A: Manual (via Django Shell)
```python
from apps.campaigns.tasks import process_campaign_notifications

# Procesar campaña ID 1
result = process_campaign_notifications.delay(1)
print(result.get())
```

#### Opción B: Automática (via interfaz web - por implementar)
- Botón en el admin para procesar campaña
- Vista personalizada para ejecutar campaña

### 5. Monitoreo

1. Navegar a "Campaign Notifications" en el Admin
2. Filtrar por campaña, estado, canal, etc.
3. Ver detalles de cada notificación:
   - Estado (Pendiente, Enviado, Fallido, Cancelado)
   - Intentos realizados
   - Mensaje enviado
   - Errores (si los hay)

## Estructura de Mensajes por Defecto

Cuando no existe una plantilla configurada, el sistema genera mensajes automáticos con el siguiente formato:

```
Hola [Nombre del Socio],

Le recordamos que tiene obligaciones pendientes por un total de S/ XXX.XX.

📋 *Detalle de sus obligaciones:*
💳 Cuotas de crédito: S/ XX.XX (X cuota(s))
📊 Aportaciones: S/ XX.XX (X aportación(es))
🏥 Seguridad Social: S/ XX.XX (X obligación(es))
⚠️ Penalidades: S/ XX.XX (X penalidad(es))

💰 Puede realizar su pago de forma rápida y segura:
👉 [Link de pago]

Para más información, contáctenos:
📞 +51 999 999 999

Gracias por su atención.
Atentamente, *Xofi*
```

**Nota**: Solo se incluyen en el mensaje los conceptos de deuda que tengan un valor mayor a 0.

## Obtención de Credenciales de WhatsApp Business

### Pasos para obtener las credenciales:

1. **Crear cuenta de Meta for Developers**
   - Ir a: https://developers.facebook.com/
   - Crear o iniciar sesión con cuenta de Facebook

2. **Crear una App de Business**
   - En el dashboard, crear una nueva app
   - Seleccionar tipo "Business"
   - Agregar el producto "WhatsApp"

3. **Configurar WhatsApp Business API**
   - En la sección de WhatsApp, encontrarás:
     - `Phone Number ID`: ID del número de teléfono
     - `WhatsApp Business Account ID`: ID de la cuenta de negocio
   - Generar un token de acceso permanente

4. **Obtener el Token de Acceso**
   - En "Settings" > "System Users" > crear un System User
   - Generar un token de acceso con permisos de WhatsApp Business
   - Guardar el token de forma segura

5. **Configurar Webhook (Opcional)**
   - Para recibir actualizaciones de estado de mensajes
   - Configurar URL de webhook en tu servidor
   - Verificar webhook con Meta

6. **Crear y Aprobar Plantillas (Opcional)**
   - Si deseas usar plantillas pre-aprobadas
   - Ir a "WhatsApp Manager" > "Message Templates"
   - Crear y enviar para aprobación (proceso de 24-48 horas)

## Cambios Recientes (v2.0)

### Simplificación del Sistema de Notificaciones

**Antes (v1.0)**:
- Campos separados: `start_date`, `end_date`, `execution_time`
- 4 tipos de notificaciones: `BEFORE_3_DAYS`, `ON_DUE_DATE`, `AFTER_3_DAYS`, `AFTER_7_DAYS`
- Múltiples switches de configuración para cada tipo de notificación
- Lógica compleja de cálculo de fechas de envío

**Ahora (v2.0)**:
- Campo unificado: `execution_date` (fecha y hora combinadas)
- 1 tipo de notificación: `SCHEDULED` (Notificación Programada)
- Configuración simplificada con fecha/hora directa
- Campo adicional: `average_cost` para tracking de costos

**Ventajas**:
- ✅ Configuración más intuitiva y directa
- ✅ Menos campos redundantes en el modelo
- ✅ Código más mantenible y simple
- ✅ Mejor experiencia de usuario en formularios
- ✅ Mayor flexibilidad en la programación de envíos

### Migración desde v1.0 a v2.0

Si ya tienes campañas creadas con la versión anterior, deberás actualizar tus datos:

```bash
# 1. Aplicar las migraciones
python manage.py migrate campaigns

# 2. Las migraciones automáticamente:
#    - Eliminarán los campos: start_date, end_date, execution_time,
#      notify_3_days_before, notify_on_due_date, notify_3_days_after, notify_7_days_after
#    - Agregarán los campos: execution_date, average_cost
#    - Actualizarán el campo notification_type en las notificaciones existentes

# 3. Actualizar campañas existentes manualmente:
#    - Accede al Admin de Django
#    - Actualiza cada campaña con su nueva execution_date
#    - Las campañas sin execution_date no se ejecutarán hasta que se configure

# 4. Actualizar plantillas de mensajes:
#    - Cambiar el template_type de las plantillas existentes a "SCHEDULED"
#    - O crear nuevas plantillas con el tipo correcto
```

**Nota Importante**: Las notificaciones programadas antiguas con tipos `BEFORE_3_DAYS`, `ON_DUE_DATE`, etc., se convertirán automáticamente a tipo `SCHEDULED` con la migración.

## Tareas Pendientes / Mejoras Futuras

- [ ] Implementar webhook para recibir estados de mensajes
- [ ] Integrar con proveedor de pagos real
- [ ] Agregar soporte para imágenes/documentos en mensajes
- [ ] Implementar plantillas interactivas de WhatsApp
- [ ] Agregar reportes de efectividad de campañas
- [ ] Implementar envío por Email y SMS
- [ ] Dashboard de métricas de campañas
- [ ] Tests unitarios y de integración
- [ ] Análisis de costos por campaña usando el campo `average_cost`

## Solución de Problemas

### Error: "Campaign has no execution date"
- **Causa**: La campaña no tiene configurada la fecha de ejecución
- **Solución**: Acceder al admin o interfaz web y configurar el campo `execution_date` con fecha y hora deseada

### Error: "WhatsApp service is not configured"
- Verificar que las variables de entorno estén configuradas correctamente
- Verificar que `WHATSAPP_API_TOKEN` y `WHATSAPP_PHONE_NUMBER_ID` no estén vacías

### Error: "Failed to send message"
- Verificar que el token de acceso sea válido
- Verificar que el número de teléfono esté en formato correcto (51XXXXXXXXX)
- Verificar límites de tasa de la API de WhatsApp
- Revisar logs en `apps/campaigns/tasks.py` para detalles

### Mensajes no se envían automáticamente
- Verificar que Celery esté corriendo: `celery -A config worker -l info`
- Verificar que Celery Beat esté corriendo: `celery -A config beat -l info`
- Verificar que la tarea periódica esté configurada en el admin
- Verificar que la campaña tenga `execution_date` configurada

### Números de teléfono no válidos
- El sistema asume números peruanos (código de país 51)
- Si el número tiene 9 dígitos, se agrega automáticamente el prefijo 51
- Para otros países, modificar el método `_clean_phone_number` en `whatsapp.py`

### Error después de actualizar a v2.0
- **Síntoma**: Campos antiguos aparecen en templates o formularios
- **Causa**: Archivos de templates o forms no actualizados
- **Solución**: Verificar que los siguientes archivos estén actualizados:
  - `templates/campaigns/campaign/list.html`
  - `templates/campaigns/campaign/detail.html`
  - `templates/campaigns/campaign/form.html`
  - `apps/campaigns/forms.py`
  - `apps/campaigns/admin.py`
  - `apps/campaigns/filtersets.py`

## Soporte

Para más información sobre la API de WhatsApp Business:
- Documentación oficial: https://developers.facebook.com/docs/whatsapp/cloud-api
- Biblioteca heyoo: https://github.com/Neurotech-HQ/heyoo

Para soporte del proyecto:
- Revisar logs de Celery y Django
- Consultar el modelo `CampaignNotification` para detalles de errores
