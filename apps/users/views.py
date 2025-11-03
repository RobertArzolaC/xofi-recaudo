from django.contrib import messages
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
)
from django.contrib.auth.models import Group, Permission
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
    View,
)
from django_filters.views import FilterView

from apps.customers import forms as customer_forms
from apps.users import filtersets, forms, models


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "users/profile.html"
    paginate_by = 6

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity"] = _("Profile")
        context["back_url"] = reverse_lazy("apps.dashboard:index")

        return context


class SettingsView(SuccessMessageMixin, LoginRequiredMixin, View):
    template_name = "users/settings.html"
    success_message = _("Settings updated successfully")
    success_url = reverse_lazy("apps.users:settings")

    def get_context_data(self, **kwargs):
        user = self.request.user

        context = {
            "entity": _("Settings"),
            "back_url": reverse_lazy("apps.dashboard:index"),
            "user_form": forms.UserSettingsForm(instance=user),
        }

        if user.is_account:
            context["account_form"] = customer_forms.AccountSettingsForm(
                instance=user.account
            )

        context.update(kwargs)
        return context

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data())

    def post(self, request, *args, **kwargs):
        try:
            user = request.user

            user_form = forms.UserSettingsForm(
                request.POST, request.FILES, instance=user
            )
            if user_form.is_valid():
                user_form.save()

            if user.is_account:
                customer_form = customer_forms.AccountSettingsForm(
                    request.POST, request.FILES, instance=user.account
                )

                if customer_form.is_valid():
                    customer_form.save()

            messages.success(request, self.success_message)
            return redirect(self.success_url)
        except Exception as e:
            messages.error(request, f"Error updating settings: {str(e)}")

        return render(request, self.template_name, self.get_context_data())


class UserListView(LoginRequiredMixin, PermissionRequiredMixin, FilterView):
    """List view for users with their assigned roles and filtering."""

    model = models.User
    template_name = "users/user/list.html"
    context_object_name = "users"
    permission_required = "auth.view_user"
    paginate_by = 5
    filterset_class = filtersets.UserFilter

    def get_queryset(self):
        """Return all users with prefetched groups, excluding superusers."""
        return (
            models.User.objects.filter(is_superuser=False)
            .prefetch_related("groups")
            .order_by("-date_joined")
        )


class UserDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Detail view for user showing assigned roles and permissions."""

    model = models.User
    template_name = "users/user/detail.html"
    context_object_name = "user_obj"
    permission_required = "auth.view_user"

    def get_queryset(self):
        """Return queryset with prefetched groups and permissions."""
        return models.User.objects.prefetch_related(
            "groups__permissions", "user_permissions"
        )

    def get_context_data(self, **kwargs):
        """Add role and permission information to context."""
        context = super().get_context_data(**kwargs)

        # Get all permissions from roles
        role_permissions = set()
        for group in self.object.groups.all():
            role_permissions.update(group.permissions.all())

        # Get direct permissions
        direct_permissions = set(self.object.user_permissions.all())

        # Combine all permissions
        all_permissions = role_permissions.union(direct_permissions)

        # Organize permissions by app and model
        permissions_by_app = {}
        for permission in all_permissions:
            app_label = permission.content_type.app_label
            model_class = permission.content_type.model_class()
            if model_class:
                model_verbose_name = str(
                    model_class._meta.verbose_name_plural.title()
                )
            else:
                model_verbose_name = permission.content_type.model.title()

            if app_label not in permissions_by_app:
                permissions_by_app[app_label] = {}

            if model_verbose_name not in permissions_by_app[app_label]:
                permissions_by_app[app_label][model_verbose_name] = []

            permissions_by_app[app_label][model_verbose_name].append(permission)

        context["permissions_by_app"] = permissions_by_app
        context["total_permissions"] = len(all_permissions)

        return context


class UserCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Create view for user."""

    model = models.User
    form_class = forms.UserCreateForm
    template_name = "users/user/form.html"
    permission_required = "auth.add_user"

    def form_valid(self, form: forms.UserCreateForm):
        """Save user and assign roles."""
        response = super().form_valid(form)
        # Roles are assigned through the form's save method
        return response

    def get_success_url(self) -> str:
        """Return success URL pointing to detail view."""
        return reverse_lazy(
            "apps.users:user-detail", kwargs={"pk": self.object.pk}
        )

    def get_context_data(self, **kwargs):
        """Add extra context to template."""
        context = super().get_context_data(**kwargs)
        context["title"] = "Create User"
        context["action"] = "create"
        return context


class UserUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Update view for user."""

    model = models.User
    form_class = forms.UserUpdateForm
    template_name = "users/user/form.html"
    permission_required = "auth.change_user"

    def get_success_url(self) -> str:
        """Return success URL pointing to detail view."""
        return reverse_lazy(
            "apps.users:user-detail", kwargs={"pk": self.object.pk}
        )

    def get_context_data(self, **kwargs):
        """Add extra context to template."""
        context = super().get_context_data(**kwargs)
        context["title"] = (
            f"Edit User: {self.object.get_full_name() or self.object.email}"
        )
        context["action"] = "update"
        return context


class UserRolesView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """View for managing roles assigned to a user."""

    model = models.User
    form_class = forms.UserRolesForm
    template_name = "users/user/roles.html"
    permission_required = "auth.change_user"

    def get_success_url(self) -> str:
        """Return success URL pointing to detail view."""
        return reverse_lazy(
            "apps.users:user-detail", kwargs={"pk": self.object.pk}
        )

    def get_context_data(self, **kwargs):
        """Add available roles to context."""
        base_title = _("Manage Roles")
        context = super().get_context_data(**kwargs)
        context["title"] = (
            f"{base_title}: {self.object.get_full_name() or self.object.email}"
        )
        context["all_roles"] = Group.objects.all().order_by("name")
        context["current_roles"] = set(
            self.object.groups.values_list("id", flat=True)
        )
        return context


class UserToggleActiveView(
    LoginRequiredMixin, PermissionRequiredMixin, UpdateView
):
    """View for toggling user active status."""

    model = models.User
    fields = ["is_active"]
    permission_required = "auth.change_user"
    success_url = reverse_lazy("apps.users:user-list")

    def form_valid(self, form):
        """Toggle is_active status."""
        self.object.is_active = not self.object.is_active
        self.object.save()
        return HttpResponse(status=200)


class UserPermissionsView(
    LoginRequiredMixin, PermissionRequiredMixin, UpdateView
):
    """View for managing direct permissions assigned to a user."""

    model = models.User
    form_class = forms.UserPermissionsForm
    template_name = "users/user/permissions.html"
    permission_required = "auth.change_user"

    def get_success_url(self) -> str:
        """Return success URL pointing to detail view."""
        return reverse_lazy(
            "apps.users:user-detail", kwargs={"pk": self.object.pk}
        )

    # Apps to exclude from permission selection

    def get_context_data(self, **kwargs):
        """Add permissions organized by app and model to context."""
        base_title = _("Manage Permissions")
        context = super().get_context_data(**kwargs)
        context["title"] = (
            f"{base_title}: {self.object.get_full_name() or self.object.email}"
        )

        # Get all permissions organized by app and model, excluding system apps
        all_permissions = (
            Permission.objects.select_related("content_type")
            .order_by(
                "content_type__app_label", "content_type__model", "codename"
            )
            .exclude(content_type__app_label__in=self.get_excluded_apps())
            .exclude(content_type__model__in=["reportfilter", "reporttype"])
        )

        permissions_structure = {}
        for permission in all_permissions:
            app_label = permission.content_type.app_label
            model_class = permission.content_type.model_class()
            if model_class:
                model_verbose_name = str(
                    model_class._meta.verbose_name_plural.title()
                )
            else:
                model_verbose_name = permission.content_type.model.title()

            if app_label not in permissions_structure:
                permissions_structure[app_label] = {}

            if model_verbose_name not in permissions_structure[app_label]:
                permissions_structure[app_label][model_verbose_name] = []

            permissions_structure[app_label][model_verbose_name].append(
                permission
            )

        context["permissions_structure"] = permissions_structure
        context["current_permissions"] = set(
            self.object.user_permissions.values_list("id", flat=True)
        )

        return context

    def get_excluded_apps(self) -> list:
        """Return the list of excluded apps."""
        return [
            "authtoken",
            "auth",
            "cities_light",
            "django_celery_beat",
            "admin",
            "contenttypes",
            "sessions",
            "sites",
            "account",
            "socialaccount",
            "constance",
            "easyaudit",
            "core",
        ]


# ------------------------------------------------------------------------------
# Role Management Views
# ------------------------------------------------------------------------------


class RoleListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """List view for roles (Groups)."""

    model = Group
    template_name = "users/role/list.html"
    context_object_name = "roles"
    permission_required = "auth.view_group"
    paginate_by = 5

    def get_queryset(self):
        """Return all groups ordered by name."""
        return Group.objects.prefetch_related("permissions").order_by("name")


class RoleDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Detail view for role (Group) showing assigned permissions."""

    model = Group
    template_name = "users/role/detail.html"
    context_object_name = "role"
    permission_required = "auth.view_group"

    def get_queryset(self):
        """Return queryset with prefetched permissions."""
        return Group.objects.prefetch_related("permissions__content_type")

    def get_context_data(self, **kwargs):
        """Add permission categorization to context."""
        context = super().get_context_data(**kwargs)

        # Organize permissions by content type
        permissions_by_app = {}
        for permission in self.object.permissions.all():
            app_label = permission.content_type.app_label
            # Get the model class to access verbose_name
            model_class = permission.content_type.model_class()
            if model_class:
                model_verbose_name = str(
                    model_class._meta.verbose_name_plural.title()
                )
            else:
                model_verbose_name = permission.content_type.model.title()

            if app_label not in permissions_by_app:
                permissions_by_app[app_label] = {}

            if model_verbose_name not in permissions_by_app[app_label]:
                permissions_by_app[app_label][model_verbose_name] = []

            permissions_by_app[app_label][model_verbose_name].append(permission)

        context["permissions_by_app"] = permissions_by_app
        return context


class RoleCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Create view for role (Group)."""

    model = Group
    form_class = forms.RoleForm
    template_name = "users/role/form.html"
    permission_required = "auth.add_group"

    def get_success_url(self) -> str:
        """Return success URL pointing to detail view."""
        return reverse_lazy(
            "apps.users:role-detail", kwargs={"pk": self.object.pk}
        )

    def get_context_data(self, **kwargs):
        """Add extra context to template."""
        context = super().get_context_data(**kwargs)
        context["title"] = "Create Role"
        context["action"] = "create"
        return context


class RoleUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Update view for role (Group)."""

    model = Group
    form_class = forms.RoleForm
    template_name = "users/role/form.html"
    permission_required = "auth.change_group"

    def get_success_url(self) -> str:
        """Return success URL pointing to detail view."""
        return reverse_lazy(
            "apps.users:role-detail", kwargs={"pk": self.object.pk}
        )

    def get_context_data(self, **kwargs):
        """Add extra context to template."""
        context = super().get_context_data(**kwargs)
        context["title"] = f"Edit Role: {self.object.name}"
        context["action"] = "update"
        return context


class RoleDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Delete view for role (Group)."""

    model = Group
    template_name = "users/role/confirm_delete.html"
    context_object_name = "role"
    permission_required = "auth.delete_group"
    success_url = reverse_lazy("apps.users:role-list")

    def get_context_data(self, **kwargs):
        """Add extra context to template."""
        context = super().get_context_data(**kwargs)
        context["title"] = f"Delete Role: {self.object.name}"
        return context


class RolePermissionsView(
    LoginRequiredMixin, PermissionRequiredMixin, UpdateView
):
    """View for managing permissions assigned to a role."""

    model = Group
    form_class = forms.RolePermissionsForm
    template_name = "users/role/permissions.html"
    permission_required = "auth.change_group"

    def get_success_url(self) -> str:
        """Return success URL pointing to detail view."""
        return reverse_lazy(
            "apps.users:role-detail", kwargs={"pk": self.object.pk}
        )

    def get_context_data(self, **kwargs):
        """Add permissions organized by app and model to context."""
        base_title = _("Manage Permissions")
        context = super().get_context_data(**kwargs)
        context["title"] = f"{base_title}: {self.object.name}"

        # Apps to exclude from permission selection
        excluded_apps = [
            "authtoken",
            "cities_light",
            "django_celery_beat",
            "admin",
            "contenttypes",
            "sessions",
            "sites",
            "account",
            "socialaccount",
            "constance",
            "easyaudit",
            "auth",
            "core",
        ]

        # Get all permissions organized by app and model, excluding system apps
        all_permissions = (
            Permission.objects.select_related("content_type")
            .order_by(
                "content_type__app_label", "content_type__model", "codename"
            )
            .exclude(content_type__app_label__in=excluded_apps)
            .exclude(content_type__model__in=["reportfilter", "reporttype"])
        )

        permissions_structure = {}
        for permission in all_permissions:
            app_label = permission.content_type.app_label
            model_class = permission.content_type.model_class()
            if model_class:
                model_verbose_name = str(
                    model_class._meta.verbose_name_plural.title()
                )
            else:
                model_verbose_name = permission.content_type.model.title()

            if app_label not in permissions_structure:
                permissions_structure[app_label] = {}

            if model_verbose_name not in permissions_structure[app_label]:
                permissions_structure[app_label][model_verbose_name] = []

            permissions_structure[app_label][model_verbose_name].append(
                permission
            )

        context["permissions_structure"] = permissions_structure
        context["current_permissions"] = set(
            self.object.permissions.values_list("id", flat=True)
        )

        return context
