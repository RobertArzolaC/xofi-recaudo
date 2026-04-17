from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict

from django.conf import settings

from apps.chatbot import choices
from apps.chatbot.conversation.responses import BotResponse


class IntentStrategy(ABC):
    """Base interface for intent-specific response strategies."""

    @abstractmethod
    def handle(
        self,
        tool_args: Dict[str, Any],
        tool_result: Dict[str, Any],
        channel: str,
    ) -> BotResponse:
        """Handle the tool result and return a formatted BotResponse."""
        pass


class GetPartnerDetailStrategy(IntentStrategy):
    """Strategy for the get_partner_detail tool."""

    def handle(
        self,
        tool_args: Dict[str, Any],
        tool_result: Dict[str, Any],
        channel: str,
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
        status_map = {
            0: "Pendiente",
            1: "Activo",
            2: "Inactivo",
            3: "Suspendido",
        }
        status_text = status_map.get(status_val, "Desconocido")

        if channel == choices.ChannelType.WHATSAPP:
            # According to docs/template_profile_summanry.md:
            # {{nombre_completo}}, {{numero_doc}}, {{telefono}}, {{correo}}, {{direccion}}, {{status}}, {{fecha_registro}}
            return BotResponse(
                text=f"Aquí tienes un resumen de tus datos personales, {full_name}.",
                template={
                    "name": "customer_profile_summary",
                    "language": "es_PE",
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


class GetAccountStatementStrategy(IntentStrategy):
    """Strategy for the get_account_statement tool."""

    def handle(
        self,
        tool_args: Dict[str, Any],
        tool_result: Dict[str, Any],
        channel: str,
    ) -> BotResponse:
        if "error" in tool_result:
            return BotResponse(text=tool_result["error"])

        summary = tool_result.get("summary") or {}
        active_credits = str(summary.get("active_credits_count", 0))
        total_disbursed = f"{summary.get('total_disbursed', 0.0):,.2f}"
        total_paid = f"{summary.get('total_payments', 0.0):,.2f}"
        total_outstanding = f"{summary.get('total_outstanding', 0.0):,.2f}"

        credits = tool_result.get("credits") or []
        main_credit = credits[0] if credits else {}

        product_names = []
        for c in credits:
            name = c.get("product") or c.get("product_name")
            if name and str(name) not in product_names:
                product_names.append(str(name))
        associated_products = ", ".join(product_names) if product_names else "-"

        amount = f"{main_credit.get('amount', 0.0):,.2f}"
        interest_rate = f"{main_credit.get('interest_rate', 0.0):,.2f}"
        term = str(main_credit.get("term_duration") or "-")
        frequency = main_credit.get("payment_frequency") or "-"
        balance = f"{main_credit.get('outstanding_balance', 0.0):,.2f}"
        status = main_credit.get("status") or "-"

        app_date = main_credit.get("application_date") or "-"
        disb_date = main_credit.get("disbursement_date") or "-"
        if app_date != "-":
            app_date = app_date[:10]
        if disb_date != "-":
            disb_date = disb_date[:10]

        contributed = f"{tool_result.get('total_contributed', 0.0):,.2f}"
        social_security = (
            f"{tool_result.get('total_social_security_paid', 0.0):,.2f}"
        )

        current_date = datetime.now().strftime("%d/%m/%Y")
        portal_link = getattr(
            settings, "PAYMENT_PORTAL_URL", "https://portal.xofi.pe/pago"
        )

        if channel == choices.ChannelType.WHATSAPP:
            # According to docs/template_account_statement_summary.md (17 parameters)
            return BotResponse(
                text=f"Aquí tienes tu estado de cuenta actualizado al {current_date}.",
                template={
                    "name": "account_statement_summary",
                    "language": "es_PE",
                    "components": [
                        {
                            "type": "body",
                            "parameters": [
                                {"type": "text", "text": current_date},  # {{1}}
                                {
                                    "type": "text",
                                    "text": active_credits,
                                },  # {{2}}
                                {
                                    "type": "text",
                                    "text": total_disbursed,
                                },  # {{3}}
                                {"type": "text", "text": total_paid},  # {{4}}
                                {
                                    "type": "text",
                                    "text": total_outstanding,
                                },  # {{5}}
                                {
                                    "type": "text",
                                    "text": associated_products,
                                },  # {{6}}
                                {"type": "text", "text": amount},  # {{7}}
                                {
                                    "type": "text",
                                    "text": interest_rate,
                                },  # {{8}}
                                {"type": "text", "text": term},  # {{9}}
                                {"type": "text", "text": frequency},  # {{10}}
                                {"type": "text", "text": balance},  # {{11}}
                                {"type": "text", "text": status},  # {{12}}
                                {"type": "text", "text": app_date},  # {{13}}
                                {"type": "text", "text": disb_date},  # {{14}}
                                {"type": "text", "text": contributed},  # {{15}}
                                {
                                    "type": "text",
                                    "text": social_security,
                                },  # {{16}}
                                {"type": "text", "text": portal_link},  # {{17}}
                            ],
                        }
                    ],
                },
            )
        else:
            text = (
                f"Aquí tienes tu *estado de cuenta actualizado* al *{current_date}*:\n\n"
                f"📊 *Resumen general*\n"
                f"• Créditos activos: *{active_credits}*\n"
                f"• Total desembolsado: *S/ {total_disbursed}*\n"
                f"• Total pagado: *S/ {total_paid}*\n"
                f"• Saldo pendiente: *S/ {total_outstanding}*\n\n"
                f"💳 *Detalle de tu crédito*\n"
                f"• Productos: *{associated_products}*\n"
                f"• Monto original: *S/ {amount}*\n"
                f"• Tasa: *{interest_rate}% anual*\n"
                f"• Plazo: *{term} meses*\n"
                f"• Frecuencia: *{frequency}*\n"
                f"• Saldo actual: *S/ {balance}*\n"
                f"• Estado: *{status}*\n\n"
                f"📅 *Fechas importantes*\n"
                f"• Solicitud: {app_date}\n"
                f"• Desembolso: {disb_date}\n\n"
                f"🏦 *Aportes y Previsión Social*\n"
                f"• Aportes: *S/ {contributed}*\n"
                f"• Previsión social: *S/ {social_security}*\n\n"
                f"Si deseas ver el detalle completo o realizar un pago, puedes hacerlo aquí 👇\n"
                f"{portal_link}"
            )
            return BotResponse(text=text)


class GetCreditsListStrategy(IntentStrategy):
    """Strategy for the get_credits_list tool."""

    def handle(
        self,
        tool_args: Dict[str, Any],
        tool_result: Dict[str, Any],
        channel: str,
    ) -> BotResponse:
        if "error" in tool_result:
            return BotResponse(text=tool_result["error"])

        summary = tool_result.get("summary") or {}
        active_count = str(summary.get("active_credits_count", 0))
        total_outstanding = f"{summary.get('total_outstanding', 0.0):,.2f}"
        total_paid = f"{summary.get('total_payments', 0.0):,.2f}"
        associated_products = summary.get("associated_products") or "Ninguno"

        if channel == choices.ChannelType.WHATSAPP:
            # According to docs/template_account_credit_list.md
            return BotResponse(
                text=f"Tienes {active_count} préstamos activos.",
                template={
                    "name": "account_credit_list",
                    "language": "es_PE",
                    "components": [
                        {
                            "type": "body",
                            "parameters": [
                                {"type": "text", "text": active_count},  # {{1}}
                                {
                                    "type": "text",
                                    "text": total_outstanding,
                                },  # {{2}}
                                {"type": "text", "text": total_paid},  # {{3}}
                                {
                                    "type": "text",
                                    "text": associated_products,
                                },  # {{4}}
                            ],
                        }
                    ],
                },
            )
        else:
            text = (
                f"Tienes *{active_count} préstamos activos*:\n\n"
                f"📊 *Resumen*\n"
                f"• Deuda total: *S/ {total_outstanding}*\n"
                f"• Total pagado: *S/ {total_paid}*\n\n"
                f"📂 *Productos asociados:*\n"
                f"{associated_products}\n\n"
                f"Selecciona un préstamo para ver el detalle 👇"
            )
            return BotResponse(text=text)


class StrategyFactory:
    """Factory to retrieve the appropriate strategy for a given tool/intent."""

    _strategies = {
        "get_partner_detail": GetPartnerDetailStrategy(),
        "get_account_statement": GetAccountStatementStrategy(),
        "get_credits_list": GetCreditsListStrategy(),
    }

    @classmethod
    def get_strategy(cls, tool_name: str) -> IntentStrategy | None:
        """Get the strategy for the given tool name."""
        return cls._strategies.get(tool_name)
