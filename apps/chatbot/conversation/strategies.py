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

        product_name = main_credit.get("product", "Préstamo")
        amount = f"{main_credit.get('amount', 0.0):,.2f}"
        interest_rate = f"{main_credit.get('interest_rate', 0.0):,.2f}"
        term = str(main_credit.get("term_duration") or "-")
        frequency = main_credit.get("payment_frequency") or "-"
        balance = f"{main_credit.get('outstanding_balance', 0.0):,.2f}"
        status = main_credit.get("status") or "-"

        disb_date = main_credit.get("disbursement_date") or "-"
        if disb_date != "-":
            disb_date = disb_date[:10]

        contributed = f"{tool_result.get('total_contributed', 0.0):,.2f}"
        social_security_pending = (
            f"{tool_result.get('total_social_security_pending', 0.0):,.2f}"
        )

        current_date = datetime.now().strftime("%d/%m/%Y")
        portal_link = getattr(
            settings,
            "PAYMENT_PORTAL_URL",
            "https://xofi.com/prestamo/1020/summary",
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
                                    "text": product_name,
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
                                {"type": "text", "text": disb_date},  # {{13}}
                                {"type": "text", "text": contributed},  # {{14}}
                                {
                                    "type": "text",
                                    "text": social_security_pending,
                                },  # {{15}}
                                {"type": "text", "text": portal_link},  # {{16}}
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
                f"💳 *Detalle de tu último crédito*\n"
                f"• Producto: *{product_name}*\n"
                f"• Monto original: *S/ {amount}*\n"
                f"• Tasa: *{interest_rate}% anual*\n"
                f"• Plazo: *{term} meses*\n"
                f"• Frecuencia: *{frequency}*\n"
                f"• Saldo actual: *S/ {balance}*\n"
                f"• Estado: *{status}*\n\n"
                f"📅 *Fechas importantes*\n"
                f"• Desembolso: {disb_date}\n\n"
                f"🏦 *Aportes y Previsión Social*\n"
                f"• Aportes: *S/ {contributed}*\n"
                f"• Previsión social: *S/ {social_security_pending}*\n\n"
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


class GetCreditDetailStrategy(IntentStrategy):
    """Strategy for the get_credit_detail tool."""

    def handle(
        self,
        tool_args: Dict[str, Any],
        tool_result: Dict[str, Any],
        channel: str,
    ) -> BotResponse:
        if "error" in tool_result:
            return BotResponse(text=tool_result["error"])

        product_name = tool_result.get("product_name") or "-"
        amount = f"{tool_result.get('amount', 0.0):,.2f}"
        balance = f"{tool_result.get('outstanding_balance', 0.0):,.2f}"
        payment = f"{tool_result.get('payment_amount', 0.0):,.2f}"
        status = tool_result.get("status") or "-"
        term = str(tool_result.get("term_duration") or "-")
        freq = tool_result.get("payment_frequency") or "-"
        rate = f"{tool_result.get('interest_rate', 0.0):,.2f}"
        overdue = str(tool_result.get("overdue_count") or "0")
        pending = str(tool_result.get("pending_count") or "0")

        if channel == choices.ChannelType.WHATSAPP:
            # According to docs/template_account_credit_detail.md (10 parameters)
            return BotResponse(
                text=f"Aquí tienes el detalle de tu {product_name}.",
                template={
                    "name": "account_credit_detail",
                    "language": "es_PE",
                    "components": [
                        {
                            "type": "body",
                            "parameters": [
                                {"type": "text", "text": product_name},  # {{1}}
                                {"type": "text", "text": amount},  # {{2}}
                                {"type": "text", "text": balance},  # {{3}}
                                {"type": "text", "text": payment},  # {{4}}
                                {"type": "text", "text": status},  # {{5}}
                                {"type": "text", "text": term},  # {{6}}
                                {"type": "text", "text": freq},  # {{7}}
                                {"type": "text", "text": rate},  # {{8}}
                                {"type": "text", "text": overdue},  # {{9}}
                                {"type": "text", "text": pending},  # {{10}}
                            ],
                        }
                    ],
                },
            )
        else:
            text = (
                f"Aquí tienes el *detalle de tu préstamo*:\n\n"
                f"💳 *{product_name}*\n\n"
                f"📊 *Resumen*\n"
                f"• Monto original: *S/ {amount}*\n"
                f"• Saldo pendiente: *S/ {balance}*\n"
                f"• Cuota mensual: *S/ {payment}*\n"
                f"• Estado: *{status}*\n\n"
                f"📅 *Condiciones*\n"
                f"• Plazo: *{term} meses*\n"
                f"• Frecuencia: *{freq}*\n"
                f"• Tasa: *{rate}%*\n\n"
                f"⚠️ *Situación actual*\n"
                f"• Cuotas vencidas: *{overdue}*\n"
                f"• Cuotas pendientes: *{pending}*\n\n"
                f"👉 Escribe *CRONOGRAMA* para ver el detalle de tus cuotas"
            )
            return BotResponse(text=text)


class GetCreditScheduleStrategy(IntentStrategy):
    """Strategy for the get_credit_schedule tool."""

    def handle(
        self,
        tool_args: Dict[str, Any],
        tool_result: Dict[str, Any],
        channel: str,
    ) -> BotResponse:
        if "error" in tool_result:
            return BotResponse(text=tool_result["error"])

        product_name = tool_result.get("product_name") or "Crédito"
        overdue = tool_result.get("overdue") or []
        next_3 = tool_result.get("next_installments") or []
        total_overdue = f"{tool_result.get('total_overdue_amount', 0.0):,.2f}"

        lines = [f"📅 *Cronograma de pagos - {product_name}*", ""]

        if overdue:
            lines.append("🔴 *Cuotas vencidas*")
            for i, inst in enumerate(overdue, 1):
                lines.append(
                    f"{inst['number']}. {inst['due_date']} - S/ {inst['amount']:,.2f} ({inst['days_overdue']} días)"
                )
            lines.append("")

        if next_3:
            lines.append("🟡 *Próximas 3 cuotas*")
            for inst in next_3:
                lines.append(
                    f"{inst['number']}. {inst['due_date']} - S/ {inst['amount']:,.2f}"
                )
            lines.append("")

        lines.append(f"💰 Total vencido: *S/ {total_overdue}*")

        return BotResponse(text="\n".join(lines))


class RequestSupportTicketStrategy(IntentStrategy):
    """Strategy for the request_support_ticket tool."""

    def handle(
        self,
        tool_args: Dict[str, Any],
        tool_result: Dict[str, Any],
        channel: str,
    ) -> BotResponse:
        if channel == choices.ChannelType.WHATSAPP:
            return BotResponse(
                text="Por favor, completa el formulario para crear tu ticket.",
                template={
                    "name": "support_ticket_create",
                    "language": "es_PE",
                    "components": [
                        {
                            "type": "button",
                            "sub_type": "flow",
                            "index": "0",
                            "parameters": [
                                {
                                    "type": "action",
                                    "action": {
                                        "flow_token": "support_ticket_request",
                                    },
                                }
                            ],
                        }
                    ],
                },
            )
        else:
            return BotResponse(
                text="Por favor, indícame el *asunto* y la *descripción* detallada de tu consulta para crear el ticket de soporte."
            )


class CreateSupportTicketStrategy(IntentStrategy):
    """Strategy for the create_support_ticket tool."""

    def handle(
        self,
        tool_args: Dict[str, Any],
        tool_result: Dict[str, Any],
        channel: str,
    ) -> BotResponse:
        if "error" in tool_result:
            return BotResponse(text=tool_result["error"])

        ticket_id = tool_result.get("id") or "-"
        text = (
            f"✅ *Ticket #{ticket_id} creado correctamente*\n\n"
            f"Nuestro equipo revisará tu caso y se contactará contigo lo antes posible."
        )
        return BotResponse(text=text)


class RequestLoanProspectStrategy(IntentStrategy):
    """Strategy for the request_loan_prospect tool."""

    def handle(
        self,
        tool_args: Dict[str, Any],
        tool_result: Dict[str, Any],
        channel: str,
    ) -> BotResponse:
        if channel == choices.ChannelType.WHATSAPP:
            return BotResponse(
                text="¡Genial! Por favor, completa el siguiente formulario para evaluar tu solicitud de crédito.",
                template={
                    "name": "credit_application_invitation",
                    "language": "en",
                    "components": [
                        {
                            "type": "button",
                            "sub_type": "flow",
                            "index": "0",
                            "parameters": [
                                {
                                    "type": "action",
                                    "action": {
                                        "flow_token": "loan_prospect_create",
                                    },
                                }
                            ],
                        }
                    ],
                },
            )
        else:
            return BotResponse(
                text="Por favor, indícame tus datos (Nombres, Apellidos, DNI, Email, Teléfono, Fecha de Nacimiento y Monto) para registrar tu solicitud de crédito."
            )


class CreateLoanProspectStrategy(IntentStrategy):
    """Strategy for the create_loan_prospect tool."""

    def handle(
        self,
        tool_args: Dict[str, Any],
        tool_result: Dict[str, Any],
        channel: str,
    ) -> BotResponse:
        if "error" in tool_result:
            return BotResponse(text=tool_result["error"])

        text = (
            "✅ *¡Solicitud recibida!*\n\n"
            "Tus datos han sido registrados correctamente. Un asesor se pondrá en contacto contigo muy pronto para continuar con la evaluación de tu crédito.\n\n"
            "¡Gracias por confiar en XoFi!"
        )
        return BotResponse(text=text)


class StrategyFactory:
    """Factory to retrieve the appropriate strategy for a given tool/intent."""

    _strategies = {
        "get_partner_detail": GetPartnerDetailStrategy(),
        "get_account_statement": GetAccountStatementStrategy(),
        "get_credits_list": GetCreditsListStrategy(),
        "get_credit_detail": GetCreditDetailStrategy(),
        "get_credit_schedule": GetCreditScheduleStrategy(),
        "request_support_ticket": RequestSupportTicketStrategy(),
        "create_support_ticket": CreateSupportTicketStrategy(),
        "request_loan_prospect": RequestLoanProspectStrategy(),
        "create_loan_prospect": CreateLoanProspectStrategy(),
    }

    @classmethod
    def get_strategy(cls, tool_name: str) -> IntentStrategy | None:
        """Get the strategy for the given tool name."""
        return cls._strategies.get(tool_name)
