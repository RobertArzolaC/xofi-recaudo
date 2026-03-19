# Chatbot ERP Cooperativa — Especificación de Implementación

> Documento de referencia para replicar el chatbot existente en el nuevo ERP cooperativo.
> Basado en la implementación actual de `apps/chatbot/` de Reffi.

---

## 1. Contexto del nuevo proyecto

El nuevo sistema es un ERP administrativo para cooperativas que gestiona:
- Socios/Miembros y sus perfiles
- Cuentas de ahorro
- Préstamos e installments
- Aportaciones mensuales obligatorias
- Nóminas (boletas de pago)
- Notificaciones y alertas de vencimiento

El chatbot actúa como canal de autoservicio para los socios via WhatsApp y/o Telegram, permitiéndoles consultar su situación financiera sin contactar a un asesor.

---

## 2. Arquitectura general

```
Webhook (WhatsApp/Telegram)
        ↓
Validación de firma (HMAC-SHA256 / Secret Token)
        ↓
Celery Task: process_message(webhook_data, platform)
        ↓
MessagingService → extrae phone, name, contenido
        ↓
ConversationManager.handle_message()
    ├── AccountLinkerService → busca socio por DNI
    ├── AutoResponder → keywords/intents sin LLM
    ├── ActionDispatcher → ejecuta acción según intent
    └── AgentService → LLM (OpenRouter) con contexto cooperativa
        ↓
Plataforma adapter → envía respuesta
        ↓
Webhook de status → tracking SENT/DELIVERED/READ/FAILED
```

### Principios de diseño

- **Adapter pattern** para multi-plataforma: cada plataforma implementa la misma interfaz base
- **Dual-response**: keywords/intents simples → respuesta directa (0 tokens LLM); casos complejos → LLM
- **Async-first**: todo el procesamiento en Celery tasks, los webhooks solo enolan y responden 200
- **Idempotencia**: tracking de `platform_message_id` para no procesar mensajes duplicados
- **Forward-only stages**: la conversación solo avanza de stage, nunca retrocede

---

## 3. Modelos de base de datos

### 3.1 Conversation

Representa una sesión activa con un socio. Una por teléfono+plataforma.

```python
class Conversation(models.Model):
    # Relación con el ERP
    member = models.ForeignKey("members.Member", null=True, blank=True)  # socio identificado

    # Identificación del canal
    customer_phone = models.CharField(max_length=20)
    customer_name  = models.CharField(max_length=200, blank=True)
    platform       = models.CharField(choices=MessagingPlatform.choices)
    session_id     = models.CharField(max_length=200, blank=True)

    # Estado de la conversación
    stage  = models.CharField(choices=ConversationStage.choices, default="new")
    status = models.CharField(choices=ConversationStatus.choices, default="active")

    # Control del bot
    is_bot_active        = models.BooleanField(default=True)
    transferred_to_human = models.BooleanField(default=False)

    # Timestamps
    last_message_at = models.DateTimeField(null=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["customer_phone", "platform"]
```

**Stages del flujo:**

| Stage | Descripción |
|---|---|
| `NEW` | Primera vez que el socio escribe |
| `GREETED` | Bot saludó y solicitó identificación |
| `IDENTIFIED` | DNI validado, socio encontrado en el ERP |
| `VERIFIED` | Socio verificado con dato adicional (fecha nacimiento, etc.) |

### 3.2 Message

Cada mensaje individual de la conversación.

```python
class Message(models.Model):
    conversation = models.ForeignKey(Conversation, related_name="messages")
    role         = models.CharField(choices=MessageRole.choices)  # user/assistant/system
    content      = models.TextField()

    # Metadatos de procesamiento
    tokens_used      = models.IntegerField(default=0)
    response_time_ms = models.IntegerField(default=0)
    response_type    = models.CharField(choices=ResponseType.choices)  # AI / AUTO

    # Identificador de la plataforma (para evitar duplicados)
    platform_message_id = models.CharField(max_length=200, blank=True)
    media_url           = models.URLField(blank=True)

    # Tracking de entrega
    delivery_status    = models.CharField(choices=MessageDeliveryStatus.choices, default="sent")
    delivery_updated_at = models.DateTimeField(null=True)
    delivery_error     = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
```

### 3.3 MessagingSession

Estadísticas de la sesión por plataforma.

