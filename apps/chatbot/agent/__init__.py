"""
Agent module for the XoFi chatbot.

Provides the Gemini-powered AI agent with function calling support.
"""

from .service import AgentService
from .tools import TOOL_DECLARATIONS, ToolRegistry

__all__ = ["AgentService", "ToolRegistry", "TOOL_DECLARATIONS"]
