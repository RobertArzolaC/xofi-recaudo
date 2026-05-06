"""AI Agent orchestrator using OpenRouter."""

import json
import logging
from typing import Any

from apps.chatbot.agent.prompts import AGENT_SYSTEM_PROMPT
from apps.chatbot.agent.tools import ToolRegistry
from apps.chatbot.constants import ERROR_PROCESSING_MESSAGE
from apps.chatbot.services.partner_api import PartnerAPIService
from apps.core.clients.openrouter import OpenRouterClient

logger = logging.getLogger(__name__)

# Maximum number of recent messages to include as conversation history
_HISTORY_LIMIT = 20

# Safety guard: maximum tool call iterations per user message
_MAX_TOOL_ITERATIONS = 5


class AgentService:
    """
    Orchestrates multi-turn conversations via OpenRouter API.

    Flow per user message:
    1. Build conversation history from DB (last N messages).
    2. Create a client with the sector-specific system prompt and tool
       declarations.
    3. Send the user message; if the model returns a tool call, execute it
       via ToolRegistry and feed the result back.
    4. Repeat step 3 until the model produces a text response or the iteration
       limit is reached.
    5. Return (response_text, tools_called_list).
    """

    def __init__(self):
        self._client = OpenRouterClient()
        if self._client.api_key:
            self._available = True
        else:
            logger.warning("OPENROUTER_API_KEY not set — AgentService unavailable")
            self._available = False

    def process(
        self, conversation, user_message: str
    ) -> tuple[str, list[dict[str, Any]]]:
        """
        Process a user message within a conversation.

        Args:
            conversation: AgentConversation instance.
            user_message: The raw text from the user.

        Returns:
            (response_text, tools_called) where tools_called is a list of
            {"tool": name, "args": {...}} dicts for logging purposes.
        """
        if not self._available:
            return ERROR_PROCESSING_MESSAGE, []

        is_auth = conversation.authenticated
        partner = conversation.partner
        api_service = PartnerAPIService()
        
        registry = ToolRegistry(
            partner_id=partner.id if partner else None,
            partner_document=partner.document_number if partner else None,
            api_service=api_service,
            authenticated=is_auth,
        )

        partner_info = ""
        if is_auth and partner:
            # Fetch associated products to inject into the system prompt context
            credits_data = api_service.get_credits_list(partner.id, status="ACTIVE")
            active_products = []
            if credits_data and "credits" in credits_data:
                active_products = list(set([c["product_name"] for c in credits_data["credits"]]))
            partner_products = ", ".join(active_products) if active_products else "Ninguno"
            
            partner_info = (
                f"Nombre: {partner.full_name}\n"
                f"Documento: {partner.document_number}\n"
                f"Productos activos asociados: {partner_products}"
            )
            auth_status = "AUTENTICADO"
        else:
            auth_status = "NO AUTENTICADO"

        system_prompt = AGENT_SYSTEM_PROMPT.format(
            auth_status=auth_status,
            partner_info=partner_info,
        )

        history = [{"role": "system", "content": system_prompt}] + self._build_history(conversation)
        history.append({"role": "user", "content": user_message})

        tools_called: list[dict[str, Any]] = []
        tool_declarations = registry.get_tool_declarations()

        for _ in range(_MAX_TOOL_ITERATIONS):
            # Inner retry loop for the current turn (to handle intermittent API format errors)
            response_msg = None
            last_error = None
            for attempt in range(3):
                try:
                    response_msg = self._client.chat_completion(
                        messages=history,
                        tools=tool_declarations,
                        return_message=True
                    )
                    break # Success!
                except Exception as exc:
                    last_error = exc
                    logger.warning(f"Turn attempt {attempt + 1} failed: {exc}")
                    if attempt < 2:
                        import time
                        time.sleep(1) # Small delay before retry
            
            if not response_msg:
                logger.error("All attempts for current turn failed.")
                return ERROR_PROCESSING_MESSAGE, tools_called

            history.append(response_msg)

            if response_msg.get("tool_calls"):
                for tool_call in response_msg["tool_calls"]:
                    if tool_call.get("type") != "function":
                        continue
                        
                    tool_name = tool_call["function"]["name"]
                    try:
                        tool_args = json.loads(tool_call["function"]["arguments"])
                    except Exception:
                        tool_args = {}

                    logger.info("OpenRouter called tool: %s with args: %s", tool_name, tool_args)
                    result = registry.execute(tool_name, tool_args)
                    tools_called.append({
                        "tool": tool_name, 
                        "args": tool_args,
                        "result": result
                    })

                    # If this is a terminal tool that handles its own formatting via Strategy,
                    # we break early to save tokens and latency.
                    if tool_name in [
                        "get_partner_detail",
                        "get_account_statement",
                        "get_credits_list",
                        "get_credit_detail",
                        "get_credit_schedule",
                        "request_support_ticket",
                        "create_support_ticket",
                        "request_payment_receipt_upload",
                        "request_prospect_registration",
                    ]:
                        return "", tools_called

                    history.append({
                        "role": "tool",
                        "content": json.dumps({"result": result}, ensure_ascii=False),
                        "tool_call_id": tool_call["id"],
                        "name": tool_name
                    })
                
                # Continue the loop so the model can generate the next response
                continue

            # If no tools called, we're done
            response_text = response_msg.get("content") or response_msg.get("reasoning") or ""
            return response_text, tools_called

        # Exited loop due to max iterations
        try:
            response_text = history[-1].get("content") or history[-1].get("reasoning") or ""
        except Exception:
            response_text = ERROR_PROCESSING_MESSAGE

        return response_text, tools_called

    @staticmethod
    def _build_history(conversation) -> list:
        """
        Build OpenRouter Content history from recent ConversationMessage records.

        Only USER and AGENT messages are included.
        Ordered chronologically (oldest first).
        """
        from apps.chatbot.choices import MessageSender

        recent = list(
            conversation.messages.filter(
                sender__in=[MessageSender.USER, MessageSender.AGENT]
            ).order_by("-created")[:_HISTORY_LIMIT]
        )
        recent.reverse()

        history = []
        for msg in recent:
            role = "user" if msg.sender == MessageSender.USER else "assistant"
            history.append({"role": role, "content": msg.message})
        return history
