"""
Management command to seed mock data for the chatbot dashboard.

Usage:
    python manage.py seed_chatbot_data
    python manage.py seed_chatbot_data --clear   # borra datos existentes primero
"""
import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone


WHATSAPP_PHONES = [
    "+573001234567", "+573109876543", "+573205551234", "+573112223333",
    "+573004445566", "+573207778899", "+573001112233", "+573104445566",
    "+573209998877", "+573003336655", "+573106667788", "+573201234321",
    "+573008887766", "+573105554433", "+573204443322", "+573007776655",
    "+573102221100", "+573206665544", "+573009990011", "+573103332211",
]

TELEGRAM_CHAT_IDS = [
    "100111222", "100333444", "100555666", "100777888", "100999000",
]

TELEGRAM_USERNAMES = [
    "jperez", "mgarcia", "rlopez", "crodriguez", "afernandez",
]

PARTNER_NAMES = [
    "Juan Pérez", "María García", "Roberto López", "Carmen Rodríguez",
    "Andrés Fernández", "Lucía Martínez", "Felipe Torres", "Diana Vargas",
    "Sergio Muñoz", "Patricia Herrera", "Alejandro Díaz", "Natalia Sánchez",
    "Miguel Ángel Ruiz", "Valentina Castro", "Esteban Morales", "Claudia Jiménez",
    "Hernán Gómez", "Isabel Ramos", "David Suárez", "Mónica Ortega",
]

BOT_RESPONSES = [
    "Hola, soy el asistente virtual de la cooperativa. ¿En qué puedo ayudarte?",
    "Tu saldo actual es de $1.250.000 COP. ¿Deseas ver el detalle?",
    "He registrado tu pago. El comprobante fue procesado exitosamente.",
    "Tu próximo vencimiento es el 5 del próximo mes por $320.000.",
    "Por favor, envía una foto clara del comprobante de pago.",
    "Tu crédito #CR-2024-0081 está al día. ¡Gracias por tu puntualidad!",
    "Se ha creado el ticket de soporte #TK-0045. Te contactaremos pronto.",
    "Para autenticarte, por favor ingresa tu número de cédula.",
    "Autenticación exitosa. Bienvenido, estamos para servirte.",
    "¿Hay algo más en lo que pueda ayudarte?",
    "Tu extracto ha sido enviado al correo registrado.",
    "El horario de atención es de lunes a viernes de 8am a 5pm.",
    "Recuerda que puedes consultar tus créditos en cualquier momento.",
    "Para más información, comunícate con nuestras oficinas.",
]

USER_MESSAGES = [
    "Hola, necesito información",
    "1234567890",
    "Quiero ver mi saldo",
    "Cuánto debo pagar este mes?",
    "Tengo un problema con mi crédito",
    "Quiero subir un comprobante de pago",
    "Necesito hablar con un asesor",
    "Cuándo vence mi próximo pago?",
    "Quiero ver mi extracto",
    "Gracias, hasta luego",
    "Hola buenas tardes",
    "Cómo me autentico?",
    "Ver mis créditos",
    "Tengo un inconveniente",
    "Adjunto comprobante",
]

INTENT_WEIGHTS = [
    ("GREETING", 15),
    ("AUTHENTICATION", 20),
    ("ACCOUNT_STATEMENT", 12),
    ("LIST_CREDITS", 10),
    ("CREDIT_DETAIL", 8),
    ("UPLOAD_RECEIPT", 18),
    ("CREATE_TICKET", 6),
    ("PARTNER_DETAIL", 5),
    ("HELP", 4),
    ("GOODBYE", 7),
    ("UNKNOWN", 5),
]

