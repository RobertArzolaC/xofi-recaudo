import json
import logging
from datetime import date
from io import BytesIO
from typing import Any, Dict, Optional

import google.generativeai as genai
from django.conf import settings
from PIL import Image

from apps.chatbot import constants

logger = logging.getLogger(__name__)


class GeminiPromptFormatter:
    """
    Formatter class for building and formatting prompts for Gemini AI.

    This class handles all the prompt construction logic, including context formatting,
    receipt extraction prompts, and intent analysis prompts.
    """

    def __init__(self):
        """Initialize the prompt formatter."""
        pass

    def build_conversation_prompt(
        self,
        query: str,
        system_prompt: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Build prompt for conversation with context.

        Args:
            query: User's query
            system_prompt: Base system prompt
            context: Optional context data

        Returns:
            Formatted prompt string
        """
        formatted_prompt = system_prompt

        if context:
            context_sections = []

            # Add partner information if available
            partner = context.get("partner")
            if partner:
                partner_info = self.format_partner_context(partner)
                if partner_info:
                    context_sections.append(partner_info)

            # Add account summary if available
            account_summary = context.get("account_summary")
            if account_summary:
                account_info = self.format_account_context(account_summary)
                if account_info:
                    context_sections.append(account_info)

            # Add other context sections if they exist
            for key, value in context.items():
                if key not in ["partner", "account_summary"] and value:
                    formatted_context = self.format_additional_context(
                        key, value
                    )
                    if formatted_context:
                        context_sections.append(formatted_context)

            # Join all context sections
            if context_sections:
                formatted_prompt += "\n\n" + "\n\n".join(context_sections)

        formatted_prompt += f"\n\nConsulta del socio: {query}\n\nRespuesta:"

        return formatted_prompt

    def format_partner_context(self, partner: Dict[str, Any]) -> str:
        """
        Format partner information for the prompt.

        Args:
            partner: Partner data dictionary

        Returns:
            Formatted partner information string
        """
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

    def format_account_context(self, account_summary: Dict[str, Any]) -> str:
        """
        Format account summary information for the prompt.

        Args:
            account_summary: Account summary data dictionary

        Returns:
            Formatted account summary string
        """
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

    def format_additional_context(self, key: str, value: Any) -> str:
        """
        Format additional context information for the prompt.

        Args:
            key: Context key name
            value: Context value

        Returns:
            Formatted context string
        """
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

    def build_receipt_extraction_prompt(self) -> str:
        """
        Build a comprehensive prompt for receipt data extraction from images.

        This prompt is specifically designed for OCR processing of payment
        receipts and vouchers sent via WhatsApp, without any text caption.

        Returns:
            Formatted prompt for Gemini receipt extraction via OCR
        """
        current_date = date.today().strftime("%Y-%m-%d")

        prompt = f"""
Eres un asistente especializado en extracción de datos de comprobantes de pago peruanos.

Tu tarea es extraer información precisa de pagos a partir de la imagen del comprobante proporcionada.

CONTEXTO:
- Los usuarios envían imágenes de comprobantes de pago (vouchers, recibos, capturas de pantalla de transferencias, etc.)
- Analiza la imagen con precisión para extraer montos, fechas e identificadores de documentos
- La imagen puede estar en diferentes formatos y calidades
- Los montos están típicamente en soles peruanos (S/)
- Las fechas pueden estar en varios formatos
- Los identificadores pueden ser números de referencia, números de transacción, códigos de operación, etc.

INSTRUCCIONES DE EXTRACCIÓN:

1. MONTO:
   - Analiza la imagen para encontrar montos de dinero claramente visibles
   - Considera formatos como: "100", "100.50", "S/ 100", "soles 100", etc.
   - Busca en campos como "Monto", "Importe", "Total", "Cantidad", "Amount"
   - Si la imagen muestra múltiples montos, prioriza el monto principal de la transacción
   - Si no encuentras un monto claro, devuelve null

2. FECHA:
   - Analiza la imagen para encontrar fechas de transacción
   - Busca en campos como "Fecha", "Date", "Fecha de operación", "Fecha de transacción", timestamps
   - Convierte cualquier fecha encontrada a formato YYYY-MM-DD
   - La fecha actual es: {current_date}
   - Si no encuentras una fecha clara, devuelve null

3. IDENTIFICADOR DE DOCUMENTO:
   - Busca identificadores únicos en la imagen como:
     * Números de referencia o referencia de operación
     * Números de transacción (transaction ID)
     * Códigos de operación o código de referencia
     * Números de seguimiento (tracking number)
     * Números de comprobante o voucher
     * Números de confirmación
   - Estos identificadores suelen aparecer en campos como "Ref", "Referencia", "Código", "ID", "Transacción", "Operación", "Seguimiento"
   - Si no encuentras un identificador claro, devuelve null

4. CONFIANZA:
   - Evalúa qué tan seguro estás de la extracción (0.0 = nada seguro, 1.0 = completamente seguro)
   - Considera la claridad de la imagen y la presencia de campos identificables

5. NOTAS:
   - Proporciona una breve explicación de cómo realizaste la extracción
   - Menciona cualquier ambigüedad, campos ilegibles o suposiciones realizadas
   - Indica si la imagen es clara o tiene mala calidad

EJEMPLOS DE RESPUESTA:
- Voucher claro con S/ 150.00, fecha 15/01/2024 e ID "REF123456" → amount: 150.0, date: "2024-01-15", document_id: "REF123456", confidence: 0.95
- Captura de pantalla de transferencia con monto, ID pero sin fecha → amount: 200.0, date: null, document_id: "TRX789012", confidence: 0.8
- Imagen muy borrosa o ilegible → amount: null, date: null, document_id: null, confidence: 0.1

Responde únicamente con el JSON solicitado.
"""
        return prompt

    def build_intent_analysis_prompt(
        self, message: str, base_prompt: str
    ) -> str:
        """
        Build prompt for intent analysis.

        Args:
            message: User message to analyze
            base_prompt: Base prompt template

        Returns:
            Formatted intent analysis prompt
        """
        return base_prompt.format(message=message)

    def get_receipt_extraction_schema(self) -> Dict[str, Any]:
        """
        Get the JSON schema for receipt extraction response.

        Returns:
            JSON schema dictionary for Gemini response validation
        """
        return {
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
                "document_id": {
                    "type": "string",
                    "description": "Identificador del documento (número de referencia, código de transacción, etc.)",
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
            "required": ["amount", "date", "confidence", "extraction_method"],
        }

    def get_intent_analysis_schema(self) -> Dict[str, Any]:
        """
        Get the JSON schema for intent analysis response.

        Returns:
            JSON schema dictionary for intent analysis response validation
        """
        return {
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
        }

    def format_generation_config(
        self, schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create generation configuration for Gemini API.

        Args:
            schema: JSON schema for response validation

        Returns:
            Generation configuration dictionary
        """
        return {
            "response_mime_type": "application/json",
            "response_schema": schema,
        }


class GeminiService:
    """
    Google Gemini AI service for chatbot.
    Handles complex queries and intent analysis using Gemini AI models.
    """

    def __init__(self):
        """Initialize Gemini service with API configuration."""
        self.gemini_api_key = getattr(settings, "GOOGLE_GEMINI_API_KEY", "")
        self.model_name = getattr(
            settings, "GEMINI_MODEL_NAME", "gemini-2.0-flash-lite"
        )

        # Initialize prompt formatter
        self.formatter = GeminiPromptFormatter()

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
        return self.formatter.build_conversation_prompt(
            query, constants.GEMINI_SYSTEM_PROMPT, context
        )

    def _validate_image_bytes(self, image_bytes: bytes) -> bool:
        """
        Validate if image bytes are in a supported format.

        Args:
            image_bytes: Raw image bytes to validate

        Returns:
            True if image is valid and supported, False otherwise
        """
        if not image_bytes or len(image_bytes) == 0:
            return False

        # Check minimum size (avoid tiny/corrupted images)
        if len(image_bytes) < 100:  # Very small, likely corrupted
            return False

        # Check maximum size (avoid huge files)
        max_size_mb = 10  # 10MB limit
        if len(image_bytes) > max_size_mb * 1024 * 1024:
            logger.warning(
                f"Image too large: {len(image_bytes) / (1024 * 1024):.1f}MB"
            )
            return False

        return True

    def _prepare_image_for_gemini(
        self, image_bytes: bytes
    ) -> Optional[Image.Image]:
        """
        Prepare image data for Gemini processing.

        Args:
            image_bytes: Raw image bytes

        Returns:
            PIL Image object ready for Gemini, or None if processing fails
        """
        # Validate image bytes first
        if not self._validate_image_bytes(image_bytes):
            logger.warning("Image bytes validation failed")
            return None

        try:
            # Create PIL Image from bytes
            image = Image.open(BytesIO(image_bytes))

            # Verify image can be loaded
            image.verify()

            # Reopen for processing (verify() closes the image)
            image = Image.open(BytesIO(image_bytes))

            # Convert to RGB if necessary (RGBA, CMYK, etc.)
            if image.mode != "RGB":
                logger.info(f"Converting image from {image.mode} to RGB")
                image = image.convert("RGB")

            # Resize image if too large (Gemini has size limits)
            max_size = (2048, 2048)  # Reasonable limit for OCR
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                original_size = image.size
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
                logger.info(
                    f"Image resized from {original_size} to {image.size} for Gemini processing"
                )

            logger.info(
                f"Image prepared for Gemini: {image.size}, mode: {image.mode}"
            )
            return image

        except Exception as e:
            logger.error(f"Error preparing image for Gemini: {e}")
            return None

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

        prompt = self.formatter.build_intent_analysis_prompt(
            message, constants.GEMINI_INTENT_ANALYSIS_PROMPT
        )

        try:
            # Configure generation to return JSON
            schema = self.formatter.get_intent_analysis_schema()
            generation_config = self.formatter.format_generation_config(schema)

            response = self.gemini_model.generate_content(
                prompt, generation_config=generation_config
            )

            result = json.loads(response.text)
            return result
        except Exception as e:
            logger.exception(f"Error analyzing intent with AI: {e}")
            return {"intent": "UNKNOWN", "confidence": 0, "entities": {}}

    def extract_receipt_data(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Extract payment receipt data from an image using Gemini AI OCR.

        This method performs OCR on receipt/voucher images and extracts
        structured payment data from the visual content.

        Args:
            image_bytes: Image data (JPEG, PNG, etc.) for OCR processing

        Returns:
            Dict with extracted data containing:
                - amount (float): Extracted payment amount
                - date (str): Extracted date in YYYY-MM-DD format
                - document_id (str): Extracted document identifier (reference number, transaction code, etc.)
                - confidence (float): Confidence score 0.0-1.0
                - extraction_method (str): Method used for extraction
                - notes (str): Additional notes about the extraction

        Examples:
            # Image processing from WHAPI
            with open('receipt.jpg', 'rb') as f:
                image_data = f.read()
            result = service.extract_receipt_data(image_data)
        """
        if not self.gemini_model:
            logger.warning(
                "Gemini model not available, falling back to default extraction"
            )
            return {
                "amount": "1.00",
                "date": date.today().isoformat(),
                "document_id": "",
                "confidence": 0.0,
                "extraction_method": "fallback_error",
                "notes": "Gemini no disponible",
            }

        # Build the receipt extraction prompt for image OCR processing
        prompt = self.formatter.build_receipt_extraction_prompt()

        try:
            # Configure generation to return structured JSON
            schema = self.formatter.get_receipt_extraction_schema()
            generation_config = self.formatter.format_generation_config(schema)

            # Prepare image for Gemini
            image = self._prepare_image_for_gemini(image_bytes)
            if not image:
                logger.error("Failed to prepare image for Gemini processing")
                return {
                    "amount": "1.00",
                    "date": date.today().isoformat(),
                    "document_id": "",
                    "confidence": 0.0,
                    "extraction_method": "image_preparation_error",
                    "notes": "No se pudo procesar la imagen",
                }

            # Prepare content for Gemini with prompt and image
            content_parts = [prompt, image]

            logger.info("Image prepared for Gemini OCR processing")

            # Generate content with image
            response = self.gemini_model.generate_content(
                content_parts, generation_config=generation_config
            )

            result = json.loads(response.text)

            # Add metadata - always image-based extraction
            result["extraction_method"] = "gemini_ai_ocr"
            result["notes"] = response.text[:500]

            logger.info(
                f"Gemini extracted receipt data via OCR: "
                f"amount={result.get('amount')}, date={result.get('date')}, "
                f"document_id={result.get('document_id')}, "
                f"confidence={result.get('confidence')}"
            )

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing Gemini JSON response: {e}")
            return {
                "amount": "1.00",
                "date": date.today().isoformat(),
                "document_id": "",
                "confidence": 0.0,
                "extraction_method": "json_parse_error",
                "notes": f"JSON Parse Error: {str(e)}",
            }
        except Exception as e:
            logger.exception(f"Error extracting receipt data with Gemini: {e}")
            return {
                "amount": "1.00",
                "date": date.today().isoformat(),
                "document_id": "",
                "confidence": 0.0,
                "extraction_method": "ocr_processing_error",
                "notes": f"Error: {str(e)}",
            }
