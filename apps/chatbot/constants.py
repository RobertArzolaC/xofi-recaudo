"""Constants and text templates for AI Agent."""

# ==========================================
# TELEGRAM BOT MESSAGES
# ==========================================

WELCOME_MESSAGE = """
🤖 *Bienvenido al Asistente Virtual de XoFi*

Soy tu asistente virtual y estoy aquí para ayudarte con:

📋 Consultas sobre tu cuenta y préstamos
💰 Estado de cuenta y pagos
🎫 Soporte técnico
📄 Carga de comprobantes

Para comenzar, necesito autenticarte.

Por favor, envía tu *número de documento* y *año de nacimiento* separados por un espacio.

*Ejemplo:* 12345678 1990
"""

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

AI_PROCESSING_ERROR = (
    "Lo siento, hubo un error al procesar tu consulta. "
    "Por favor, intenta reformular tu pregunta."
)

# ==========================================
# Whapi CONSTANTS
# ==========================================

MESSAGE_TYPE_TEXT = "text"
MESSAGE_TYPE_IMAGE = "image"
MESSAGE_TYPE_BUTTON = "button"
MESSAGE_TYPE_INTERACTIVE = "interactive"
EVENT_TYPE_MESSAGES = "messages"