TEMPLATE_DATA = [
    {
        "name": "bienvenida_cooperativa",
        "category": "UTILITY",
        "language": "es",
        "status": "APPROVED",
        "body": "Bienvenido a la Cooperativa. Soy tu asistente virtual y estoy aquí para ayudarte con tus consultas de crédito y pagos. ¿En qué puedo ayudarte hoy?",
        "meta_template_id": "MT-001",
        "times_used": 245,
    },
    {
        "name": "recordatorio_pago",
        "category": "UTILITY",
        "language": "es",
        "status": "APPROVED",
        "body": "Hola {{1}}, te recordamos que tu cuota de crédito por {{2}} vence el {{3}}. Para pagar, responde este mensaje con tu comprobante.",
        "meta_template_id": "MT-002",
        "times_used": 512,
    },
    {
        "name": "confirmacion_pago",
        "category": "UTILITY",
        "language": "es",
        "status": "APPROVED",
        "body": "Tu pago de {{1}} ha sido recibido y procesado exitosamente. Número de transacción: {{2}}. ¡Gracias!",
        "meta_template_id": "MT-003",
        "times_used": 389,
    },
    {
        "name": "alerta_mora",
        "category": "UTILITY",
        "language": "es",
        "status": "APPROVED",
        "body": "Estimado {{1}}, tienes una cuota vencida desde el {{2}} por valor de {{3}}. Comunícate con nosotros para regularizar tu situación.",
        "meta_template_id": "MT-004",
        "times_used": 78,
    },
    {
        "name": "encuesta_satisfaccion",
        "category": "MARKETING",
        "language": "es",
        "status": "APPROVED",
        "body": "Hola {{1}}, queremos conocer tu opinión sobre nuestro servicio. ¿Cómo calificarías tu experiencia del 1 al 5?",
        "meta_template_id": "MT-005",
        "times_used": 134,
    },
    {
        "name": "extracto_mensual",
        "category": "UTILITY",
        "language": "es",
        "status": "APPROVED",
        "body": "Tu extracto del mes de {{1}} ya está disponible. Total a pagar: {{2}}. Próximo vencimiento: {{3}}.",
        "meta_template_id": "MT-006",
        "times_used": 201,
    },
    {
        "name": "oferta_nuevo_credito",
        "category": "MARKETING",
        "language": "es",
        "status": "PENDING",
        "body": "{{1}}, tienes una oferta preaprobada de crédito hasta {{2}} con una tasa preferencial. ¿Te interesa conocer más detalles?",
        "meta_template_id": None,
        "times_used": 0,
    },
    {
        "name": "autenticacion_otp",
        "category": "AUTHENTICATION",
        "language": "es",
        "status": "APPROVED",
        "body": "Tu código de verificación es: {{1}}. Válido por 5 minutos. No lo compartas con nadie.",
        "meta_template_id": "MT-007",
        "times_used": 623,
    },
    {
        "name": "actualizacion_datos",
        "category": "UTILITY",
        "language": "es",
        "status": "REJECTED",
        "body": "Hola {{1}}, detectamos que tus datos necesitan actualización. Por favor acércate a la oficina más cercana.",
        "meta_template_id": None,
        "times_used": 0,
    },
    {
        "name": "promocion_diciembre",
        "category": "MARKETING",
        "language": "es",
        "status": "PAUSED",
        "body": "¡Felices fiestas! Durante diciembre, disfruta de tasas especiales en tu próximo crédito. Válido hasta el 31/12.",
        "meta_template_id": "MT-008",
        "times_used": 45,
    },
]


def weighted_choice(weighted_list):
    choices, weights = zip(*weighted_list)
    total = sum(weights)
    r = random.uniform(0, total)
    cumulative = 0
    for choice, weight in zip(choices, weights):
        cumulative += weight
        if r <= cumulative:
            return choice
    return choices[-1]


