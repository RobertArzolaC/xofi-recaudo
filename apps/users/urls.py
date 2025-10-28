from django.urls import path

from apps.users import api, views

app_name = "apps.users"

urlpatterns = [
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("settings/", views.SettingsView.as_view(), name="settings"),
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