```python
class MessagingSession(models.Model):
    platform     = models.CharField(choices=MessagingPlatform.choices)
    session_id   = models.CharField(max_length=200, unique=True)
    phone_number = models.CharField(max_length=20)
    is_connected = models.BooleanField(default=True)
    last_activity = models.DateTimeField(auto_now=True)

    # Contadores
    messages_sent      = models.IntegerField(default=0)
    messages_received  = models.IntegerField(default=0)
    messages_delivered = models.IntegerField(default=0)
    messages_read      = models.IntegerField(default=0)
    messages_failed    = models.IntegerField(default=0)

    @property
    def delivery_rate(self) -> float:
        if self.messages_sent == 0:
            return 0.0
        return (self.messages_delivered / self.messages_sent) * 100

    @property
    def read_rate(self) -> float:
        if self.messages_delivered == 0:
            return 0.0
        return (self.messages_read / self.messages_delivered) * 100
```

### 3.4 AutoResponseRule

Reglas configurables desde admin para responder sin llamar al LLM.

```python
class AutoResponseRule(models.Model):
    name              = models.CharField(max_length=200)
    keywords          = models.TextField(help_text="Palabras clave separadas por coma")
    intent            = models.CharField(choices=UserIntent.choices, blank=True)
    response_template = models.TextField(help_text="Soporta placeholders: {member_name}, {balance}, etc.")
    data_source       = models.CharField(choices=DataSource.choices, default="none")

    # Filtrado por stage
    for_stage  = models.CharField(choices=ConversationStage.choices, blank=True)
    next_stage = models.CharField(choices=ConversationStage.choices, blank=True)

    # Comportamiento con socios no identificados
    requires_member      = models.BooleanField(default=False)
    unidentified_response = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)
    order     = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]
```

### 3.5 KnowledgeDocument y KnowledgeChunk

Base de conocimiento para RAG (preguntas frecuentes, políticas, reglamentos cooperativos).

```python
class KnowledgeDocument(models.Model):
    title    = models.CharField(max_length=300)
    content  = models.TextField()
    category = models.CharField(choices=KnowledgeCategory.choices)
    is_active = models.BooleanField(default=True)

class KnowledgeChunk(models.Model):
    document   = models.ForeignKey(KnowledgeDocument, related_name="chunks")
    content    = models.TextField()
    embedding  = models.JSONField(default=list)  # vector de floats
    chunk_index = models.IntegerField()
    is_indexed  = models.BooleanField(default=False)
```

---

## 4. Choices (Enums)

```python
class ConversationStage(TextChoices):
    NEW        = "new",        "Nuevo"
    GREETED    = "greeted",    "Saludado"
    IDENTIFIED = "identified", "Identificado"
    VERIFIED   = "verified",   "Verificado"

class ConversationStatus(TextChoices):
    ACTIVE      = "active",      "Activo"
    COMPLETED   = "completed",   "Completado"
    ABANDONED   = "abandoned",   "Abandonado"
    TRANSFERRED = "transferred", "Transferido a humano"

class MessageRole(TextChoices):
    USER      = "user",      "Usuario"
    ASSISTANT = "assistant", "Asistente"
    SYSTEM    = "system",    "Sistema"

class MessagingPlatform(TextChoices):
    WHATSAPP = "whatsapp", "WhatsApp"
    TELEGRAM = "telegram", "Telegram"

class ResponseType(TextChoices):
    AI   = "ai",   "IA"
    AUTO = "auto", "Automático"

class MessageDeliveryStatus(TextChoices):
    SENT      = "sent",      "Enviado"
    DELIVERED = "delivered", "Entregado"
    READ      = "read",      "Leído"
    FAILED    = "failed",    "Fallido"

class UserIntent(TextChoices):
    OTHER                = "other",                "Otro"
    GREETING             = "greeting",             "Saludo"
    IDENTIFICATION       = "identification",       "Identificación"
    ACCOUNT_BALANCE      = "account_balance",      "Saldo de cuenta"
    LOAN_STATUS          = "loan_status",          "Estado de préstamo"
    LOAN_INSTALLMENT     = "loan_installment",     "Próxima cuota"
    PAYMENT_HISTORY      = "payment_history",      "Historial de pagos"
    CONTRIBUTION_STATUS  = "contribution_status",  "Estado de aportaciones"
    PAYSLIP_REQUEST      = "payslip_request",      "Boleta de nómina"
    MEMBERSHIP_INFO      = "membership_info",      "Información de membresía"
    CONTACT_ADVISOR      = "contact_advisor",      "Contactar asesor"
    HUMAN_HANDOFF        = "human_handoff",        "Transferir a humano"
    REGISTRATION         = "registration",         "Registro"

class DataSource(TextChoices):
    NONE               = "none",               "Ninguno"
    ACCOUNT_BALANCE    = "account_balance",    "Saldo de ahorro"
    LOAN_INFO          = "loan_info",          "Info de préstamo"
    CONTRIBUTION_INFO  = "contribution_info",  "Aportaciones"
    MEMBER_INFO        = "member_info",        "Info del socio"
    PAYSLIP_INFO       = "payslip_info",       "Boleta de nómina"

class KnowledgeCategory(TextChoices):
    FAQ        = "faq",        "Preguntas frecuentes"
    POLICY     = "policy",     "Políticas"
    GUIDE      = "guide",      "Guías"
    REGULATION = "regulation", "Reglamentos"
    RATES      = "rates",      "Tasas y tarifas"
```

