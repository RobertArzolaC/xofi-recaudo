"""Tool declarations and registry for the XoFi AI Agent."""
import logging
from typing import Any

from apps.chatbot.services.partner_api import PartnerAPIService

logger = logging.getLogger(__name__)


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

    def __init__(
        self, 
        partner_id: int = None, 
        partner_document: str = None, 
        api_service: PartnerAPIService = None,
        authenticated: bool = False
    ):
        self.partner_id = partner_id
        self.partner_document = partner_document
        self.api_service = api_service
        self.authenticated = authenticated
        self._executors = {
            "get_partner_detail": self._exec_partner_detail,
            "get_account_statement": self._exec_account_statement,
            "get_total_contributions": self._exec_total_contributions,
            "get_credits_list": self._exec_credits_list,
            "get_credit_detail": self._exec_credit_detail,
            "get_credit_schedule": self._exec_credit_schedule,
            "request_support_ticket": self._exec_request_support_ticket,
            "create_support_ticket": self._exec_create_support_ticket,
            "request_payment_receipt_upload": self._exec_request_payment_receipt_upload,
            "request_prospect_registration": self._exec_request_prospect_registration,
            "logout_partner": self._exec_logout_partner,
        }

    def get_tool_declarations(self) -> list[dict]:
        """Generate tool declarations dynamically to inject context like associated products."""
        product_names = []
        if self.authenticated and self.partner_id:
            # Fetch associated products to use as enum in tool parameters
            credits_data = self.api_service.get_credits_list(self.partner_id, status="ACTIVE")
            if credits_data and "credits" in credits_data:
                product_names = list(set([c["product_name"] for c in credits_data["credits"]]))

        # Define product_name parameter schema based on available products
        product_param = {
            "type": "string",
            "description": "Nombre del producto del crédito a consultar.",
        }
        if product_names:
            product_param["enum"] = product_names

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "request_prospect_registration",
                    "description": "Obtener el acceso al formulario web para que un no socio pueda registrarse como prospecto para ser evaluado.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                }
            },
        ]

        # Only include member-specific tools if authenticated
        if self.authenticated:
            tools.extend([
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
                        "name": "get_total_contributions",
                        "description": "Obtener el detalle de los aportes totales acumulados del socio.",
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
                        "description": "Obtener la lista de préstamos/créditos del socio con sus montos, saldos y estados.",
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
                        "description": "Obtener el detalle de un préstamo/crédito específico.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "product_name": product_param,
                            },
                            "required": ["product_name"],
                        },
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "get_credit_schedule",
                        "description": "Obtener el cronograma de pagos detallado de un préstamo. Muestra cuotas vencidas y próximas cuotas.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "product_name": product_param,
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
                {
                    "type": "function",
                    "function": {
                        "name": "request_payment_receipt_upload",
                        "description": "Solicitar al socio que envíe la foto de su comprobante de pago para registrar un pago. Usar cuando el socio quiere subir un comprobante, registrar un pago realizado o enviar un voucher de pago.",
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
                        "name": "logout_partner",
                        "description": "Cerrar la sesión actual del socio. Usar cuando el socio indique explícitamente que desea salir, terminar la sesión o cerrar su cuenta del chat.",
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": [],
                        },
                    }
                },
            ])

        return tools

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

    def _exec_request_prospect_registration(self) -> dict:
        return {"status": "prospect_form_requested"}

    def _exec_request_support_ticket(self) -> dict:
        return {"status": "form_requested"}

    def _exec_partner_detail(self) -> dict:
        if not self.partner_id:
            return {"error": "Acceso denegado: debe estar autenticado."}
        data = self.api_service.get_partner_detail(self.partner_id)
        if not data:
            return {"error": "No se encontró información del socio."}
        return data

    def _exec_account_statement(self) -> dict:
        if not self.partner_id:
            return {"error": "Acceso denegado: debe estar autenticado."}
        data = self.api_service.get_account_statement(self.partner_id)
        if not data:
            return {"error": "No se pudo obtener el estado de cuenta."}
        return data

    def _exec_total_contributions(self) -> dict:
        if not self.partner_id:
            return {"error": "Acceso denegado: debe estar autenticado."}
        data = self.api_service.get_total_contributions(self.partner_id)
        if not data:
            return {"error": "No se pudo obtener el detalle de aportes."}
        return data

    def _exec_credits_list(self, status: str = None) -> dict:
        if not self.partner_id:
            return {"error": "Acceso denegado: debe estar autenticado."}
        data = self.api_service.get_credits_list(self.partner_id, status=status)
        if not data:
            return {"error": "No se pudo obtener la lista de préstamos."}
        return data

    def _exec_credit_detail(self, product_name: str) -> dict:
        if not self.partner_id:
            return {"error": "Acceso denegado: debe estar autenticado."}
        data = self.api_service.get_credit_detail(self.partner_id, product_name)
        if not data:
            return {"error": f"No se encontró el préstamo '{product_name}'."}
        return data

    def _exec_credit_schedule(self, product_name: str) -> dict:
        if not self.partner_id:
            return {"error": "Acceso denegado: debe estar autenticado."}
        data = self.api_service.get_credit_schedule(self.partner_id, product_name)
        if not data:
            return {"error": f"No se pudo obtener el cronograma del préstamo '{product_name}'."}
        return data

    def _exec_create_support_ticket(self, subject: str, description: str) -> dict:
        if not self.partner_document:
            return {"error": "Acceso denegado: debe estar autenticado."}
        data = self.api_service.create_support_ticket(
            self.partner_document, subject, description
        )
        if not data:
            return {"error": "No se pudo crear el ticket de soporte."}
        return data

    def _exec_request_payment_receipt_upload(self) -> dict:
        return {"status": "payment_receipt_upload_requested"}

    def _exec_logout_partner(self) -> dict:
        return {"status": "logout_requested"}
