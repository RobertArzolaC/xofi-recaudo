from django.db.models import Sum, Count, Q, Avg, F, Case, When, DecimalField, OuterRef, Subquery, Value
from django.db.models.functions import Coalesce, TruncMonth
from django.utils import timezone
from django.views.generic import TemplateView
from datetime import timedelta, datetime
from decimal import Decimal

from apps.core.mixins import CacheMixin
from apps.credits.models import Credit, Installment, Product
from apps.payments.models import Payment, MagicPaymentLink
from apps.partners.models import Partner
from apps.campaigns.models import Campaign, CampaignNotification
from apps.compliance.models import Contribution, SocialSecurity, Penalty


class DashboardView(CacheMixin, TemplateView):
    template_name = "dashboard/index.html"
    cache_timeout = 300

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now()

        # ============================================
        # SECCIÓN 1: KPIs PRINCIPALES
        # ============================================

        # Cartera total activa
        credits_queryset = Credit.objects.filter(status='active')
        total_credits = credits_queryset.count()
        total_portfolio = credits_queryset.aggregate(
            total=Coalesce(Sum('outstanding_balance'), Value(0), output_field=DecimalField())
        )['total'] or Decimal('0')

        # Cartera del mes anterior para comparación
        last_month = today - timedelta(days=30)
        last_month_portfolio = Credit.objects.filter(
            status='active',
            created__lte=last_month
        ).aggregate(
            total=Coalesce(Sum('outstanding_balance'), Value(0), output_field=DecimalField())
        )['total'] or Decimal('0')

        portfolio_change = 0
        if last_month_portfolio > 0:
            portfolio_change = ((total_portfolio - last_month_portfolio) / last_month_portfolio) * 100

        # Cuotas vencidas
        overdue_installments = Installment.objects.filter(
            status='pending',
            due_date__lt=today
        )
        overdue_count = overdue_installments.count()
        overdue_amount = overdue_installments.aggregate(
            total=Coalesce(Sum('installment_amount'), Value(0), output_field=DecimalField())
        )['total'] or Decimal('0')

        # Cuotas vencidas mes anterior
        last_month_overdue = Installment.objects.filter(
            status='pending',
            due_date__lt=last_month,
            due_date__gte=last_month - timedelta(days=30)
        ).aggregate(
            total=Coalesce(Sum('installment_amount'), Value(0), output_field=DecimalField())
        )['total'] or Decimal('0')

        overdue_change = 0
        if last_month_overdue > 0:
            overdue_change = ((overdue_amount - last_month_overdue) / last_month_overdue) * 100

        # Tasa de morosidad
        delinquency_rate = 0
        if total_portfolio > 0:
            delinquency_rate = (overdue_amount / total_portfolio) * 100

        # Recaudación del mes
        payments_month = Payment.objects.filter(
            payment_date__year=today.year,
            payment_date__month=today.month,
            status='completed'
        )
        collected_month = payments_month.aggregate(
            total=Coalesce(Sum('amount'), Value(0), output_field=DecimalField())
        )['total'] or Decimal('0')
        payments_count_month = payments_month.count()

        # Meta mensual (puedes ajustar esto según tu lógica)
        monthly_goal = total_portfolio * Decimal('0.15')  # 15% de la cartera como meta
        goal_percentage = 0
        if monthly_goal > 0:
            goal_percentage = (collected_month / monthly_goal) * 100

        # ============================================
        # SECCIÓN 2: CRÉDITOS Y PRODUCTOS
        # ============================================

        # Créditos por estado
        credit_by_status = Credit.objects.values('status').annotate(
            count=Count('id'),
            total_amount=Coalesce(Sum('amount'), Value(0), output_field=DecimalField())
        ).order_by('-count')

        # Créditos recientes (últimos 30 días)
        credits_recent = Credit.objects.filter(
            application_date__gte=today - timedelta(days=30)
        )
        credits_approved = credits_recent.filter(status__in=['approved', 'active', 'completed']).count()
        credits_rejected = credits_recent.filter(status='rejected').count()
        credits_pending = credits_recent.filter(status='pending').count()

        # Portfolio por producto
        portfolio_by_product = Credit.objects.filter(status='active').values(
            'product__name'
        ).annotate(
            count=Count('id'),
            total_active=Coalesce(Sum('outstanding_balance'), Value(0), output_field=DecimalField()),
            total_disbursed=Coalesce(Sum('amount'), Value(0), output_field=DecimalField())
        ).order_by('-total_active')

        # ============================================
        # SECCIÓN 3: PAGOS Y CANALES
        # ============================================

        # Pagos por método (mes actual)
        payments_by_method = Payment.objects.filter(
            payment_date__year=today.year,
            payment_date__month=today.month,
            status='completed'
        ).values('payment_method').annotate(
            count=Count('id'),
            total=Coalesce(Sum('amount'), Value(0), output_field=DecimalField()),
            average=Avg('amount')
        ).order_by('-total')

        # Links mágicos
        magic_links_total = MagicPaymentLink.objects.count()
        magic_links_used = MagicPaymentLink.objects.filter(status='used').count()
        magic_links_active = MagicPaymentLink.objects.filter(status='active').count()
        magic_links_expired = MagicPaymentLink.objects.filter(status='expired').count()

        # Pagos recientes
        recent_payments = Payment.objects.filter(
            status='completed'
        ).select_related('partner').order_by('-payment_date')[:10]

        # ============================================
        # SECCIÓN 4: MOROSIDAD Y DEUDORES
        # ============================================

        # Top 10 deudores
        overdue_subquery = Installment.objects.filter(
            credit__partner=OuterRef('pk'),
            status='pending',
            due_date__lt=today
        ).values('credit__partner').annotate(
            total_debt=Coalesce(Sum('installment_amount'), Value(0), output_field=DecimalField()),
            installments=Count('id')
        ).values('total_debt', 'installments')

        top_debtors_qs = Partner.objects.filter(
            credits__status='active'
        ).annotate(
            total_overdue=Coalesce(
                Subquery(overdue_subquery.values('total_debt')[:1]),
                Value(0),
                output_field=DecimalField()
            ),
            overdue_installments=Coalesce(
                Subquery(overdue_subquery.values('installments')[:1]),
                Value(0)
            )
        ).filter(
            total_overdue__gt=0
        ).distinct().order_by('-total_overdue')[:10]

        top_debtors = [
            {
                'partner': partner,
                'debt': partner.total_overdue,
                'installments_count': partner.overdue_installments,
                'risk_level': 'high' if partner.total_overdue > 30000 else 'medium' if partner.total_overdue > 10000 else 'low'
            }
            for partner in top_debtors_qs
        ]

        # Distribución por rangos de mora
        mora_ranges = {
            '1-30': overdue_installments.filter(due_date__gte=today - timedelta(days=30)).count(),
            '31-60': overdue_installments.filter(
                due_date__lt=today - timedelta(days=30),
                due_date__gte=today - timedelta(days=60)
            ).count(),
            '61-90': overdue_installments.filter(
                due_date__lt=today - timedelta(days=60),
                due_date__gte=today - timedelta(days=90)
            ).count(),
            '90+': overdue_installments.filter(due_date__lt=today - timedelta(days=90)).count(),
        }

        # Morosidad por región/ciudad
        morosidad_por_region = Partner.objects.filter(
            credits__status='active'
        ).values('city').annotate(
            total_overdue=Coalesce(
                Sum('credits__installments__installment_amount',
                    filter=Q(credits__installments__status='pending',
                            credits__installments__due_date__lt=today)),
                Value(0),
                output_field=DecimalField()
            )
        ).filter(total_overdue__gt=0).order_by('-total_overdue')[:6]

        # ============================================
        # SECCIÓN 5: CAMPAÑAS
        # ============================================

        # Estadísticas de campañas (manejo seguro del campo channel)
        try:
            campaigns_stats = Campaign.objects.aggregate(
                active=Count('id', filter=Q(status='active')),
                sending=Count('id', filter=Q(status='sending')),
                completed=Count('id', filter=Q(status='completed')),
                total_target=Coalesce(Sum('target_amount'), Value(0), output_field=DecimalField())
            )

            # Notificaciones por canal
            notifications_by_channel = CampaignNotification.objects.filter(
                created__gte=today - timedelta(days=30)
            ).values('channel').annotate(
                sent=Count('id', filter=Q(status='sent')),
                failed=Count('id', filter=Q(status='failed')),
                pending=Count('id', filter=Q(status='pending')),
                success_rate=Case(
                    When(sent__gt=0, then=F('sent') * 100.0 / (F('sent') + F('failed') + F('pending'))),
                    default=Value(0),
                    output_field=DecimalField()
                )
            ).order_by('channel')

            # Campañas recientes
            recent_campaigns = Campaign.objects.select_related('group').order_by('-created')[:5]

        except Exception as e:
            # Si hay error con el campo channel, usar datos simulados
            campaigns_stats = {'active': 0, 'sending': 0, 'completed': 0, 'total_target': Decimal('0')}
            notifications_by_channel = []
            recent_campaigns = []

        # ============================================
        # SECCIÓN 6: COMPLIANCE
        # ============================================

        contributions_pending = Contribution.objects.filter(status='pending').aggregate(
            count=Count('id'),
            total=Coalesce(Sum('amount'), Value(0), output_field=DecimalField())
        )

        social_security_pending = SocialSecurity.objects.filter(status='pending').aggregate(
            count=Count('id'),
            total=Coalesce(Sum('amount'), Value(0), output_field=DecimalField())
        )

        penalties_active = Penalty.objects.filter(status='active').aggregate(
            count=Count('id'),
            total=Coalesce(Sum('amount'), Value(0), output_field=DecimalField())
        )

        # ============================================
        # SECCIÓN 7: GRÁFICOS Y TENDENCIAS
        # ============================================

        # Evolución de recaudación (6 meses)
        recaudacion_evolution = []
        for i in range(6, 0, -1):
            month_date = today - timedelta(days=30*i)
            month_payments = Payment.objects.filter(
                status='completed',
                payment_date__year=month_date.year,
                payment_date__month=month_date.month
            ).aggregate(total=Coalesce(Sum('amount'), Value(0), output_field=DecimalField()))

            recaudacion_evolution.append({
                'month': month_date.strftime('%b %Y'),
                'amount': float(month_payments['total'] or 0),
                'goal': float(monthly_goal)
            })

        # Evolución de morosidad (6 meses)
        morosidad_evolution = []
        for i in range(6, 0, -1):
            month_date = today - timedelta(days=30*i)
            month_overdue = Installment.objects.filter(
                status='pending',
                due_date__lt=month_date,
                due_date__gte=month_date - timedelta(days=30)
            ).aggregate(total=Coalesce(Sum('installment_amount'), Value(0), output_field=DecimalField()))

            morosidad_evolution.append({
                'month': month_date.strftime('%b %Y'),
                'amount': float(month_overdue['total'] or 0)
            })

        # ============================================
        # CONTEXTO FINAL
        # ============================================

        context.update({
            "last_updated": today,

            # KPIs Principales
            "total_credits": total_credits,
            "total_portfolio": total_portfolio,
            "portfolio_change": round(portfolio_change, 2),
            "overdue_count": overdue_count,
            "overdue_amount": overdue_amount,
            "overdue_change": round(overdue_change, 2),
            "delinquency_rate": round(delinquency_rate, 2),
            "collected_month": collected_month,
            "payments_count_month": payments_count_month,
            "monthly_goal": monthly_goal,
            "goal_percentage": round(goal_percentage, 1),

            # Créditos
            "credit_by_status": credit_by_status,
            "credits_approved": credits_approved,
            "credits_rejected": credits_rejected,
            "credits_pending": credits_pending,
            "portfolio_by_product": portfolio_by_product,

            # Pagos
            "payments_by_method": payments_by_method,
            "magic_links_total": magic_links_total,
            "magic_links_used": magic_links_used,
            "magic_links_active": magic_links_active,
            "magic_links_expired": magic_links_expired,
            "recent_payments": recent_payments,

            # Morosidad
            "top_debtors": top_debtors,
            "mora_ranges": mora_ranges,
            "morosidad_por_region": morosidad_por_region,

            # Campañas
            "campaigns_stats": campaigns_stats,
            "notifications_by_channel": notifications_by_channel,
            "recent_campaigns": recent_campaigns,

            # Compliance
            "contributions_pending": contributions_pending,
            "social_security_pending": social_security_pending,
            "penalties_active": penalties_active,

            # Gráficos
            "morosidad_evolution": morosidad_evolution,
            "recaudacion_evolution": recaudacion_evolution,
        })

        return context