---

## 5. Servicios

### 5.1 ConversationManager (orquestador principal)

Punto de entrada para todo mensaje entrante.

**Responsabilidades:**
- Extraer teléfono, nombre, contenido del payload de la plataforma
- Obtener o crear la `Conversation`
- Verificar si el bot está activo (puede estar transferido a humano)
- Intentar linkear la cuenta del socio por DNI si aún no está identificado
- Detectar intents especiales (deep links: `/start MEMBER_ID`, mensajes de registro)
- Coordinar el flujo: AutoResponder → ActionDispatcher → AgentService
- Enviar la respuesta via el adapter correspondiente
- Guardar ambos mensajes (user + assistant) en la DB

**Flujo interno:**
```
handle_message(platform, webhook_data)
    ↓
MessagingService.process_message() → extrae datos crudos
    ↓
¿Bot activo? Si no → ignorar
    ↓
AccountLinkerService.try_auto_link() → busca DNI en el mensaje
    ↓
AutoResponder.try_keyword_respond() → match exacto de keywords
    ↓ (si no hubo match)
AgentService.detect_intent() → LLM clasifica el intent
    ↓
ActionDispatcher.dispatch(intent, conversation) → ejecuta acción
    ↓
AutoResponder.try_respond(intent) → respuesta plantilla sin LLM
    ↓ (si no hay plantilla)
AgentService.generate_response() → LLM con contexto completo
    ↓
Adapter.send_message() → envía a WhatsApp/Telegram
```

### 5.2 AccountLinkerService

Detecta documentos de identidad (DNI/CE) en los mensajes y linkea la conversación al socio del ERP.

**Patrones a detectar:**
- DNI: exactamente 8 dígitos
- CE (Carnet de Extranjería): 9-12 dígitos
- Puede extenderse a RUC si aplica (11 dígitos)

**Método principal:**
```python
def try_auto_link(self, conversation: Conversation, message_text: str) -> bool:
    """
    Intenta extraer un documento del texto y linkear la conversación al socio.
    Retorna True si se linkeó exitosamente.
    """
```

**Consulta al ERP:**
```python
# Adaptar según el modelo de Member del ERP
member = Member.objects.filter(
    document_number=document_number,
    is_active=True
).select_related("savings_account", "active_loan").first()
```

### 5.3 AutoResponder

Responde sin llamar al LLM usando keywords o intents predefinidos.

**Normalización de texto:**
- Lowercase
- Remover acentos (á→a, é→e, etc.)
- Remover caracteres especiales

**Fuentes de datos para plantillas:**

| Placeholder | Fuente |
|---|---|
| `{member_name}` | `conversation.member.full_name` |
| `{savings_balance}` | `member.savings_account.balance` |
| `{loan_amount}` | `member.active_loan.amount` |
| `{next_installment}` | `member.active_loan.next_installment_date` |
| `{next_installment_amount}` | `member.active_loan.next_installment_amount` |
| `{contribution_status}` | `member.contribution_status` |
| `{membership_since}` | `member.membership_date` |

### 5.4 AgentService (LLM)

Genera respuestas usando OpenRouter.

**detect_intent():** Llama al LLM con un prompt de clasificación que devuelve uno de los `UserIntent`. Respuesta en JSON puro.

