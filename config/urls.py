from allauth.account.views import LoginView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.core import views as core_views

handler404 = core_views.Error404View.as_view()
handler500 = core_views.Error500View.as_view()
handler403 = core_views.Error403View.as_view()

urlpatterns = [
    path("admin/", admin.site.urls),
    path("authentication/", include("allauth.urls")),
    path("", LoginView.as_view(), name="account_login"),
]

urlpatterns += [
    path("core/", include("apps.core.urls")),
    path("users/", include("apps.users.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
    path("customers/", include("apps.customers.urls")),
    path("authentication/", include("apps.authentication.urls")),
    path("partners/", include("apps.partners.urls")),
    path("team/", include("apps.team.urls")),
    path("credits/", include("apps.credits.urls")),
    path("payments/", include("apps.payments.urls")),
    path("compliance/", include("apps.compliance.urls")),
    path("campaigns/", include("apps.campaigns.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT
    )

    from debug_toolbar.toolbar import debug_toolbar_urls  # noqa

    urlpatterns += debug_toolbar_urls()

    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]