class Command(BaseCommand):
    help = "Seed mock data for the chatbot dashboard"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing chatbot data before seeding",
        )
        parser.add_argument(
            "--conversations",
            type=int,
            default=20,
            help="Number of WhatsApp conversations to create (default: 20)",
        )

    def handle(self, *args, **options):
        from apps.chatbot.models import AgentConversation, ConversationMessage, WhatsAppTemplate
        from apps.chatbot.choices import (
            ChannelType, ConversationStatus, MessageSender,
            IntentType, MessageDeliveryStatus, TemplateStatus,
        )

        if options["clear"]:
            self.stdout.write("Borrando datos existentes del chatbot...")
            ConversationMessage.objects.all().delete()
            AgentConversation.objects.all().delete()
            WhatsAppTemplate.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Datos borrados."))

        # ── Templates ────────────────────────────────────────────────────────
        self.stdout.write("Creando plantillas WhatsApp...")
        templates_created = 0
        for tpl in TEMPLATE_DATA:
            _, created = WhatsAppTemplate.objects.get_or_create(
                name=tpl["name"],
                defaults={
                    "category": tpl["category"],
                    "language": tpl["language"],
                    "status": tpl["status"],
                    "body": tpl["body"],
                    "meta_template_id": tpl["meta_template_id"],
                    "times_used": tpl["times_used"],
                },
            )
            if created:
                templates_created += 1
        self.stdout.write(self.style.SUCCESS(f"  {templates_created} plantillas creadas."))

        # ── WhatsApp Conversations ───────────────────────────────────────────
        self.stdout.write("Creando conversaciones WhatsApp...")
        now = timezone.now()
        num_conversations = options["conversations"]
        phones_to_use = WHATSAPP_PHONES[:num_conversations]

        status_pool = (
            [ConversationStatus.ACTIVE] * 6
            + [ConversationStatus.AUTHENTICATED] * 5
            + [ConversationStatus.PENDING_AUTH] * 4
            + [ConversationStatus.CLOSED] * 4
            + [ConversationStatus.BLOCKED] * 1
        )

        wa_conversations = []
        for i, phone in enumerate(phones_to_use):
            if AgentConversation.objects.filter(whatsapp_phone=phone).exists():
                continue

            status = random.choice(status_pool)
            authenticated = status in (
                ConversationStatus.ACTIVE,
                ConversationStatus.AUTHENTICATED,
                ConversationStatus.CLOSED,
            )
            days_ago = random.randint(0, 30)
            last_interaction = now - timedelta(
                days=days_ago, hours=random.randint(0, 23)
            )

            conv = AgentConversation(
                channel=ChannelType.WHATSAPP,
                whatsapp_phone=phone,
                status=status,
                authenticated=authenticated,
                last_interaction=last_interaction,
            )
            conv.save()
            # Force last_interaction (auto_now=True ignores assignment)
            AgentConversation.objects.filter(pk=conv.pk).update(
                last_interaction=last_interaction
            )
            wa_conversations.append(conv)

        self.stdout.write(self.style.SUCCESS(f"  {len(wa_conversations)} conversaciones WhatsApp creadas."))

        # ── Telegram Conversations ───────────────────────────────────────────
        self.stdout.write("Creando conversaciones Telegram...")
        tg_conversations = []
        for chat_id, username in zip(TELEGRAM_CHAT_IDS, TELEGRAM_USERNAMES):
            if AgentConversation.objects.filter(telegram_chat_id=chat_id).exists():
                continue

            status = random.choice(status_pool)
            authenticated = status in (
                ConversationStatus.ACTIVE,
                ConversationStatus.AUTHENTICATED,
            )
            days_ago = random.randint(1, 60)
            last_interaction = now - timedelta(
                days=days_ago, hours=random.randint(0, 23)
            )
            conv = AgentConversation(
                channel=ChannelType.TELEGRAM,
                telegram_chat_id=chat_id,
                telegram_username=username,
                status=status,
                authenticated=authenticated,
            )
            conv.save()
            AgentConversation.objects.filter(pk=conv.pk).update(
                last_interaction=last_interaction
            )
            tg_conversations.append(conv)

        self.stdout.write(self.style.SUCCESS(f"  {len(tg_conversations)} conversaciones Telegram creadas."))

        # ── Messages ────────────────────────────────────────────────────────
        self.stdout.write("Creando mensajes...")
        all_conversations = wa_conversations + tg_conversations
        total_messages = 0

        delivery_status_pool = (
            [MessageDeliveryStatus.READ] * 55
            + [MessageDeliveryStatus.DELIVERED] * 25
            + [MessageDeliveryStatus.SENT] * 15
            + [MessageDeliveryStatus.FAILED] * 5
        )

        for conv in all_conversations:
            num_messages = random.randint(4, 18)
            conv_start = now - timedelta(days=random.randint(0, 30), hours=random.randint(1, 5))
            message_time = conv_start

            # Opening user message
            ConversationMessage.objects.create(
                conversation=conv,
                sender=MessageSender.USER,
                message=random.choice(["Hola", "Buenas", "Hola buenos días"]),
                intent=IntentType.GREETING,
            )
            total_messages += 1

            # Bot greeting response
            ConversationMessage.objects.create(
                conversation=conv,
                sender=MessageSender.AGENT,
                message=BOT_RESPONSES[0],
                delivery_status=random.choice(delivery_status_pool),
            )
            total_messages += 1

            # Auth exchange if authenticated
            if conv.authenticated:
                ConversationMessage.objects.create(
                    conversation=conv,
                    sender=MessageSender.USER,
                    message="Mi cédula es " + str(random.randint(10000000, 99999999)),
                    intent=IntentType.AUTHENTICATION,
                )
                ConversationMessage.objects.create(
                    conversation=conv,
                    sender=MessageSender.AGENT,
                    message=BOT_RESPONSES[8],
                    delivery_status=random.choice(delivery_status_pool),
                )
                total_messages += 2

            # Remaining messages
            for _ in range(num_messages - 2):
                intent = weighted_choice(INTENT_WEIGHTS)
                user_msg = ConversationMessage.objects.create(
                    conversation=conv,
                    sender=MessageSender.USER,
                    message=random.choice(USER_MESSAGES),
                    intent=intent,
                )
                total_messages += 1

                bot_msg = ConversationMessage.objects.create(
                    conversation=conv,
                    sender=MessageSender.AGENT,
                    message=random.choice(BOT_RESPONSES[1:]),
                    delivery_status=random.choice(delivery_status_pool),
                )
                total_messages += 1

        self.stdout.write(self.style.SUCCESS(f"  {total_messages} mensajes creados."))

        # ── Summary ─────────────────────────────────────────────────────────
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(self.style.SUCCESS("Datos mock creados exitosamente:"))
        self.stdout.write(f"  Conversaciones WhatsApp : {len(wa_conversations)}")
        self.stdout.write(f"  Conversaciones Telegram : {len(tg_conversations)}")
        self.stdout.write(f"  Mensajes totales        : {total_messages}")
        self.stdout.write(f"  Plantillas              : {templates_created}")
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write("Ejecuta: python manage.py seed_chatbot_data --clear  para reiniciar.")