**generate_response():** Llama al LLM con:
- System prompt construido por `ContextBuilder`
- Últimos N mensajes de la conversación (ventana de contexto)
- Resultado de la acción ejecutada (si aplica)

**Sanitización anti-injection:**
- Remover secuencias de instrucciones (ej. "ignora las instrucciones anteriores")
- Limitar longitud del mensaje
- Escapar caracteres especiales

### 5.5 ContextBuilder

Construye el system prompt del LLM con el contexto del socio.

**Para socio identificado:**
```
Eres el asistente virtual de {cooperative_name}, una cooperativa de ahorro y crédito.
Eres amable, profesional y siempre orientado a ayudar al socio.

INFORMACIÓN DEL SOCIO:
- Nombre: {member.full_name}
- Número de socio: {member.member_number}
- Miembro desde: {member.membership_date}
- Estado: {member.status}

SITUACIÓN FINANCIERA:
- Saldo de ahorros: S/. {savings_balance}
- Préstamo activo: {loan_details}  (o "Sin préstamos activos")
- Próxima cuota: S/. {installment_amount} vence el {installment_date}
- Aportaciones: {contribution_status}

CONTEXTO ADICIONAL (base de conocimiento):
{rag_context}

INSTRUCCIONES:
- Responde siempre en español, de forma concisa (máx 3 párrafos cortos)
- No inventes información financiera que no te fue provista
- Si el socio pregunta algo fuera de tu alcance, sugiere llamar a la cooperativa
- No compartas información de otros socios
```

**Para socio no identificado:**
```
Eres el asistente virtual de {cooperative_name}.
El socio aún no se ha identificado.
Salúdalo cordialmente y solicítale su número de DNI para poder ayudarlo.
Si pregunta algo general (horarios, tasas, servicios), puedes responderlo con el conocimiento disponible.
```

### 5.6 ActionDispatcher

Mapea intents a clases de acción.

```python
INTENT_ACTION_MAP = {
    UserIntent.ACCOUNT_BALANCE:     AccountBalanceAction,
    UserIntent.LOAN_STATUS:         LoanStatusAction,
    UserIntent.LOAN_INSTALLMENT:    LoanInstallmentAction,
    UserIntent.PAYMENT_HISTORY:     PaymentHistoryAction,
    UserIntent.CONTRIBUTION_STATUS: ContributionStatusAction,
    UserIntent.PAYSLIP_REQUEST:     PayslipAction,
    UserIntent.MEMBERSHIP_INFO:     MembershipInfoAction,
    UserIntent.CONTACT_ADVISOR:     ContactAdvisorAction,
    UserIntent.HUMAN_HANDOFF:       HumanHandoffAction,
}
```

---

## 6. Acciones (Actions)

Cada acción recibe la `Conversation` y retorna un `ActionResult(success, message, data)`.

### AccountBalanceAction
- Consulta el saldo de la cuenta de ahorro del socio
- Si no está identificado: retorna mensaje pidiendo DNI
- Retorna saldo formateado y últimos 3 movimientos

### LoanStatusAction
- Consulta el préstamo activo del socio
- Retorna: monto original, saldo pendiente, cuotas pagadas, cuotas totales, estado
- Si no tiene préstamo: informa que no hay préstamos activos

### LoanInstallmentAction
- Retorna la próxima cuota a pagar: monto, fecha vencimiento, estado (al día / vencida)
- Si está vencida: indica días de mora y monto de mora

### PaymentHistoryAction
- Retorna los últimos N pagos realizados (por defecto 5)
- Formato: fecha, concepto, monto

### ContributionStatusAction
- Estado de aportaciones del mes actual y meses anteriores
- Indica si hay aportaciones pendientes

### PayslipAction
- Si el ERP maneja nóminas: retorna datos de la última boleta
- Si es sistema externo: redirige al canal correcto

### MembershipInfoAction
- Retorna datos de membresía: número de socio, fecha de ingreso, tipo de socio, estado

### ContactAdvisorAction
- Proporciona los datos de contacto del asesor asignado al socio (si aplica)
- O los datos generales de atención de la cooperativa

### HumanHandoffAction
- Marca `conversation.transferred_to_human = True`
- Marca `conversation.is_bot_active = False`
- Notifica al equipo interno (via signal o tarea Celery)

---

