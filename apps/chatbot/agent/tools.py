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
            "description": "Obtener el detalle completo de un préstamo/crédito específico: producto, monto, tasa de interés, plazo, cuota mensual, saldo pendiente, cuotas pagadas, pendientes y vencidas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "credit_id": {
                        "type": "integer",
                        "description": "ID numérico del préstamo/crédito a consultar.",
                    },
                },
                "required": ["credit_id"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_support_ticket",
            "description": "Crear un ticket de soporte para el socio. Usar cuando el socio reporta un problema, queja, reclamo o necesita asistencia especializada que no se puede resolver con las consultas disponibles.",
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
            "create_support_ticket": self._exec_create_support_ticket,
        }

    def execute(self, tool_name: str, args: dict) -> dict[str, Any]:
        """Dispatch a tool call to its executor. Returns the result dict."""
        executor = self._executors.get(tool_name)
        if not executor:
            logger.warning("Unknown tool requested: %s", tool_name)
            return {"error": f"Herramienta desconocida: {tool_name}"}
        try:
            return executor(**args)
        except Exception as exc:
            logger.error("Error executing tool %s: %s", tool_name, exc, exc_info=True)
            return {"error": "No se pudo completar la consulta. Intenta de nuevo."}

    # ------------------------------------------------------------------
    # Executors
    # ------------------------------------------------------------------

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

    def _exec_credit_detail(self, credit_id: int) -> dict:
        data = self.api_service.get_credit_detail(self.partner_id, credit_id)
        if not data:
            return {"error": f"No se encontró el préstamo #{credit_id}."}
        return data

    def _exec_create_support_ticket(self, subject: str, description: str) -> dict:
        data = self.api_service.create_support_ticket(
            self.partner_document, subject, description
        )
        if not data:
            return {"error": "No se pudo crear el ticket de soporte."}
        return data
