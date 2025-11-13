import json
import logging
from datetime import date
from typing import Any, Dict, Optional

import google.generativeai as genai
from django.conf import settings

from apps.chatbot import constants

logger = logging.getLogger(__name__)


class GeminiService:
    """
    Google Gemini AI service for chatbot.
    Handles complex queries and intent analysis using Gemini AI models.
    """

    def __init__(self):
        """Initialize Gemini service with API configuration."""
        self.gemini_api_key = getattr(settings, "GOOGLE_GEMINI_API_KEY", "")
        self.model_name = getattr(settings, "GEMINI_MODEL_NAME", "gemini-pro")

        # Initialize Gemini client
        self._init_gemini_client()

    def _init_gemini_client(self):
        """Initialize Google Gemini client."""
        try:
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_model = genai.GenerativeModel(self.model_name)
            logger.info(
                f"Gemini client initialized with model {self.model_name}"
            )
        except ImportError:
            logger.warning(
                "google-generativeai not installed. AI features disabled."
            )
            self.gemini_model = None
        except Exception as e:
            logger.error(f"Error initializing Gemini client: {e}")
            self.gemini_model = None

    def _build_prompt(
        self, query: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build prompt for AI model with context."""
        system_prompt = constants.GEMINI_SYSTEM_PROMPT

        if context:
            context_sections = []

            # Add partner information if available
            partner = context.get("partner")
            if partner:
                partner_info = self._format_partner_context(partner)
                if partner_info:
                    context_sections.append(partner_info)

            # Add account summary if available
            account_summary = context.get("account_summary")
            if account_summary:
                account_info = self._format_account_context(account_summary)
                if account_info:
                    context_sections.append(account_info)

            # Add other context sections if they exist
            for key, value in context.items():
                if key not in ["partner", "account_summary"] and value:
                    formatted_context = self._format_additional_context(
                        key, value
                    )
                    if formatted_context:
                        context_sections.append(formatted_context)

            # Join all context sections
            if context_sections:
                system_prompt += "\n\n" + "\n\n".join(context_sections)

        system_prompt += f"\n\nConsulta del socio: {query}\n\nRespuesta:"

        return system_prompt

    def _format_partner_context(self, partner: Dict[str, Any]) -> str:
        """Format partner information for the prompt."""
        if not partner:
            return ""

        partner_lines = ["Socio:"]

        # Add available partner fields
        fields_mapping = {
            "full_name": "Nombre",
            "document_number": "Documento",
            "phone": "Teléfono",
            "email": "Email",
        }

        for field, label in fields_mapping.items():
            value = partner.get(field)
            if value and value != "N/A":
                partner_lines.append(f"- {label}: {value}")

        return "\n".join(partner_lines) if len(partner_lines) > 1 else ""

    def _format_account_context(self, account_summary: Dict[str, Any]) -> str:
        """Format account summary information for the prompt."""
        if not account_summary:
            return ""

        summary_lines = ["Resumen de cuenta:"]

        # Format active credits count
        active_credits = account_summary.get("active_credits_count", 0)
        summary_lines.append(f"- Créditos activos: {active_credits}")

        # Format total outstanding with proper currency formatting
        total_outstanding = account_summary.get("total_outstanding", 0)
        if isinstance(total_outstanding, (int, float)):
            formatted_amount = f"S/ {total_outstanding:,.2f}"
        else:
            formatted_amount = f"S/ {total_outstanding}"
        summary_lines.append(f"- Saldo pendiente: {formatted_amount}")

        # Add other relevant account fields
        additional_fields = {
            "next_payment_date": "Próximo pago",
            "last_payment_date": "Último pago",
            "total_credits": "Total de créditos",
        }

        for field, label in additional_fields.items():
            value = account_summary.get(field)
            if value:
                summary_lines.append(f"- {label}: {value}")

        return "\n".join(summary_lines)

    def _format_additional_context(self, key: str, value: Any) -> str:
        """Format additional context information for the prompt."""
        if not value:
            return ""

        # Handle different types of additional context
        if isinstance(value, dict):
            if not value:
                return ""

            context_lines = [f"{key.replace('_', ' ').title()}:"]
            for sub_key, sub_value in value.items():
                if sub_value:
                    formatted_key = sub_key.replace("_", " ").title()
                    context_lines.append(f"- {formatted_key}: {sub_value}")

            return "\n".join(context_lines) if len(context_lines) > 1 else ""

        elif isinstance(value, list):
            if not value:
                return ""

            context_lines = [f"{key.replace('_', ' ').title()}:"]
            for item in value[
                :5
            ]:  # Limit to first 5 items to avoid token overflow
                context_lines.append(f"- {item}")

            if len(value) > 5:
                context_lines.append(f"- ... y {len(value) - 5} más")

            return "\n".join(context_lines)

        else:
            # Handle simple values
            formatted_key = key.replace("_", " ").title()
            return f"{formatted_key}: {value}"

    def analyze_intent_with_ai(self, message: str) -> Dict[str, Any]:
        """
        Use AI to analyze message intent when rule-based detection fails.

        Args:
            message: User's message

        Returns:
            Dict with intent classification and extracted entities
        """
        if not self.gemini_model:
            return {"intent": "UNKNOWN", "confidence": 0, "entities": {}}

        prompt = constants.GEMINI_INTENT_ANALYSIS_PROMPT.format(message=message)

        try:
            # Configure generation to return JSON
            generation_config = {
                "response_mime_type": "application/json",
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "intent": {
                            "type": "string",
                            "enum": [
                                "GREETING",
                                "AUTHENTICATION",
                                "PARTNER_DETAIL",
                                "ACCOUNT_STATEMENT",
                                "LIST_CREDITS",
                                "CREDIT_DETAIL",
                                "CREATE_TICKET",
                                "UPLOAD_RECEIPT",
                                "HELP",
                                "GOODBYE",
                                "UNKNOWN",
                            ],
                        },
                        "confidence": {"type": "number"},
                        "entities": {
                            "type": "object",
                            "properties": {
                                "loan_id": {"type": "string"},
                                "amount": {"type": "string"},
                                "date": {"type": "string"},
                                "ticket_subject": {"type": "string"},
                            },
                        },
                    },
                    "required": ["intent", "confidence", "entities"],
                },
            }

            response = self.gemini_model.generate_content(
                prompt, generation_config=generation_config
            )

            result = json.loads(response.text)
            return result
        except Exception as e:
            logger.exception(f"Error analyzing intent with AI: {e}")
            return {"intent": "UNKNOWN", "confidence": 0, "entities": {}}

    def extract_receipt_data(
        self, caption: str, image_bytes: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """
        Extract payment receipt data using Gemini AI.

        Args:
            caption: User-provided caption or description
            image_bytes: Optional image data for OCR processing

        Returns:
            Dict with extracted data: amount, date, confidence, etc.
        """
        if not self.gemini_model:
            logger.warning(
                "Gemini model not available, falling back to default extraction"
            )
            return {
                "amount": None,
                "date": None,
                "confidence": 0.0,
                "extraction_method": "fallback",
                "raw_response": "Gemini no disponible",
            }

        # Build the receipt extraction prompt
        prompt = self._build_receipt_extraction_prompt(caption)

        try:
            # Configure generation to return structured JSON
            generation_config = {
                "response_mime_type": "application/json",
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "amount": {
                            "type": "number",
                            "description": "Monto extraído del comprobante en formato decimal",
                        },
                        "date": {
                            "type": "string",
                            "description": "Fecha extraída en formato YYYY-MM-DD",
                        },
                        "confidence": {
                            "type": "number",
                            "description": "Nivel de confianza de la extracción (0.0 a 1.0)",
                        },
                        "extraction_method": {
                            "type": "string",
                            "description": "Método utilizado para la extracción",
                        },
                        "notes": {
                            "type": "string",
                            "description": "Notas adicionales sobre la extracción",
                        },
                    },
                    "required": [
                        "amount",
                        "date",
                        "confidence",
                        "extraction_method",
                    ],
                },
            }

            # Generate content with or without image
            if image_bytes:
                # TODO: Implement image processing when available
                # For now, process only the caption
                response = self.gemini_model.generate_content(
                    prompt, generation_config=generation_config
                )
            else:
                response = self.gemini_model.generate_content(
                    prompt, generation_config=generation_config
                )

            result = json.loads(response.text)

            # Add metadata
            result["extraction_method"] = "gemini_ai"
            result["raw_response"] = response.text[
                :500
            ]  # Store first 500 chars for debugging

            logger.info(
                f"Gemini extracted receipt data: amount={result.get('amount')}, "
                f"date={result.get('date')}, confidence={result.get('confidence')}"
            )

            return result

        except Exception as e:
            logger.exception(f"Error extracting receipt data with Gemini: {e}")
            return {
                "amount": None,
                "date": None,
                "confidence": 0.0,
                "extraction_method": "error",
                "raw_response": f"Error: {str(e)}",
            }

    def _build_receipt_extraction_prompt(self, caption: str) -> str:
        """
        Build a comprehensive prompt for receipt data extraction.

        Args:
            caption: User-provided caption or description

        Returns:
            Formatted prompt for Gemini
        """
        prompt = f"""
Eres un asistente especializado en extracción de datos de comprobantes de pago peruanos.

Tu tarea es extraer información precisa de pagos a partir de la descripción proporcionada por el usuario.

CONTEXTO:
- Los usuarios envían descripciones de sus pagos realizados
- Necesitas extraer el monto y la fecha del pago
- Los montos están típicamente en soles peruanos (S/)
- Las fechas pueden estar en varios formatos

DESCRIPCIÓN DEL USUARIO:
"{caption}"

INSTRUCCIONES DE EXTRACCIÓN:

1. MONTO:
   - Busca números que representen montos de dinero
   - Considera formatos como: "100", "100.50", "S/ 100", "soles 100", etc.
   - Si hay múltiples números, usa el contexto para identificar el monto del pago
   - Si no encuentras un monto claro, devuelve null

2. FECHA:
   - Busca fechas en formatos como: "2024-01-15", "15/01/2024", "15-01-2024", "ayer", "hoy"
   - Convierte fechas relativas a formato YYYY-MM-DD (usa la fecha actual como referencia: {date.today().strftime("%Y-%m-%d")})
   - Si no encuentras una fecha clara, devuelve null

3. CONFIANZA:
   - Evalúa qué tan seguro estás de la extracción (0.0 = nada seguro, 1.0 = completamente seguro)
   - Considera la claridad de la descripción y la presencia de palabras clave

4. NOTAS:
   - Proporciona una breve explicación de cómo realizaste la extracción
   - Menciona cualquier ambigüedad o suposición realizada

EJEMPLOS:
- "Pagué 150 soles el 15 de enero" → amount: 150.0, date: "2024-01-15"
- "Deposité S/ 75.50 ayer" → amount: 75.5, date: "[fecha de ayer]"
- "Transferencia de 200" → amount: 200.0, date: null (sin fecha clara)

Responde únicamente con el JSON solicitado.
"""
        return prompt
