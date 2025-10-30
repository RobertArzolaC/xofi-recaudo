from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.payments import api, views, viewsets

app_name = "apps.payments"

# API Router
router = DefaultRouter()
router.register(r"receipts", viewsets.PaymentReceiptViewSet, basename="receipt")

# Main URLs for payments module
urlpatterns = [
    # API URLs - Router
    path("api/", include(router.urls)),
    # Payment CRUD views
    path("payments/", views.PaymentListView.as_view(), name="payment-list"),
    path(
        "payment/create/",
        views.PaymentCreateView.as_view(),
        name="payment-create",
    ),
    path(
        "payment/<int:pk>/",
        views.PaymentDetailView.as_view(),
        name="payment-detail",
    ),
    path(
        "payment/<int:pk>/edit/",
        views.PaymentUpdateView.as_view(),
        name="payment-edit",
    ),
    path(
        "payment/<int:pk>/delete/",
        views.PaymentDeleteView.as_view(),
        name="payment-delete",
    ),
    # Payment Receipt CRUD views
    path(
        "receipts/",
        views.PaymentReceiptListView.as_view(),
        name="payment-receipt-list",
    ),
    path(
        "receipt/create/",
        views.PaymentReceiptCreateView.as_view(),
        name="payment-receipt-create",
    ),
    path(
        "receipt/<int:pk>/",
        views.PaymentReceiptDetailView.as_view(),
        name="payment-receipt-detail",
    ),
    path(
        "receipt/<int:pk>/edit/",
        views.PaymentReceiptUpdateView.as_view(),
        name="payment-receipt-edit",
    ),
    path(
        "receipt/<int:pk>/delete/",
        views.PaymentReceiptDeleteView.as_view(),
        name="payment-receipt-delete",
    ),
    # Magic Payment Link views
    path(
        "magic-links/",
        views.MagicPaymentLinkListView.as_view(),
        name="magic-link-list",
    ),
    path(
        "magic-link/create/",
        views.MagicPaymentLinkCreateView.as_view(),
        name="magic-link-create",
    ),
    path(
        "magic-link/<int:pk>/",
        views.MagicPaymentLinkDetailView.as_view(),
        name="magic-link-detail",
    ),
    # Public Magic Payment Link view (short URL)
    path(
        "s/<str:token>/",
        views.MagicPaymentLinkPublicView.as_view(),
        name="magic-link-public",
    ),
    # API URLs
    path(
        "api/",
        include(
            [
                # Partner payment summary and pending debts
                path(
                    "partner-summary/<int:pk>/",
                    api.PartnerPaymentSummaryAPIView.as_view(),
                    name="api-partner-summary",
                ),
                # Payment concept allocation
                path(
                    "allocations/create/",
                    api.PaymentConceptAllocationCreateAPIView.as_view(),
                    name="api-allocation-create",
                ),
                path(
                    "allocations/",
                    api.PaymentConceptAllocationListAPIView.as_view(),
                    name="api-allocation-list",
                ),
                path(
                    "allocations/payment/<int:payment_id>/",
                    api.PaymentConceptAllocationListAPIView.as_view(),
                    name="api-allocation-by-payment",
                ),
                # Payment processing
                path(
                    "process/",
                    api.ProcessPaymentAPIView.as_view(),
                    name="api-process-payment",
                ),
                # Auto allocation
                path(
                    "<int:pk>/auto-allocate/",
                    api.AutoAllocatePaymentAPIView.as_view(),
                    name="api-auto-allocate",
                ),
                # Payment search and statistics
                path(
                    "search/",
                    api.PaymentSearchAPIView.as_view(),
                    name="api-payment-search",
                ),
                path(
                    "statistics/",
                    api.PaymentStatisticsAPIView.as_view(),
                    name="api-payment-statistics",
                ),
            ]
        ),
    ),
]
