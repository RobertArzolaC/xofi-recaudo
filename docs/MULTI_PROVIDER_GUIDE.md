# Guía de Múltiples Proveedores

Esta guía explica cómo usar y cambiar entre múltiples proveedores para cada canal de mensajería.

## Tabla de Contenidos

1. [Proveedores Disponibles](#proveedores-disponibles)
2. [Configuración](#configuración)
3. [Cambiar de Proveedor](#cambiar-de-proveedor)
4. [Comparación de Proveedores](#comparación-de-proveedores)
5. [Casos de Uso](#casos-de-uso)
6. [Testing y Failover](#testing-y-failover)

## Proveedores Disponibles

### WhatsApp (3 opciones)

| Proveedor | Variable | Ventajas | Desventajas |
|-----------|----------|----------|-------------|
| **Meta** | `WHATSAPP_PROVIDER=meta` | ✅ Oficial<br>✅ API completa<br>✅ Templates aprobados | ❌ Proceso de aprobación largo<br>❌ Requiere Business Manager |
| **WHAPI** | `WHATSAPP_PROVIDER=whapi` | ✅ Rápido setup<br>✅ Sin aprobaciones<br>✅ Botones interactivos | ❌ Servicio de terceros<br>❌ Costo por mensaje |
| **BulkGate** | `WHATSAPP_PROVIDER=bulkgate` | ✅ Multi-canal<br>✅ Fallback a SMS<br>✅ Una sola API | ❌ Costo adicional<br>❌ Sin templates avanzados |

### SMS (1 opción)

| Proveedor | Variable | Características |
|-----------|----------|-----------------|
| **BulkGate** | `SMS_PROVIDER=bulkgate` | ✅ Envío masivo<br>✅ Personalización<br>✅ 200+ países |

### Telegram (1 opción)

| Proveedor | Variable | Características |
|-----------|----------|-----------------|
| **Telegram Bot** | - | ✅ Gratis<br>✅ Botones inline<br>✅ Sin límites |

## Configuración

### Opción 1: Solo SMS (BulkGate)

```bash
# .env
BULKGATE_APPLICATION_ID=tu_app_id
BULKGATE_APPLICATION_TOKEN=tu_token
SMS_PROVIDER=bulkgate
```

### Opción 2: SMS + WhatsApp con BulkGate

```bash
# .env
# BulkGate para ambos canales
BULKGATE_APPLICATION_ID=tu_app_id
BULKGATE_APPLICATION_TOKEN=tu_token
BULKGATE_DEFAULT_SENDER=TuEmpresa
BULKGATE_WHATSAPP_SMS_FALLBACK=True

# Configurar proveedores
SMS_PROVIDER=bulkgate
WHATSAPP_PROVIDER=bulkgate  # Usar BulkGate para WhatsApp
```

**Ventaja**: Con una sola cuenta de BulkGate, puedes enviar tanto SMS como WhatsApp, y si WhatsApp falla, automáticamente cae a SMS.

### Opción 3: Múltiples Proveedores (Recomendado para Producción)

```bash
# .env
# WhatsApp: Usar WHAPI (más fácil de configurar)
WHATSAPP_PROVIDER=whapi
WHAPI_API_TOKEN=tu_whapi_token

# SMS: Usar BulkGate (más robusto)
SMS_PROVIDER=bulkgate
BULKGATE_APPLICATION_ID=tu_app_id
BULKGATE_APPLICATION_TOKEN=tu_token

# Telegram
TELEGRAM_BOT_TOKEN=tu_bot_token
```

**Ventaja**: Usa el mejor proveedor para cada canal.

### Opción 4: Redundancia (Máxima Confiabilidad)

Configurar todos los proveedores y cambiar fácilmente entre ellos:

```bash
# .env
# Meta WhatsApp (oficial)
WHATSAPP_API_TOKEN=tu_meta_token
WHATSAPP_PHONE_NUMBER_ID=tu_phone_id

# WHAPI (backup)
WHAPI_API_TOKEN=tu_whapi_token

# BulkGate (SMS + WhatsApp backup)
BULKGATE_APPLICATION_ID=tu_app_id
BULKGATE_APPLICATION_TOKEN=tu_token

# Proveedores activos
WHATSAPP_PROVIDER=whapi  # Cambiar a 'meta' o 'bulkgate' si falla
SMS_PROVIDER=bulkgate
```

## Cambiar de Proveedor

### Durante Desarrollo

Edita tu archivo `.env`:

```bash
# Cambiar proveedor de WhatsApp
WHATSAPP_PROVIDER=bulkgate  # Cambiar de 'whapi' a 'bulkgate'
```

Reinicia el servidor:

```bash
python manage.py runserver
```

### En Producción (Sin Reiniciar)

Puedes cambiar el proveedor dinámicamente en el código:

```python
from apps.notifications.providers.factory import ProviderFactory
from apps.campaigns.choices import NotificationChannel

# Obtener proveedor por defecto
provider = ProviderFactory.get_provider(NotificationChannel.WHATSAPP)

# O especificar uno manualmente
from apps.notifications.providers.whatsapp import BulkGateWhatsAppProvider
provider = BulkGateWhatsAppProvider()
```

## Comparación de Proveedores

### WhatsApp: ¿Cuál usar?

#### Meta (Facebook/WhatsApp Oficial)
```python
WHATSAPP_PROVIDER=meta
```

**Usar cuando**:
- Necesitas templates oficiales aprobados
- Volumen muy alto (millones de mensajes)
- Integración oficial requerida por negocio
- Tienes tiempo para proceso de aprobación

**No usar cuando**:
- Necesitas empezar rápido
- Mensajes personalizados frecuentes
- Prototipado o desarrollo

#### WHAPI
```python
WHATSAPP_PROVIDER=whapi
```

**Usar cuando**:
- Necesitas empezar en minutos
- Mensajes personalizados
- Botones y multimedia
- Testing y desarrollo

**No usar cuando**:
- Presupuesto muy ajustado (costo por mensaje)
- Volumen extremadamente alto

#### BulkGate WhatsApp
```python
WHATSAPP_PROVIDER=bulkgate
```

**Usar cuando**:
- Ya usas BulkGate para SMS
- Quieres fallback automático a SMS
- Necesitas una sola factura/cuenta
- Multi-canal (WhatsApp + SMS + Viber)

**No usar cuando**:
- Necesitas templates avanzados de WhatsApp
- Solo necesitas WhatsApp (sobrepago)

## Casos de Uso

### Caso 1: Startup - Comenzando Rápido

**Objetivo**: Empezar a enviar notificaciones lo antes posible.

**Recomendación**:
```bash
WHATSAPP_PROVIDER=whapi
TELEGRAM_BOT_TOKEN=tu_token
```

**Por qué**: WHAPI es el más rápido de configurar (5 minutos), Telegram es gratis.

### Caso 2: Notificaciones de Cobro

**Objetivo**: Maximizar entrega de recordatorios de pago.

**Recomendación**:
```bash
WHATSAPP_PROVIDER=bulkgate
SMS_PROVIDER=bulkgate
BULKGATE_WHATSAPP_SMS_FALLBACK=True
```

**Por qué**: Si WhatsApp falla, automáticamente envía SMS. Máxima tasa de entrega.

### Caso 3: Alto Volumen en Producción

**Objetivo**: Escalar a miles de mensajes diarios.

**Recomendación**:
```bash
# Principal
WHATSAPP_PROVIDER=meta
SMS_PROVIDER=bulkgate

# Backup configurado pero inactivo
WHAPI_API_TOKEN=backup_token
```

**Por qué**: Meta es más económico a gran escala, BulkGate robusto para SMS.

### Caso 4: Testing de Integraciones

**Objetivo**: Probar diferentes proveedores sin afectar producción.

**Estrategia**:

```python
# En tu código de prueba
def test_whatsapp_providers():
    from apps.notifications.providers.whatsapp import (
        MetaWhatsAppProvider,
        WHAPIProvider,
        BulkGateWhatsAppProvider
    )

    # Probar cada uno
    for ProviderClass in [MetaWhatsAppProvider, WHAPIProvider, BulkGateWhatsAppProvider]:
        provider = ProviderClass()
        if provider.is_configured():
            result = provider.send_text_message(
                recipient="51987654321",
                message="Test"
            )
            print(f"{provider.get_provider_name()}: {result.get('success')}")
```

## Testing y Failover

### Script de Prueba de Proveedores

```python
# test_providers.py
from apps.notifications.providers.factory import ProviderFactory
from apps.campaigns.choices import NotificationChannel

def test_all_whatsapp_providers():
    """Probar todos los proveedores de WhatsApp disponibles."""

    test_number = "51987654321"  # Tu número de prueba

    providers_to_test = ["meta", "whapi", "bulkgate"]
    results = {}

    for provider_name in providers_to_test:
        print(f"\n🔍 Probando proveedor: {provider_name}")

        # Cambiar proveedor temporalmente
        import os
        os.environ['WHATSAPP_PROVIDER'] = provider_name

        # Obtener proveedor
        provider = ProviderFactory.get_provider(NotificationChannel.WHATSAPP)

        if not provider or not provider.is_configured():
            print(f"❌ {provider_name} no configurado")
            results[provider_name] = {"configured": False}
            continue

        # Enviar mensaje de prueba
        result = provider.send_text_message(
            recipient=test_number,
            message=f"Test desde {provider_name}"
        )

        results[provider_name] = {
            "configured": True,
            "success": result.get("success"),
            "message_id": result.get("message_id"),
            "error": result.get("error")
        }

        if result.get("success"):
            print(f"✅ {provider_name} funcionando correctamente")
        else:
            print(f"❌ {provider_name} falló: {result.get('error')}")

    return results

# Ejecutar
if __name__ == "__main__":
    results = test_all_whatsapp_providers()
    print("\n📊 Resumen:")
    for provider, result in results.items():
        print(f"{provider}: {result}")
```

### Implementar Failover Automático

```python
# services/failover_sender.py
from typing import List, Dict
from apps.notifications.providers.factory import ProviderFactory
from apps.campaigns.choices import NotificationChannel

class FailoverSender:
    """Envía mensajes con failover automático entre proveedores."""

    # Orden de prioridad para WhatsApp
    WHATSAPP_PRIORITY = ["whapi", "bulkgate", "meta"]

    @classmethod
    def send_whatsapp_with_failover(
        cls,
        recipient: str,
        message: str
    ) -> Dict:
        """
        Intenta enviar WhatsApp usando múltiples proveedores.

        Returns:
            dict: Resultado con proveedor usado
        """
        import os

        for provider_name in cls.WHATSAPP_PRIORITY:
            print(f"Intentando con {provider_name}...")

            # Cambiar proveedor
            os.environ['WHATSAPP_PROVIDER'] = provider_name

            # Obtener proveedor
            provider = ProviderFactory.get_provider(NotificationChannel.WHATSAPP)

            if not provider or not provider.is_configured():
                print(f"⚠️  {provider_name} no disponible")
                continue

            # Intentar enviar
            result = provider.send_text_message(
                recipient=recipient,
                message=message
            )

            if result.get("success"):
                print(f"✅ Enviado con {provider_name}")
                result["provider_used"] = provider_name
                return result

            print(f"❌ Falló con {provider_name}: {result.get('error')}")

        return {
            "success": False,
            "error": "Todos los proveedores fallaron",
            "providers_tried": cls.WHATSAPP_PRIORITY
        }

# Uso
result = FailoverSender.send_whatsapp_with_failover(
    recipient="51987654321",
    message="Mensaje con failover"
)
```

## Ver Proveedores Disponibles

```python
from apps.notifications.providers.factory import ProviderFactory
from apps.campaigns.choices import NotificationChannel

# Ver todos los proveedores de WhatsApp
providers_info = ProviderFactory.get_available_providers(
    NotificationChannel.WHATSAPP
)

for name, info in providers_info.items():
    print(f"\nProveedor: {name}")
    print(f"  Configurado: {info['configured']}")
    print(f"  Soporta botones: {info.get('supports_buttons', False)}")
    print(f"  Características: {info.get('features', {})}")
```

## Recomendaciones

### Para Desarrollo
- ✅ WHAPI para WhatsApp (rápido)
- ✅ Telegram Bot (gratis)
- ⚠️ BulkGate solo si necesitas SMS

### Para Producción Pequeña (< 1000 msg/día)
- ✅ WHAPI para WhatsApp
- ✅ BulkGate para SMS
- ✅ Telegram Bot

### Para Producción Grande (> 10k msg/día)
- ✅ Meta para WhatsApp (más económico)
- ✅ BulkGate para SMS
- ✅ Configurar failover con WHAPI como backup

### Para Máxima Confiabilidad
- ✅ Configurar TODOS los proveedores
- ✅ Implementar failover automático
- ✅ Monitorear tasas de éxito
- ✅ Rotar según performance

## Monitoreo

```python
# Crear un comando para monitorear proveedores
from django.core.management.base import BaseCommand
from apps.notifications.providers.factory import ProviderFactory
from apps.campaigns.choices import NotificationChannel

class Command(BaseCommand):
    help = 'Verificar estado de todos los proveedores'

    def handle(self, *args, **options):
        channels = [
            NotificationChannel.WHATSAPP,
            NotificationChannel.SMS,
            NotificationChannel.TELEGRAM
        ]

        for channel in channels:
            self.stdout.write(f"\n{channel}:")
            providers = ProviderFactory.get_available_providers(channel)

            for name, info in providers.items():
                status = "✅" if info['configured'] else "❌"
                self.stdout.write(f"  {status} {name}: {info}")
```

Ejecutar con:
```bash
python manage.py check_providers
```
