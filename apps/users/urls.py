from django.urls import path

from apps.users import api, views

app_name = "apps.users"

urlpatterns = [
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("settings/", views.SettingsView.as_view(), name="settings"),
    # User Management URLs
    path("users/", views.UserListView.as_view(), name="user-list"),
    path("users/create/", views.UserCreateView.as_view(), name="user-create"),
    path("users/<int:pk>/", views.UserDetailView.as_view(), name="user-detail"),
    path(
        "users/<int:pk>/edit/", views.UserUpdateView.as_view(), name="user-edit"
    ),
    path(
        "users/<int:pk>/roles/",
        views.UserRolesView.as_view(),
        name="user-roles",
    ),
    path(
        "users/<int:pk>/permissions/",
        views.UserPermissionsView.as_view(),
        name="user-permissions",
    ),
    # Role URLs
    path("roles/", views.RoleListView.as_view(), name="role-list"),
    path("roles/create/", views.RoleCreateView.as_view(), name="role-create"),
    path("roles/<int:pk>/", views.RoleDetailView.as_view(), name="role-detail"),
    path(
        "roles/<int:pk>/edit/", views.RoleUpdateView.as_view(), name="role-edit"
    ),
    path(
        "roles/<int:pk>/delete/",
        views.RoleDeleteView.as_view(),
        name="role-delete",
    ),
    path(
        "roles/<int:pk>/permissions/",
        views.RolePermissionsView.as_view(),
        name="role-permissions",
    ),
    # API URLs
    path(
        "api/toggle-user-status/",
        api.ToggleUserStatusView.as_view(),
        name="toggle_user_status_api",
    ),
    path(
        "api/upload-avatar/",
        api.UploadAvatarView.as_view(),
        name="upload_avatar_api",
    ),
    path(
        "api/verify-email/",
        api.VerifyEmailView.as_view(),
        name="verify_email_api",
    ),
]
