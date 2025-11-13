from django.utils import timezone
from django.views.generic import TemplateView

from apps.core.mixins import CacheMixin
from apps.dashboard import services


class DashboardView(CacheMixin, TemplateView):
    template_name = "dashboard/index.html"
    cache_timeout = 300

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now()

        # Obtener KPIs principales
        kpis = services.get_dashboard_kpis()

        # Obtener datos para gráficos de campañas
        campaigns_by_status = services.get_campaigns_by_status_data()
        campaigns_by_channel = services.get_campaigns_by_channel_data()

        # Obtener datos para gráficos de pagos
        payments_by_method = services.get_payments_by_method_data()
        payments_timeline = services.get_payments_timeline_data()

        # Obtener datos para gráficos de créditos
        credits_by_status = services.get_credits_by_status_data()
        credits_outstanding_trend = (
            services.get_credits_outstanding_trend_data()
        )

        # Obtener datos para gráficos de socios
        partners_by_type = services.get_partners_by_type_data()
        partners_activity = services.get_partners_activity_data()

        # Obtener datos para gráficos de soporte
        tickets_by_status = services.get_tickets_by_status_data()
        tickets_timeline = services.get_tickets_timeline_data()

        context.update(
            {
                "last_updated": today,
                # KPIs principales
                "active_campaigns_count": kpis["active_campaigns_count"],
                "completed_campaigns_count": kpis["completed_campaigns_count"],
                "completed_payments_count": kpis["completed_payments_count"],
                "active_credits_count": kpis["active_credits_count"],
                "open_tickets_count": kpis["open_tickets_count"],
                "total_collected": kpis["total_collected"],
                "collection_rate": kpis["collection_rate"],
                # Datos de campañas
                "campaigns_by_status_labels": campaigns_by_status["labels"],
                "campaigns_by_status_data": campaigns_by_status["data"],
                "campaigns_by_channel_labels": campaigns_by_channel["labels"],
                "campaigns_by_channel_data": campaigns_by_channel["data"],
                # Datos de pagos
                "payments_by_method_labels": payments_by_method["labels"],
                "payments_by_method_data": payments_by_method["data"],
                "payments_timeline_labels": payments_timeline["labels"],
                "payments_timeline_data": payments_timeline["data"],
                # Datos de créditos
                "credits_by_status_labels": credits_by_status["labels"],
                "credits_by_status_data": credits_by_status["data"],
                "credits_outstanding_trend_labels": credits_outstanding_trend[
                    "labels"
                ],
                "credits_outstanding_trend_data": credits_outstanding_trend[
                    "data"
                ],
                # Datos de socios
                "partners_by_type_labels": partners_by_type["labels"],
                "partners_by_type_data": partners_by_type["data"],
                "partners_activity_labels": partners_activity["labels"],
                "partners_activity_data": partners_activity["data"],
                # Datos de soporte
                "tickets_by_status_labels": tickets_by_status["labels"],
                "tickets_by_status_data": tickets_by_status["data"],
                "tickets_timeline_labels": tickets_timeline["labels"],
                "tickets_timeline_data": tickets_timeline["data"],
            }
        )

        return context
