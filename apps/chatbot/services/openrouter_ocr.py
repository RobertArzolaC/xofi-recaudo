import base64
import json
import logging
from datetime import date
from typing import Any, Dict

from django.conf import settings

from apps.core.clients.openrouter import OpenRouterClient

logger = logging.getLogger(__name__)


class OpenRouterOCRService:
    """
    Service for extracting payment data from images using OpenRouter (multimodal models).
    """

    def __init__(self):
        """Initialize with OpenRouter client."""
        self.client = OpenRouterClient()
        # Default model for vision tasks
        self.model = getattr(
            settings, "OPENROUTER_VISION_MODEL", "google/gemma-3n-e2b-it:free"
        )

    def extract_receipt_data(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Extract payment receipt data from an image using OpenRouter multimodal capabilities.

        Args:
            image_bytes: Raw image bytes

        Returns:
            Dict with extracted data
        """
        if not self.client.api_key:
            logger.error("OpenRouter API key not set — OCR unavailable")
            return self._fallback_response("OCR Service unavailable")

        # Encode image to base64
        base64_image = base64.b64encode(image_bytes).decode("utf-8")

        # Determine mime type (basic inference)
        mime_type = "image/jpeg"
        if image_bytes.startswith(b"\x89PNG"):
            mime_type = "image/png"

        current_date = date.today().strftime("%Y-%m-%d")

        prompt = f"""
Eres un asistente especializado en extracción de datos de comprobantes de pago peruanos.
Tu tarea es extraer información precisa de pagos a partir de la imagen proporcionada.

CONTEXTO:
- Usuarios envían comprobantes (vouchers, capturas de pantalla, etc.)
- La moneda es soles peruanos (S/)
- La fecha actual es: {current_date}

INSTRUCCIONES DE EXTRACCIÓN:
1. MONTO (amount): Monto principal de la transacción (numérico).
2. FECHA (date): Fecha de la operación en formato YYYY-MM-DD.
3. ID (document_id): Código de operación, número de referencia o transacción.
4. CONFIANZA (confidence): 0.0 a 1.0.

Responde únicamente con un objeto JSON válido con estas llaves:
{{
  "amount": number or null,
  "date": "string" or null,
  "document_id": "string" or null,
  "confidence": number,
  "notes": "string"
}}
"""

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{base64_image}"
                        },
                    },
                ],
            }
        ]

        try:
            response_text = self.client.chat_completion(
                messages=messages,
                model=self.model,
                temperature=0.1,  # Low temperature for extraction
                response_format={"type": "json_object"},
            )

            # Some models might wrap JSON in markdown blocks
            if isinstance(response_text, str):
                cleaned_text = response_text.strip()
                if cleaned_text.startswith("```json"):
                    cleaned_text = cleaned_text[7:-3].strip()
                elif cleaned_text.startswith("```"):
                    cleaned_text = cleaned_text[3:-3].strip()
                result = json.loads(cleaned_text)
            else:
                result = response_text

            # Add extraction method
            result["extraction_method"] = f"openrouter_ocr_{self.model}"

            logger.info("OCR Extraction successful via OpenRouter")
            return result

        except Exception as exc:
            logger.error("Error during OpenRouter OCR: %s", exc, exc_info=True)
            return self._fallback_response(str(exc))

    def _fallback_response(self, error_msg: str) -> Dict[str, Any]:
        """Return a safe fallback response when extraction fails."""
        return {
            "amount": None,
            "date": date.today().isoformat(),
            "document_id": None,
            "confidence": 0.0,
            "extraction_method": "fallback_error",
            "notes": f"Error: {error_msg}",
        }
