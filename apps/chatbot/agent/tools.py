"""Tool declarations and registry for the XoFi AI Agent."""
import logging
from typing import Any

from apps.chatbot.services.partner_api import PartnerAPIService

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tool declarations (OpenAI-compatible function calling format)
# ---------------------------------------------------------------------------

TOOL_DECLARATIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_partner_detail",
            "description": "Obtener los datos personales del socio autenticado: nombre completo, número de documento, teléfono y email.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_account_statement",
            "description": "Obtener el estado de cuenta del socio: resumen de créditos, montos desembolsados, total de pagos realizados y saldo pendiente total.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_credits_list",
            "description": "Obtener la lista de préstamos/créditos del socio con sus montos, saldos y estados. Útil para identificar el ID de un crédito específico.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Filtrar por estado: 'active' (activos), 'closed' (cancelados), 'overdue' (en mora). Omitir para ver todos.",
                    },
                },
                "required": [],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_credit_detail",
            "description": "Obtener el detalle de un préstamo/crédito específico usando el nombre del producto asociado (ej. 'CRÉDITO PERSONAL'). Devuelve monto, saldo, cuota y estado.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "Nombre del producto del crédito a consultar (ej. 'CRÉDITO PERSONAL').",
                    },
                },
                "required": ["product_name"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_credit_schedule",
            "description": "Obtener el cronograma de pagos detallado de un préstamo usando el nombre del producto. Muestra cuotas vencidas y próximas cuotas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "Nombre del producto del crédito a consultar.",
                    },
                },
                "required": ["product_name"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "request_support_ticket",
            "description": "Usar cuando el socio solicita crear un ticket de soporte, ayuda, queja o reclamo. NO pide parámetros, solo envía el formulario.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_support_ticket",
            "description": "Crear un ticket de soporte en el sistema. Usar ÚNICAMENTE cuando el socio ya ha enviado los datos estructurados del formulario (asunto y descripción).",
            "parameters": {
                "type": "object",
                "properties": {
                    "subject": {
                        "type": "string",
                        "description": "Asunto breve del ticket (máximo 100 caracteres).",
                    },
                    "description": {
                        "type": "string",
                        "description": "Descripción detallada del problema o consulta.",
                    },
                },
                "required": ["subject", "description"],
            },
        }
    },
]


# ---------------------------------------------------------------------------
# Tool Registry
# ---------------------------------------------------------------------------

class ToolRegistry:
    """
    Binds tool declarations to their PartnerAPIService executors.

    Each executor receives the tool arguments from the AI model and returns a
    raw data dict. The AI model generates the natural language response from
    that data.
    """

    def __init__(self, partner_id: int, partner_document: str, api_service: PartnerAPIService):
        self.partner_id = partner_id
        self.partner_document = partner_document
        self.api_service = api_service
        self._executors = {
            "get_partner_detail": self._exec_partner_detail,
            "get_account_statement": self._exec_account_statement,
            "get_credits_list": self._exec_credits_list,
            "get_credit_detail": self._exec_credit_detail,
            "get_credit_schedule": self._exec_credit_schedule,
            "request_support_ticket": self._exec_request_support_ticket,
            "create_support_ticket": self._exec_create_support_ticket,
        }

    def execute(self, tool_name: str, args: dict) -> dict[str, Any]:
        """Dispatch a tool call to its executor. Returns the result dict."""
        import inspect

        executor = self._executors.get(tool_name)
        if not executor:
            logger.warning("Unknown tool requested: %s", tool_name)
            return {"error": f"Herramienta desconocida: {tool_name}"}

        # Some models might nest arguments under '@arguments' or similar keys
        actual_args = args
        if isinstance(args, dict):
            if "@arguments" in args:
                actual_args = args["@arguments"]
            elif "arguments" in args and isinstance(args["arguments"], dict):
                actual_args = args["arguments"]

        try:
            # Get the expected parameters for the executor
            sig = inspect.signature(executor)
            valid_params = sig.parameters.keys()

            # Filter out arguments that are not expected by the executor
            # This handles cases where the model hallucinations keys like '' or '@type'
            filtered_args = {
                k: v for k, v in actual_args.items() 
                if k in valid_params and k != ""
            }

            return executor(**filtered_args)
        except Exception as exc:
            logger.error("Error executing tool %s: %s", tool_name, exc, exc_info=True)
            return {"error": "No se pudo completar la consulta. Intenta de nuevo."}

    # ------------------------------------------------------------------
    # Executors
    # ------------------------------------------------------------------

    def _exec_request_support_ticket(self) -> dict:
        return {"status": "form_requested"}

    def _exec_partner_detail(self) -> dict:
        data = self.api_service.get_partner_detail(self.partner_id)
        if not data:
            return {"error": "No se encontró información del socio."}
        return data

    def _exec_account_statement(self) -> dict:
        data = self.api_service.get_account_statement(self.partner_id)
        if not data:
            return {"error": "No se pudo obtener el estado de cuenta."}
        return data

    def _exec_credits_list(self, status: str = None) -> dict:
        data = self.api_service.get_credits_list(self.partner_id, status=status)
        if not data:
            return {"error": "No se pudo obtener la lista de préstamos."}
        return data

    def _exec_credit_detail(self, product_name: str) -> dict:
        data = self.api_service.get_credit_detail(self.partner_id, product_name)
        if not data:
            return {"error": f"No se encontró el préstamo '{product_name}'."}
        return data

    def _exec_credit_schedule(self, product_name: str) -> dict:
        data = self.api_service.get_credit_schedule(self.partner_id, product_name)
        if not data:
            return {"error": f"No se pudo obtener el cronograma del préstamo '{product_name}'."}
        return data

    def _exec_create_support_ticket(self, subject: str, description: str) -> dict:
        data = self.api_service.create_support_ticket(
            self.partner_document, subject, description
        )
        if not data:
            return {"error": "No se pudo crear el ticket de soporte."}
        return data
