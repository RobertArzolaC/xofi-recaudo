"""
Agent module for the XoFi chatbot.

Provides the Gemini-powered AI agent with function calling support.
"""

from .service import AgentService
from .tools import ToolRegistry

__all__ = ["AgentService", "ToolRegistry"]
