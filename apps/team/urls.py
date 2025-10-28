"""
URL patterns for team management module.
"""

from django.urls import path

from apps.team import views

app_name = "apps.team"

urlpatterns = [
    # Area URLs
    path("areas/", views.AreaListView.as_view(), name="area-list"),
    path("area/<int:pk>/", views.AreaDetailView.as_view(), name="area-detail"),
    path("area/create/", views.AreaCreateView.as_view(), name="area-create"),
    path(
        "area/<int:pk>/edit/",
        views.AreaUpdateView.as_view(),
        name="area-update",
    ),
    path(
        "area/<int:pk>/delete/",
        views.AreaDeleteView.as_view(),
        name="area-delete",
    ),
    # Position URLs
    path("positions/", views.PositionListView.as_view(), name="position-list"),
    path(
        "position/<int:pk>/",
        views.PositionDetailView.as_view(),
        name="position-detail",
    ),
    path(
        "position/create/",
        views.PositionCreateView.as_view(),
        name="position-create",
    ),
    path(
        "position/<int:pk>/edit/",
        views.PositionUpdateView.as_view(),
        name="position-update",
    ),
    path(
        "position/<int:pk>/delete/",
        views.PositionDeleteView.as_view(),
        name="position-delete",
    ),
    # Employee URLs
    path("employees/", views.EmployeeListView.as_view(), name="employee-list"),
    path(
        "employee/<int:pk>/",
        views.EmployeeDetailView.as_view(),
        name="employee-detail",
    ),
    path(
        "employee/create/",
        views.EmployeeCreateView.as_view(),
        name="employee-create",
    ),
    path(
        "employee/<int:pk>/edit/",
        views.EmployeeUpdateView.as_view(),
        name="employee-update",
    ),
    path(
        "employee/<int:pk>/delete/",
        views.EmployeeDeleteView.as_view(),
        name="employee-delete",
    ),
]
