import json
import logging
from typing import Any, Dict, Optional

from django.conf import settings

from apps.ai_agent import constants

logger = logging.getLogger(__name__)


class AIAgentService:
    """
    AI Agent service using Google Gemini.
    Handles complex queries that cannot be resolved with rule-based matching.
    """

    def __init__(self):
        """Initialize AI agent with Gemini configuration."""
        self.gemini_api_key = getattr(settings, "GOOGLE_GEMINI_API_KEY", "")
        self.model_name = getattr(settings, "GEMINI_MODEL_NAME", "gemini-pro")

        # Initialize Gemini client
        self._init_gemini_client()

    def _init_gemini_client(self):
        """Initialize Google Gemini client."""
        try:
            import google.generativeai as genai

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

    def process_complex_query(
        self, query: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Process a complex query using AI.

        Args:
            query: User's query text
            context: Additional context (partner info, recent data, etc.)

        Returns:
            AI-generated response
        """
        if not self.gemini_model:
            return constants.AI_SERVICE_UNAVAILABLE

        # Build prompt with context
        prompt = self._build_prompt(query, context)

        try:
            # Generate response using Gemini
            response = self.gemini_model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return constants.AI_PROCESSING_ERROR

    def _build_prompt(
        self, query: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build prompt for AI model with context."""
        system_prompt = constants.GEMINI_SYSTEM_PROMPT

        if context:
            partner = context.get("partner")
            if partner:
                system_prompt += f"""
Socio:
- Nombre: {partner.get("full_name", "N/A")}
- Documento: {partner.get("document_number", "N/A")}
"""

            account_summary = context.get("account_summary")
            if account_summary:
                system_prompt += f"""
Resumen de cuenta:
- Créditos activos: {account_summary.get("active_credits_count", 0)}
- Saldo pendiente: S/ {account_summary.get("total_outstanding", 0):,.2f}
"""

        system_prompt += f"\n\nConsulta del socio: {query}\n\nRespuesta:"

        return system_prompt

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


# Singleton instance
_ai_agent_service = None


def get_ai_agent_service() -> AIAgentService:
    """Get or create singleton AI agent service instance."""
    global _ai_agent_service
    if _ai_agent_service is None:
        _ai_agent_service = AIAgentService()
    return _ai_agent_service
