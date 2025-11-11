# WhatsApp Chatbot - Guía de Inicio Rápido

Esta guía te ayudará a configurar el chatbot de WhatsApp en minutos usando WHAPI.

## 📋 Requisitos Previos

- Servidor Django en ejecución
- Migraciones de base de datos aplicadas
- Acceso a un número de WhatsApp
- Servidor accesible desde internet (para webhooks)

## 🚀 Configuración en 5 Pasos

### 1️⃣ Crear Cuenta en WHAPI

1. Ve a [https://whapi.cloud/](https://whapi.cloud/)
2. Registra una cuenta gratuita o de pago
3. Crea un nuevo canal

### 2️⃣ Vincular WhatsApp

1. En el panel de WHAPI, verás un código QR
2. Abre WhatsApp en tu teléfono
3. Ve a Configuración > Dispositivos vinculados
4. Escanea el código QR
5. Tu WhatsApp quedará vinculado con WHAPI

### 3️⃣ Obtener Credenciales

En el panel de WHAPI:

1. Copia el **API Token**
2. Copia el **Phone Number ID** (o número de teléfono)

### 4️⃣ Configurar Variables de Entorno

Agrega estas variables a tu archivo `.env`:

```bash
# WhatsApp WHAPI Configuration
WHATSAPP_API_TOKEN=tu_token_de_whapi_aqui
WHATSAPP_PHONE_NUMBER_ID=tu_phone_number_id_aqui

# WHAPI Base URL (opcional)
WHAPI_BASE_URL=https://gate.whapi.cloud

# Base URL de tu servidor (para webhooks)
BASE_URL=https://tu-dominio.com
```

### 5️⃣ Configurar Webhook en WHAPI

1. En el panel de WHAPI, ve a **Settings > Webhooks**
2. Agrega esta URL: `https://tu-dominio.com/chatbot/webhook/whatsapp/`
3. Selecciona el evento: **messages**
4. Haz clic en **Save**

¡Listo! Tu chatbot está configurado.

## ✅ Verificar Instalación

Ejecuta este comando para verificar la configuración:

```bash
python manage.py verify_whatsapp_config
```

Deberías ver algo como:

```
============================================================
WhatsApp Chatbot Configuration Verification
============================================================

✅ WhatsApp service is configured properly.

Configuration Details:
  Phone Number ID: 12345678901234
  API Token: ********************abc123xyz
  WHAPI Base URL: https://gate.whapi.cloud

Webhook Configuration:
  Webhook URL: https://tu-dominio.com/chatbot/webhook/whatsapp/

To configure the webhook in WHAPI:
  1. Go to https://whapi.cloud/
  2. Select your channel
  3. Go to Settings > Webhooks
  4. Set Webhook URL: https://tu-dominio.com/chatbot/webhook/whatsapp/
  5. Select event: 'messages'
  6. Click Save

Note: WHAPI doesn't require webhook verification tokens

Testing Service:
✅ WhatsApp service initialized successfully

============================================================
Verification Complete
============================================================
```

## 🧪 Probar el Chatbot

1. **Envía un mensaje de prueba**:
   - Desde tu teléfono, envía "Hola" al número vinculado

2. **Deberías recibir**:
   ```
   ¡Hola! Soy tu asistente virtual de Xofi.

   Para comenzar, necesito autenticarte. Por favor envía:
   DNI [tu_número] año [año_nacimiento]

   Ejemplo: DNI 12345678 año 1990
   ```

3. **Autentícate**:
   - Envía tu DNI y año de nacimiento
   - Ejemplo: `DNI 12345678 año 1990`

4. **Usa el chatbot**:
   - Una vez autenticado, prueba comandos como:
     - "Mi información"
     - "Estado de cuenta"
     - "Mis préstamos"
     - "Ayuda"

## 📱 Probar Localmente con ngrok

Si quieres probar en tu computadora local:

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

4. **Copia la URL de ngrok** (ej: `https://abc123.ngrok.io`)

5. **Actualiza el webhook en WHAPI**:
   - URL: `https://abc123.ngrok.io/chatbot/webhook/whatsapp/`

6. **Prueba enviando mensajes**

## 🔍 Ver Logs en Tiempo Real

```bash
# Ver todos los logs
tail -f /var/log/django.log

# Ver solo logs del chatbot
tail -f /var/log/django.log | grep chatbot

# Si usas Docker
docker logs -f tu-contenedor
```

## 📊 Estructura de Mensajes WHAPI

Cuando recibes un mensaje, WHAPI envía esta estructura:

```json
{
    "messages": [
        {
            "id": "msg-id",
            "from_me": false,
            "type": "text",
            "from": "51987654321",
            "text": {
                "body": "Hola"
            }
        }
    ],
    "event": {
        "type": "messages",
        "event": "post"
    },
    "channel_id": "tu-canal-id"
}
```

## 🎯 Comandos Disponibles

Una vez autenticado, el usuario puede usar:

| Mensaje | Acción |
|---------|--------|
| "Hola" / "Buenos días" | Saludo + menú |
| "Ayuda" / "Help" | Lista de comandos |
| "Mi información" | Ver datos personales |
| "Estado de cuenta" | Ver resumen de deudas |
| "Mis préstamos" | Lista de créditos |
| "Detalle préstamo [ID]" | Info de un préstamo |
| "Crear ticket" | Iniciar ticket de soporte |
| "Subir boleta" | Instrucciones para comprobante |
| [Enviar imagen] | Subir comprobante de pago |

## ❓ Solución de Problemas Comunes

### Problema: No recibo mensajes

**Solución**:
1. Verifica que el webhook esté configurado en WHAPI
2. Verifica que tu servidor sea accesible desde internet
3. Revisa los logs: `tail -f /var/log/django.log`

### Problema: El bot no responde

**Solución**:
1. Verifica las credenciales en `.env`
2. Verifica que el servicio de WhatsApp esté configurado:
   ```bash
   python manage.py verify_whatsapp_config
   ```
3. Revisa los logs de error

### Problema: Error 403 o 401

**Causa**: Token de API inválido

**Solución**:
1. Ve a WHAPI y copia nuevamente el token
2. Actualiza `WHATSAPP_API_TOKEN` en `.env`
3. Reinicia el servidor

### Problema: "No se pudo descargar la imagen"

**Causa**: Error al descargar archivos multimedia

**Solución**:
1. Verifica que `WHAPI_BASE_URL` esté configurado
2. Verifica que el token tenga permisos para descargar media
3. Revisa los logs para más detalles

## 📚 Documentación Completa

Para más información detallada, consulta:
- [Documentación Completa](./WHATSAPP_CHATBOT_INTEGRATION.md)
- [Arquitectura del Sistema](./WHATSAPP_CHATBOT_INTEGRATION.md#arquitectura)
- [Flujos de Mensajes](./WHATSAPP_CHATBOT_INTEGRATION.md#flujo-de-mensajes)

## 🆘 Soporte

Si tienes problemas:
1. Revisa los logs del servidor
2. Consulta la documentación completa
3. Verifica la configuración con `verify_whatsapp_config`
4. Revisa el panel de WHAPI para ver el estado del webhook

---

**Última actualización**: 2025-01-11
