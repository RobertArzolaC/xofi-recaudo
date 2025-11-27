"""Constants and text templates for AI Agent."""

# ==========================================
# TELEGRAM BOT MESSAGES
# ==========================================

HELP_MESSAGE = """
🤖 *Comandos Disponibles*

/start - Iniciar conversación
/help - Ver ayuda
/menu - Ver menú de opciones
/micuenta - Ver mi información
/prestamos - Ver mis préstamos
/saldo - Ver estado de cuenta

💬 *También puedes escribir tus consultas en lenguaje natural:*

Ejemplos:
• "Cuál es mi saldo?"
• "Muéstrame mis préstamos"
• "Detalle del préstamo 123"
• "Necesito ayuda con un pago"
"""

MENU_MESSAGE = """
🤖 *Bienvenido al Asistente Virtual*

Puedo ayudarte con lo siguiente:

📋 *Consultas:*
• Ver mis datos personales
• Consultar estado de cuenta
• Ver mis préstamos
• Detalle de un préstamo específico

🎫 *Soporte:*
• Crear ticket de soporte
• Cargar comprobante de pago

💬 *Ejemplos de preguntas:*
• "Cuál es mi estado de cuenta?"
• "Muéstrame mis préstamos"
• "Detalle del préstamo 123"
• "Necesito ayuda con un pago"
• "Quiero subir un comprobante"

Escribe tu consulta y te ayudaré de inmediato.
"""

AUTHENTICATION_PROMPT = """
🔐 *Autenticación requerida*

Para continuar, por favor proporciona:

1️⃣ Tu número de documento (DNI)
2️⃣ Tu año de nacimiento

*Ejemplo:* 12345678 1990

Esta información será validada en nuestro sistema.
"""

AUTHENTICATION_SUCCESS_TEMPLATE = "Bienvenido {name}!\n\n{menu}"

AUTHENTICATION_ERROR = (
    "No se pudo autenticar. Verifica tu documento y año de nacimiento."
)

GOODBYE_MESSAGE = "Hasta luego! Si necesitas ayuda, aquí estaré. 👋"

UPLOAD_RECEIPT_MESSAGE = """
Para cargar un comprobante de pago, por favor envía la imagen del comprobante.

Asegúrate de que la imagen sea clara y se pueda leer toda la información.
"""

PHOTO_RECEIVED_MESSAGE = """
✅ Imagen recibida correctamente.

📋 Por favor, proporciona la siguiente información:

1️⃣ Número de préstamo (si aplica)
2️⃣ Monto pagado
3️⃣ Fecha del pago
4️⃣ Método de pago (transferencia, efectivo, etc.)

Nuestro equipo verificará el comprobante y actualizará tu cuenta.
"""

ERROR_PROCESSING_MESSAGE = "❌ Lo siento, hubo un error al procesar tu mensaje. Por favor, intenta de nuevo."

UNEXPECTED_ERROR_MESSAGE = (
    "❌ Ocurrió un error inesperado. Por favor, intenta de nuevo más tarde."
)

UNKNOWN_INTENT_RESPONSE = "Lo siento, no entendí tu consulta.\n\n{menu}"

# ==========================================
# CREDIT DETAIL PROMPTS
# ==========================================

CREDIT_DETAIL_REQUEST = (
    "Por favor, indícame el número del préstamo del que deseas ver el detalle. "
    "Ejemplo: préstamo 123"
)

# ==========================================
# TICKET CREATION FLOW
# ==========================================

TICKET_START_MESSAGE = (
    "Voy a ayudarte a crear un ticket de soporte.\n\n"
    "Por favor, describe brevemente el asunto:"
)

TICKET_DESCRIPTION_PROMPT = (
    "Ahora, describe con más detalle tu problema o consulta:"
)

TICKET_SUCCESS_TEMPLATE = (
    "Ticket #{ticket_id} creado exitosamente.\n"
    "Nuestro equipo lo atenderá pronto."
)

TICKET_ERROR = "No se pudo crear el ticket."

TICKET_FLOW_ERROR = "Hubo un error en el proceso."

# ==========================================
# ERROR MESSAGES
# ==========================================

NO_PARTNER_INFO_ERROR = "No se encontró información del socio."

ACCOUNT_STATEMENT_ERROR = "No se pudo obtener el estado de cuenta."

CREDITS_LIST_ERROR = "No se pudo obtener la lista de préstamos."

CREDIT_DETAIL_ERROR = "No se pudo obtener el detalle del préstamo."

NO_CREDITS_MESSAGE = "No tienes créditos registrados."

# ==========================================
# AI SERVICE PROMPTS
# ==========================================

AI_SERVICE_UNAVAILABLE = (
    "Lo siento, el servicio de IA no está disponible en este momento. "
    "Por favor, intenta con comandos más específicos como 'mis préstamos' o 'estado de cuenta'."
)

AI_PROCESSING_ERROR = (
    "Lo siento, hubo un error al procesar tu consulta. "
    "Por favor, intenta reformular tu pregunta."
)

