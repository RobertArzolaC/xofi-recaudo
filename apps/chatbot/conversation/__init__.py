"""
Conversation module for chatbot.

This module contains the conversation logic and utilities
that are shared across all channels.
"""

from .intent_detector import IntentDetector
from .message_formatter import MessageFormatter
from .service import ConversationService

__all__ = ["ConversationService", "IntentDetector", "MessageFormatter"]