## 7. Adapters de plataforma

Ambos adapters implementan la misma interfaz base:

```python
class PlatformAdapter(ABC):
    def send_message(self, phone: str, message: str) -> str: ...
    def send_media(self, phone: str, media_url: str, caption: str) -> str: ...
    def process_message(self, webhook_data: dict) -> dict: ...
    def validate_webhook_signature(self, request) -> bool: ...
```

### WhatsAppAdapter

- **API**: Meta WhatsApp Business Cloud API v18+
- **Auth**: Bearer token (`WHATSAPP_ACCESS_TOKEN`)
- **Signature**: HMAC-SHA256 del body con `WHATSAPP_APP_SECRET`
- **Verificación del webhook**: GET con `hub.challenge` y `WHATSAPP_VERIFY_TOKEN`
- **Estructura de payload entrante**:
  ```json
  {
    "entry": [{
      "changes": [{
        "value": {
          "messages": [{ "from": "51999...", "text": {"body": "..."} }],
          "statuses": [{ "id": "wamid.xxx", "status": "delivered" }]
        }
      }]
    }]
  }
  ```

**Variables de entorno requeridas:**
```
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_VERIFY_TOKEN=
WHATSAPP_APP_SECRET=
```

### TelegramAdapter

- **API**: Telegram Bot API
- **Auth**: Bot token en la URL (`TELEGRAM_BOT_TOKEN`)
- **Signature**: Header `X-Telegram-Bot-API-Secret-Token`
- **Webhook**: POST con updates de Telegram

**Variables de entorno requeridas:**
```
TELEGRAM_BOT_TOKEN=
TELEGRAM_BOT_SECRET_TOKEN=
TELEGRAM_BOT_USERNAME=
```

---

## 8. Celery Tasks

```python
@shared_task(bind=True, max_retries=3)
def process_message(self, webhook_data: dict, platform: str) -> None:
    """Procesa un mensaje entrante de cualquier plataforma."""

@shared_task(bind=True, max_retries=3)
def process_delivery_status(self, webhook_data: dict) -> None:
    """Actualiza el estado de entrega de un mensaje (solo WhatsApp)."""
    # Solo avanza el estado, nunca retrocede:
    # SENT → DELIVERED → READ (READ es estado final positivo)
    # Cualquier estado → FAILED (si Meta reporta error)

@shared_task
def scout_unanswered_conversations() -> None:
    """
    Tarea periódica (cada 5 minutos via Celery Beat).
    Detecta conversaciones donde el bot no respondió al último mensaje del usuario.
    Reintenta la respuesta si el mensaje tiene más de 5 minutos sin respuesta.
    """
```

---

## 9. Endpoints (URLs)

```python
urlpatterns = [
    # Webhooks de plataformas
    path("webhook/whatsapp/", WhatsAppWebhookView.as_view(), name="webhook-whatsapp"),
    path("webhook/telegram/", TelegramWebhookView.as_view(), name="webhook-telegram"),

    # Testing manual (solo en DEBUG)
    path("chat/", ChatTestView.as_view(), name="chat-test"),

    # Dashboard API (opcional)
    path("conversations/", ConversationListView.as_view(), name="conversation-list"),
    path("conversations/<int:pk>/", ConversationDetailView.as_view(), name="conversation-detail"),
]
```

---

## 10. Dashboard (vistas administrativas)

Vistas para el equipo interno de la cooperativa:

| Vista | Descripción |
|---|---|
| `ChatbotDashboardView` | Stats: conversaciones activas, tasa de entrega, socios atendidos |
| `ChatbotConversationsView` | Lista de conversaciones con filtros por estado, stage, fecha |
| `ChatbotConversationDetailView` | Detalle de conversación con hilo de mensajes |
| `TransferQueueView` | Conversaciones transferidas a humano, pendientes de atención |

**Stats del dashboard:**
- Total conversaciones hoy / semana / mes
- Socios únicos atendidos
- Tasa de resolución sin humano (% respondido solo por bot)
- Tasa de entrega de mensajes
- Intent más frecuente
- Tiempo promedio de respuesta del bot

---

## 11. Preguntas pendientes de definición

Antes de iniciar la implementación, responder:

