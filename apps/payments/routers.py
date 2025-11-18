from rest_framework.routers import DefaultRouter

from apps.payments import viewsets

app_name = "payments_api"

router = DefaultRouter()
router.register(
    r"payments-receipts",
    viewsets.PaymentReceiptViewSet,
    basename="payment-receipt",
)

urlpatterns = router.urls
