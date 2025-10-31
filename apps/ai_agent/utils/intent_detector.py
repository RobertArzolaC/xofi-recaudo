import re
from typing import Dict, Optional

from apps.ai_agent.choices import IntentType
from apps.ai_agent.constants import INTENT_KEYWORDS


class IntentDetector:
    """
    Intent detector using spaCy for NLP and rule-based matching.
    This reduces the need for LLM calls for common queries.
    """

    INTENT_KEYWORDS = {
        IntentType.GREETING: INTENT_KEYWORDS["GREETING"],
        IntentType.GOODBYE: INTENT_KEYWORDS["GOODBYE"],
        IntentType.HELP: INTENT_KEYWORDS["HELP"],
        IntentType.PARTNER_DETAIL: INTENT_KEYWORDS["PARTNER_DETAIL"],
        IntentType.ACCOUNT_STATEMENT: INTENT_KEYWORDS["ACCOUNT_STATEMENT"],
        IntentType.LIST_CREDITS: INTENT_KEYWORDS["LIST_CREDITS"],
        IntentType.CREDIT_DETAIL: INTENT_KEYWORDS["CREDIT_DETAIL"],
        IntentType.CREATE_TICKET: INTENT_KEYWORDS["CREATE_TICKET"],
        IntentType.UPLOAD_RECEIPT: INTENT_KEYWORDS["UPLOAD_RECEIPT"],
    }

    def __init__(self):
        """Initialize spaCy model."""
        try:
            import spacy

            try:
                self.nlp = spacy.load("es_core_news_sm")
            except OSError:
                self.nlp = spacy.blank("es")
        except ImportError:
            self.nlp = None

    def detect_intent(self, message: str) -> IntentType:
        """
        Detect the intent of a message using NLP and keyword matching.

        Args:
            message: User message text

        Returns:
            Detected IntentType
        """
        message_lower = message.lower().strip()

        if self._is_authentication_message(message_lower):
            return IntentType.AUTHENTICATION

        if self.nlp:
            doc = self.nlp(message_lower)
            lemmas = [token.lemma_ for token in doc]
            text_to_match = " ".join(lemmas)
        else:
            text_to_match = message_lower

        for intent, keywords in self.INTENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_to_match or keyword in message_lower:
                    return intent

        return IntentType.UNKNOWN

    @staticmethod
    def _is_authentication_message(message: str) -> bool:
        """
        Check if message matches authentication pattern.
        Expected: document_number and birth_year (e.g., "12345678 1990")
        """
        # Pattern: 8 digits + space + 4 digits (year)
        pattern = r"\b\d{8}\s+\d{4}\b"
        return bool(re.search(pattern, message))

    @staticmethod
    def extract_auth_data(message: str) -> Optional[Dict[str, str]]:
        """
        Extract authentication data from message.

        Returns:
            Dict with document_number and birth_year or None
        """
        pattern = r"\b(\d{8})\s+(\d{4})\b"
        match = re.search(pattern, message)
        if match:
            return {
                "document_number": match.group(1),
                "birth_year": match.group(2),
            }
        return None

    @staticmethod
    def extract_credit_id(message: str) -> Optional[int]:
        """
        Extract credit ID from message.

        Returns:
            Credit ID as integer or None
        """
        # Look for patterns like "prestamo 123", "credito 456", etc.
        pattern = r"(?:prestamo|credito|cr[ée]dito)[\s#:]*(\d+)"
        match = re.search(pattern, message.lower())
        if match:
            return int(match.group(1))

        # Also check for standalone numbers
        numbers = re.findall(r"\b(\d+)\b", message)
        if len(numbers) == 1:
            return int(numbers[0])

        return None
