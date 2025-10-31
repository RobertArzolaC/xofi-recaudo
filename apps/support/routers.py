from rest_framework.routers import DefaultRouter

from apps.support import viewsets

app_name = "support_api"

# API Router
router = DefaultRouter()
router.register(r"tickets", viewsets.TicketViewSet, basename="ticket-api")

urlpatterns = router.urls
