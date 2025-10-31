from rest_framework.routers import DefaultRouter

from apps.partners import viewsets

app_name = "partners_api"

# API Router
router = DefaultRouter()
router.register(r"partners", viewsets.PartnerViewSet, basename="partner")

urlpatterns = router.urls
