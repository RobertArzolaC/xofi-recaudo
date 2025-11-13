"""
Dashboard Services
Servicios para calcular métricas y estadísticas del dashboard
"""
import json
from datetime import timedelta
from decimal import Decimal

from django.db.models import (
    Count,
    Q,
    Sum,
    Avg,
    F,
    ExpressionWrapper,
    DecimalField,
    Case,
    When,
    Value,
)
from django.db.models.functions import TruncDate, Coalesce
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


def get_campaigns_by_status_data():
    """
    Obtiene la distribución de campañas por estado.

    Returns:
        dict: Diccionario con labels y data para gráfico pie
    """
    try:
        from apps.campaigns.models import Campaign

        # Agrupar campañas por status
        campaigns = (
            Campaign.objects
            .values('status')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        labels = []
        data = []

        for campaign in campaigns:
            status_display = campaign['status'].replace('_', ' ').title()
            labels.append(status_display)
            data.append(campaign['count'])

        return {
            'labels': json.dumps(labels),
            'data': json.dumps(data),
        }
    except Exception as e:
        # Si hay error, retornar datos vacíos
        return {
            'labels': json.dumps([]),
            'data': json.dumps([]),
        }


def get_campaigns_by_channel_data():
    """
    Obtiene la distribución de campañas por canal de comunicación.

    Returns:
        dict: Diccionario con labels y data para gráfico pie
    """
    try:
        from apps.campaigns.models import Campaign

        # Verificar si el modelo tiene el campo 'channel'
        if not hasattr(Campaign, 'channel'):
            return {
                'labels': json.dumps([]),
                'data': json.dumps([]),
            }

        # Agrupar campañas por canal
        campaigns = (
            Campaign.objects
            .values('channel')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        labels = []
        data = []

        for campaign in campaigns:
            channel_display = campaign['channel'].replace('_', ' ').title()
            labels.append(channel_display)
            data.append(campaign['count'])

        return {
            'labels': json.dumps(labels),
            'data': json.dumps(data),
        }
    except Exception as e:
        # Si hay error, retornar datos vacíos
        return {
            'labels': json.dumps([]),
            'data': json.dumps([]),
        }


def get_payments_by_method_data():
    """
    Obtiene la distribución de pagos por método de pago.

    Returns:
        dict: Diccionario con labels y data para gráfico pie
    """
    try:
        from apps.payments.models import Payment

        # Agrupar pagos por método
        payments = (
            Payment.objects
            .values('payment_method')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        labels = []
        data = []

        for payment in payments:
            method_display = payment['payment_method'].replace('_', ' ').title()
            labels.append(method_display)
            data.append(payment['count'])

        return {
            'labels': json.dumps(labels),
            'data': json.dumps(data),
        }
    except Exception as e:
        return {
            'labels': json.dumps([]),
            'data': json.dumps([]),
        }


def get_payments_timeline_data(days=7):
    """
    Obtiene la cantidad de pagos por día en los últimos N días.

    Args:
        days: Número de días a consultar (default: 7)

    Returns:
        dict: Diccionario con labels y data para gráfico de línea
    """
    try:
        from apps.payments.models import Payment

        today = timezone.now().date()
        start_date = today - timedelta(days=days-1)

        # Agrupar pagos por día
        payments = (
            Payment.objects
            .filter(payment_date__gte=start_date, payment_date__lte=today)
            .annotate(date=TruncDate('payment_date'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )

        # Crear diccionario con todas las fechas
        date_counts = {start_date + timedelta(days=i): 0 for i in range(days)}

        # Llenar con datos reales
        for payment in payments:
            date_counts[payment['date']] = payment['count']

        # Ordenar por fecha
        sorted_dates = sorted(date_counts.items())
        labels = [date.strftime('%d/%m') for date, _ in sorted_dates]
        data = [count for _, count in sorted_dates]

        return {
            'labels': json.dumps(labels),
            'data': json.dumps(data),
        }
    except Exception as e:
        # Retornar datos vacíos para los últimos 7 días
        today = timezone.now().date()
        labels = [(today - timedelta(days=i)).strftime('%d/%m') for i in range(days-1, -1, -1)]
        return {
            'labels': json.dumps(labels),
            'data': json.dumps([0] * days),
        }


def get_credits_by_status_data():
    """
    Obtiene la distribución de créditos por estado.

    Returns:
        dict: Diccionario con labels y data para gráfico pie
    """
    try:
        from apps.credits.models import Credit

        # Agrupar créditos por status
        credits = (
            Credit.objects
            .values('status')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        labels = []
        data = []

        for credit in credits:
            status_display = credit['status'].replace('_', ' ').title()
            labels.append(status_display)
            data.append(credit['count'])

        return {
            'labels': json.dumps(labels),
            'data': json.dumps(data),
        }
    except Exception as e:
        return {
            'labels': json.dumps([]),
            'data': json.dumps([]),
        }


def get_credits_outstanding_trend_data(months=6):
    """
    Obtiene la tendencia de saldo pendiente en los últimos N meses.

    Args:
        months: Número de meses a consultar (default: 6)

    Returns:
        dict: Diccionario con labels y data para gráfico de línea
    """
    try:
        from apps.credits.models import Credit

        # Por ahora retornar datos de ejemplo
        # En producción aquí se consultaría el saldo pendiente por mes
        labels = []
        data = []

        today = timezone.now().date()
        for i in range(months-1, -1, -1):
            month_date = today - timedelta(days=30*i)
            labels.append(month_date.strftime('%b %Y'))

            # Calcular saldo pendiente para ese mes (ejemplo)
            # En producción esto debería calcular el saldo real por mes
            data.append(0)

        return {
            'labels': json.dumps(labels),
            'data': json.dumps(data),
        }
    except Exception as e:
        labels = []
        today = timezone.now().date()
        for i in range(months-1, -1, -1):
            month_date = today - timedelta(days=30*i)
            labels.append(month_date.strftime('%b %Y'))
        return {
            'labels': json.dumps(labels),
            'data': json.dumps([0] * months),
        }


def get_partners_by_type_data():
    """
    Obtiene la distribución de socios por estado.

    Returns:
        dict: Diccionario con labels y data para gráfico pie
    """
    from apps.partners.models import Partner
    from apps.partners import choices

    # Agrupar socios por status
    partners = (
        Partner.objects
        .values('status')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    labels = []
    data = []

    for partner in partners:
        # Obtener el display name del status
        status_value = partner['status']
        try:
            status_display = str(choices.PartnerStatus(status_value).label)
        except (ValueError, AttributeError):
            status_display = f"Status {status_value}"
        labels.append(status_display)
        data.append(partner['count'])

    return {
        'labels': json.dumps(labels),
        'data': json.dumps(data),
    }


def get_partners_activity_data():
    """
    Obtiene la actividad de socios (ejemplo: pagos recientes).

    Returns:
        dict: Diccionario con labels y data para gráfico de barras
    """
    try:
        from apps.partners.models import Partner

        # Obtener top 10 socios con más actividad (ejemplo: más pagos)
        partners = (
            Partner.objects
            .annotate(payment_count=Count('payments'))
            .order_by('-payment_count')[:10]
        )

        labels = []
        data = []

        for partner in partners:
            labels.append(partner.full_name[:20])  # Limitar a 20 caracteres
            data.append(partner.payment_count)

        return {
            'labels': json.dumps(labels),
            'data': json.dumps(data),
        }
    except Exception as e:
        return {
            'labels': json.dumps([]),
            'data': json.dumps([]),
        }


def get_tickets_by_status_data():
    """
    Obtiene la distribución de tickets de soporte por estado.

    Returns:
        dict: Diccionario con labels y data para gráfico pie
    """
    try:
        from apps.support.models import Ticket
        from apps.support import choices

        # Agrupar tickets por status
        tickets = (
            Ticket.objects
            .values('status')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        labels = []
        data = []

        for ticket in tickets:
            status_value = ticket['status']
            try:
                status_display = str(choices.TicketStatus(status_value).label)
            except (ValueError, AttributeError):
                status_display = f"Status {status_value}"
            labels.append(status_display)
            data.append(ticket['count'])

        return {
            'labels': json.dumps(labels),
            'data': json.dumps(data),
        }
    except Exception as e:
        return {
            'labels': json.dumps([]),
            'data': json.dumps([]),
        }


def get_tickets_timeline_data(days=7):
    """
    Obtiene la cantidad de tickets creados por día en los últimos N días.

    Args:
        days: Número de días a consultar (default: 7)

    Returns:
        dict: Diccionario con labels y data para gráfico de línea
    """
    try:
        from apps.support.models import Ticket

        today = timezone.now().date()
        start_date = today - timedelta(days=days-1)

        # Agrupar tickets por día de creación
        tickets = (
            Ticket.objects
            .filter(created_at__date__gte=start_date, created_at__date__lte=today)
            .annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )

        # Crear diccionario con todas las fechas
        date_counts = {start_date + timedelta(days=i): 0 for i in range(days)}

        # Llenar con datos reales
        for ticket in tickets:
            date_counts[ticket['date']] = ticket['count']

        # Ordenar por fecha
        sorted_dates = sorted(date_counts.items())
        labels = [date.strftime('%d/%m') for date, _ in sorted_dates]
        data = [count for _, count in sorted_dates]

        return {
            'labels': json.dumps(labels),
            'data': json.dumps(data),
        }
    except Exception as e:
        # Retornar datos vacíos para los últimos 7 días
        today = timezone.now().date()
        labels = [(today - timedelta(days=i)).strftime('%d/%m') for i in range(days-1, -1, -1)]
        return {
            'labels': json.dumps(labels),
            'data': json.dumps([0] * days),
        }


def get_dashboard_kpis():
    """
    Obtiene los KPIs principales del dashboard.

    Returns:
        dict: Diccionario con los KPIs principales
    """
    try:
        from apps.campaigns.models import Campaign
        from apps.payments.models import Payment
        from apps.credits.models import Credit
        from apps.support.models import Ticket

        today = timezone.now().date()
        this_month = today.replace(day=1)
        three_months_ago = today - timedelta(days=90)

        # Contar campañas activas
        try:
            active_campaigns_count = Campaign.objects.filter(
                status='ACTIVE'
            ).count()
        except Exception:
            active_campaigns_count = 0

        # Contar campañas completadas
        try:
            completed_campaigns_count = Campaign.objects.filter(
                status='COMPLETED'
            ).count()
        except Exception:
            completed_campaigns_count = 0

        # Contar pagos completados este mes
        try:
            completed_payments_count = Payment.objects.filter(
                payment_date__gte=this_month,
                status='PAID'
            ).count()
        except Exception:
            completed_payments_count = 0

        # Contar créditos activos
        try:
            active_credits_count = Credit.objects.filter(
                status='ACTIVE'
            ).count()
        except Exception:
            active_credits_count = 0

        # Contar tickets abiertos (OPEN=1, IN_PROGRESS=2)
        try:
            open_tickets_count = Ticket.objects.filter(
                status__in=[1, 2]
            ).count()
        except Exception:
            open_tickets_count = 0

        # Calcular total recolectado en últimos 3 meses
        try:
            total_collected = Payment.objects.filter(
                payment_date__gte=three_months_ago,
                status='PAID'
            ).aggregate(
                total=Coalesce(Sum('amount'), Decimal('0.00'))
            )['total']
        except Exception:
            total_collected = Decimal('0.00')

        # Calcular tasa de cobranza (ejemplo simple)
        # En producción esto sería más complejo
        collection_rate = Decimal('0.00')

        return {
            'active_campaigns_count': active_campaigns_count,
            'completed_campaigns_count': completed_campaigns_count,
            'completed_payments_count': completed_payments_count,
            'active_credits_count': active_credits_count,
            'open_tickets_count': open_tickets_count,
            'total_collected': f'S/ {total_collected:,.2f}',
            'collection_rate': f'{collection_rate:.1f}%',
        }
    except Exception as e:
        # Si todo falla, retornar valores por defecto
        return {
            'active_campaigns_count': 0,
            'completed_campaigns_count': 0,
            'completed_payments_count': 0,
            'active_credits_count': 0,
            'open_tickets_count': 0,
            'total_collected': 'S/ 0.00',
            'collection_rate': '0.0%',
        }