- [ ] **¿Cuál es el modelo de `Member`?** Nombre del app, campos de documento, relaciones con cuenta/préstamo
- [ ] **¿WhatsApp, Telegram, o ambos?**
- [ ] **¿El bot solo consulta o también puede ejecutar operaciones?** (ej: marcar pago, solicitar préstamo)
- [ ] **¿Nóminas es parte del ERP o sistema externo?**
- [ ] **¿Hay tipos de socio?** (Activo, Inactivo, Jubilado, etc.) y cambia el flujo según tipo?
- [ ] **¿Verificación en dos pasos?** (DNI + dato adicional como fecha de nacimiento)
- [ ] **¿Cuál es el modelo de préstamo?** ¿Puede tener varios préstamos activos simultáneos?
- [ ] **¿Qué LLM se usará?** (OpenRouter, OpenAI directo, otro)
- [ ] **¿Hay número de teléfono ya configurado en WhatsApp Business?**

---

## 12. Estructura de archivos sugerida

```
apps/chatbot/
├── __init__.py
├── models.py
├── choices.py
├── views.py
├── urls.py
├── tasks.py
├── serializers.py
├── admin.py
├── factories.py
│
├── adapters/
│   ├── __init__.py
│   ├── base.py
│   ├── whatsapp_adapter.py
│   └── telegram_adapter.py
│
├── services/
│   ├── __init__.py
│   ├── conversation_manager.py
│   ├── messaging_service.py
│   ├── account_linker.py
│   ├── auto_responder.py
│   ├── sales_agent.py
│   ├── context_builder.py
│   ├── data_provider.py
│   ├── rag_service.py
│   └── embedding_service.py
│
├── actions/
│   ├── __init__.py
│   ├── base.py
│   ├── dispatcher.py
│   ├── account.py        # AccountBalanceAction
│   ├── loans.py          # LoanStatusAction, LoanInstallmentAction, PaymentHistoryAction
│   ├── contributions.py  # ContributionStatusAction
│   ├── membership.py     # MembershipInfoAction
│   ├── payslip.py        # PayslipAction
│   └── handoff.py        # HumanHandoffAction, ContactAdvisorAction
│
├── utils/
│   ├── __init__.py
│   └── formatters.py
│
├── management/
│   └── commands/
│       ├── setup_whatsapp_webhook.py
│       ├── setup_telegram_webhook.py
│       ├── configure_chatbot_rules.py
│       └── index_knowledge_base.py
│
├── migrations/
│   └── __init__.py
│
└── tests/
    ├── __init__.py
    ├── test_models.py
    ├── test_views.py
    ├── test_conversation_manager.py
    ├── test_account_linker.py
    ├── test_auto_responder.py
    ├── test_actions.py
    └── test_adapters.py
```

---

## 13. Variables de entorno completas

```env
# WhatsApp Business Cloud API
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_VERIFY_TOKEN=
WHATSAPP_APP_SECRET=

# Telegram Bot API
TELEGRAM_BOT_TOKEN=
TELEGRAM_BOT_SECRET_TOKEN=
TELEGRAM_BOT_USERNAME=

# LLM (OpenRouter)
OPENROUTER_API_KEY=
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=openai/gpt-4o-mini          # modelo de chat
OPENROUTER_VISION_MODEL=google/gemini-flash   # modelo de visión (si aplica)

# Chatbot config
CHATBOT_MAX_CONTEXT_MESSAGES=10    # mensajes de historial que ve el LLM
CHATBOT_BOT_NAME=Asistente Virtual
COOPERATIVE_NAME=                  # nombre de la cooperativa
```

---

## 14. Reglas generales del bot

1. **Nunca inventar datos financieros** — solo mostrar lo que viene de la DB
2. **Respuestas cortas** — máximo 3 párrafos, preferir listas cuando hay múltiples datos
3. **Siempre en español** — tono formal pero amable
4. **Si no identifica al socio en 3 intentos** — ofrecer contacto con asesor humano
5. **No compartir datos de otros socios** bajo ninguna circunstancia
6. **Transferir a humano** ante: quejas graves, operaciones no soportadas, solicitud explícita
7. **Horario de atención** — el bot atiende 24/7, pero aclarar horario para trámites presenciales
8. **Mensajes muy largos del usuario** — resumir y confirmar antes de procesar
9. **Emojis moderados** — uno o dos por mensaje para calidez, no en mensajes de error
10. **Timeout de sesión** — conversación sin actividad por 24h se marca como ABANDONED
