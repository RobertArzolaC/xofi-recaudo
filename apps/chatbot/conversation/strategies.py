from abc import ABC, abstractmethod
from typing import Any, Dict

from apps.chatbot import choices
from apps.chatbot.conversation.responses import BotResponse


class IntentStrategy(ABC):
    """Base interface for intent-specific response strategies."""

    @abstractmethod
    def handle(
        self, tool_args: Dict[str, Any], tool_result: Dict[str, Any], channel: str
    ) -> BotResponse:
        """Handle the tool result and return a formatted BotResponse."""
        pass


class GetPartnerDetailStrategy(IntentStrategy):
    """Strategy for the get_partner_detail tool."""

    def handle(
        self, tool_args: Dict[str, Any], tool_result: Dict[str, Any], channel: str
    ) -> BotResponse:
        if "error" in tool_result:
            return BotResponse(text=tool_result["error"])

        full_name = tool_result.get("full_name") or "-"
        document_number = str(tool_result.get("document_number") or "-")
        phone = tool_result.get("phone") or "-"
        email = tool_result.get("email") or "-"
        address = tool_result.get("address") or "No registrada"
        status_val = tool_result.get("status")
        created = tool_result.get("created") or ""
        registration_date = created[:10] if created else "-"

        # Human readable status
        status_map = {0: "Pendiente", 1: "Activo", 2: "Inactivo", 3: "Suspendido"}
        status_text = status_map.get(status_val, "Desconocido")

        if channel == choices.ChannelType.WHATSAPP:
            # According to docs/template_profile_summanry.md:
            # {{nombre_completo}}, {{numero_doc}}, {{telefono}}, {{correo}}, {{direccion}}, {{status}}, {{fecha_registro}}
            return BotResponse(
                text=f"Aquí tienes un resumen de tus datos personales, {full_name}.",
                template={
                    "name": "customer_profile_summary",
                    "language": "es",
                    "components": [
                        {
                            "type": "body",
                            "parameters": [
                                {"type": "text", "text": full_name},
                                {"type": "text", "text": document_number},
                                {"type": "text", "text": phone},
                                {"type": "text", "text": email},
                                {"type": "text", "text": address},
                                {"type": "text", "text": status_text},
                                {"type": "text", "text": registration_date},
                            ],
                        }
                    ],
                },
            )
        else:
            # Telegram / Web / Other channels: return formatted text
            text = (
                f"Aquí tienes un resumen de tus *datos personales* en XoFi:\n\n"
                f"🪪 *Identificación*\n"
                f"• Nombre: *{full_name}*\n"
                f"• Documento: {document_number}\n\n"
                f"📱 *Contacto*\n"
                f"• Teléfono: {phone}\n"
                f"• Correo: {email}\n\n"
                f"📍 *Dirección*\n"
                f"{address}\n\n"
                f"🏢 *Estado*\n"
                f"• {status_text}\n"
                f"• Registro: {registration_date}\n\n"
                f"📌 También puedes consultar:\n"
                f"• Estado de cuenta\n"
                f"• Préstamos\n"
                f"• Menú principal"
            )
            return BotResponse(text=text)


class StrategyFactory:
    """Factory to retrieve the appropriate strategy for a given tool/intent."""

    _strategies = {
        "get_partner_detail": GetPartnerDetailStrategy(),
    }

    @classmethod
    def get_strategy(cls, tool_name: str) -> IntentStrategy | None:
        """Get the strategy for the given tool name."""
        return cls._strategies.get(tool_name)