GEMINI_SYSTEM_PROMPT = """
Eres un asistente virtual de una cooperativa de ahorro y crédito en Perú.
Tu objetivo es ayudar a los socios con consultas sobre préstamos, pagos y su cuenta.

Instrucciones:
- Responde siempre en español
- Sé claro, conciso y amable
- Si no tienes información suficiente, solicítala educadamente
- Usa formato markdown para mejor legibilidad
- No inventes información, usa solo los datos proporcionados

Información disponible:
"""

GEMINI_INTENT_ANALYSIS_PROMPT = """
Analiza el siguiente mensaje de un socio de una cooperativa y clasifica su intención.

Intenciones posibles:
- PARTNER_DETAIL: Consultar datos personales
- ACCOUNT_STATEMENT: Ver estado de cuenta o deuda
- LIST_CREDITS: Ver lista de préstamos
- CREDIT_DETAIL: Ver detalle de un préstamo específico
- CREATE_TICKET: Reportar problema o solicitar soporte
- UPLOAD_RECEIPT: Cargar comprobante de pago
- HELP: Solicitar ayuda
- UNKNOWN: No se puede clasificar

Mensaje: "{message}"

Clasifica la intención y proporciona un nivel de confianza entre 0.0 y 1.0.
"""

# ==========================================
# MESSAGE FORMATTING TEMPLATES
# ==========================================

PARTNER_INFO_TEMPLATE = """
📋 *Información del Socio*

👤 *Nombre:* {full_name}
🆔 *Documento:* {document_number}
📱 *Teléfono:* {phone}
📧 *Email:* {email}
"""

ACCOUNT_STATEMENT_TEMPLATE = """
💰 *Estado de Cuenta*

📊 *Resumen General:*
• Créditos totales: {total_credits}
• Créditos activos: {active_credits_count}
• Total desembolsado: S/ {total_disbursed:,.2f}
• Total pagado: S/ {total_payments:,.2f}
• *Saldo pendiente:* S/ {total_outstanding:,.2f}
"""

CREDIT_LIST_HEADER = "📋 *Mis Préstamos*\n\n"

CREDIT_LIST_ITEM_TEMPLATE = """
{index}. *Préstamo #{credit_id}*
   Producto: {product_name}
   Monto: S/ {amount:,.2f}
   Saldo: S/ {outstanding_balance:,.2f}
   Estado: {status}
"""

CREDIT_DETAIL_TEMPLATE = """
💳 *Detalle del Préstamo #{credit_id}*

*Información General:*
• Producto: {product_name}
• Monto: S/ {amount:,.2f}
• Tasa de interés: {interest_rate}%
• Plazo: {term_duration} meses
• Cuota: S/ {payment_amount:,.2f}
• Saldo pendiente: S/ {outstanding_balance:,.2f}

*Resumen de Pagos:*
• Total de cuotas: {total_installments}
• Cuotas pagadas: {paid_installments}
• Cuotas pendientes: {pending_installments}
• Cuotas vencidas: {overdue_installments}
"""

GREETING_TEMPLATE = "Hola {name}! 👋\n\n{menu}"

# ==========================================
# INTENT KEYWORDS
# ==========================================

INTENT_KEYWORDS = {
    "GREETING": [
        "hola",
        "buenos dias",
        "buenas tardes",
        "buenas noches",
        "saludos",
        "que tal",
        "como estas",
    ],
    "GOODBYE": [
        "adios",
        "chao",
        "hasta luego",
        "nos vemos",
        "bye",
        "gracias adios",
    ],
    "HELP": [
        "ayuda",
        "ayudame",
        "que puedes hacer",
        "opciones",
        "menu",
        "comandos",
        "que hago",
    ],
    "PARTNER_DETAIL": [
        "mis datos",
        "mi informacion",
        "datos personales",
        "mi perfil",
        "informacion personal",
    ],
    "ACCOUNT_STATEMENT": [
        "estado de cuenta",
        "mi cuenta",
        "saldo",
        "balance",
        "deuda total",
        "cuanto debo",
        "mi deuda",
    ],
    "LIST_CREDITS": [
        "mis prestamos",
        "mis préstamos",
        "mis creditos",
        "mis créditos",
        "prestamos activos",
        "listar prestamos",
        "ver prestamos",
    ],
    "CREDIT_DETAIL": [
        "detalle de prestamo",
        "detalle de préstamo",
        "detalle de credito",
        "detalle de crédito",
        "detalle de un préstamo",
        "detalle de un crédito",
        "detalle de un prestamo",
        "detalle de un credito",
        "info de prestamo",
        "cuotas",
        "pagos de prestamo",
        "cronograma",
    ],
    "CREATE_TICKET": [
        "ticket",
        "soporte",
        "problema",
        "reclamo",
        "queja",
        "ayuda con",
        "tengo un problema",
    ],
    "UPLOAD_RECEIPT": [
        "comprobante",
        "voucher",
        "recibo de pago",
        "subir comprobante",
        "enviar comprobante",
        "pago realizado",
    ],
}


# ==========================================
# Whapi CONSTANTS
# ==========================================

WHAPI_MESSAGE_TYPE_TEXT = "text"
WHAPI_MESSAGE_TYPE_IMAGE = "image"
WHAPI_MESSAGE_TYPE_BUTTON = "button"
WHAPI_EVENT_TYPE_MESSAGES = "messages"
