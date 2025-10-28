from django.urls import include, path

from apps.payments import api, views

app_name = "apps.payments"

# Main URLs for payments module
urlpatterns = [
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
