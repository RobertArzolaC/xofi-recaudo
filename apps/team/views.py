from typing import Any

from constance import config
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
)
from django.db.models import QuerySet
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from apps.team import filtersets, forms, models


class AreaListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """List view for Area model."""

    model = models.Area
    filterset_class = filtersets.AreaFilterSet
    template_name = "team/area/list.html"
    context_object_name = "areas"
    permission_required = "team.view_area"
    paginate_by = config.ITEMS_PER_PAGE

    def get_queryset(self) -> QuerySet[models.Area]:
        """Return filtered and ordered queryset."""
        queryset = models.Area.objects.all()

        # Apply filters
        self.filterset = self.filterset_class(self.request.GET, queryset=queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": _("Areas"),
                "subtitle": _("Manage organizational areas"),
                "filterset": self.filterset,
            }
        )
        return context


class AreaDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Detail view for Area model."""

    model = models.Area
    template_name = "team/area/detail.html"
    context_object_name = "area"
    permission_required = "team.view_area"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": _("Area: {name}").format(name=self.object.name),
                "subtitle": _("Area details and information"),
                "employees": models.Employee.objects.filter(position__area=self.object),
            }
        )
        return context


class AreaCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Create view for Area model."""

    model = models.Area
    form_class = forms.AreaForm
    template_name = "team/area/form.html"
    permission_required = "team.add_area"
    success_url = reverse_lazy("apps.team:area-list")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": _("Create Area"),
                "subtitle": _("Add new organizational area"),
                "form_action": "Create",
            }
        )
        return context

    def form_valid(self, form: Any) -> Any:
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class AreaUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Update view for Area model."""

    model = models.Area
    form_class = forms.AreaForm
    template_name = "team/area/form.html"
    permission_required = "team.change_area"
    success_url = reverse_lazy("apps.team:area-list")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": _("Edit Area: {name}").format(name=self.object.name),
                "subtitle": _("Update area information"),
                "form_action": "Update",
            }
        )
        return context

    def form_valid(self, form: Any) -> Any:
        form.instance.modified_by = self.request.user
        return super().form_valid(form)


class AreaDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Delete view for Area model."""

    model = models.Area
    template_name = "team/area/confirm_delete.html"
    context_object_name = "area"
    permission_required = "team.delete_area"
    success_url = reverse_lazy("apps.team:area-list")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": _("Delete Area: {name}").format(name=self.object.name),
                "subtitle": _("Confirm area deletion"),
            }
        )
        return context


class PositionListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """List view for Position model."""

    model = models.Position
    filterset_class = filtersets.PositionFilterSet
    template_name = "team/position/list.html"
    context_object_name = "positions"
    permission_required = "team.view_position"
    paginate_by = config.ITEMS_PER_PAGE

    def get_queryset(self) -> QuerySet[models.Position]:
        """Return filtered and ordered queryset."""
        queryset = models.Position.objects.select_related("area")

        # Apply filters
        self.filterset = self.filterset_class(self.request.GET, queryset=queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": _("Positions"),
                "subtitle": _("Manage organizational positions"),
                "filterset": self.filterset,
            }
        )
        return context


class PositionDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Detail view for Position model."""

    model = models.Position
    template_name = "team/position/detail.html"
    context_object_name = "position"
    permission_required = "team.view_position"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": _("Position: {name}").format(name=self.object.name),
                "subtitle": _("Position details and information"),
            }
        )
        return context


class PositionCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Create view for Position model."""

    model = models.Position
    form_class = forms.PositionForm
    template_name = "team/position/form.html"
    permission_required = "team.add_position"
    success_url = reverse_lazy("apps.team:position-list")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": _("Create Position"),
                "subtitle": _("Add new organizational position"),
                "form_action": _("Create"),
            }
        )
        return context

    def form_valid(self, form: Any) -> Any:
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class PositionUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Update view for Position model."""

    model = models.Position
    form_class = forms.PositionForm
    template_name = "team/position/form.html"
    permission_required = "team.change_position"
    success_url = reverse_lazy("apps.team:position-list")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": _("Edit Position: {name}").format(name=self.object.name),
                "subtitle": _("Update position information"),
                "form_action": _("Update"),
            }
        )
        return context

    def form_valid(self, form: Any) -> Any:
        form.instance.modified_by = self.request.user
        return super().form_valid(form)


class PositionDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Delete view for Position model."""

    model = models.Position
    template_name = "team/position/confirm_delete.html"
    context_object_name = "position"
    permission_required = "team.delete_position"
    success_url = reverse_lazy("apps.team:position-list")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": _("Delete Position: {name}").format(name=self.object.name),
                "subtitle": _("Confirm position deletion"),
            }
        )
        return context


# Employee Views
class EmployeeListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """List view for Employee model."""

    model = models.Employee
    filterset_class = filtersets.EmployeeFilterSet
    template_name = "team/employee/list.html"
    context_object_name = "employees"
    permission_required = "team.view_employee"
    paginate_by = config.ITEMS_PER_PAGE

    def get_queryset(self) -> QuerySet[models.Employee]:
        """Return filtered and ordered queryset."""
        queryset = models.Employee.objects.select_related(
            "position", "position__area", "user"
        )

        # Apply filters
        self.filterset = self.filterset_class(self.request.GET, queryset=queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": _("Employees"),
                "subtitle": _("Manage employees"),
                "filterset": self.filterset,
            }
        )
        return context


class EmployeeDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Detail view for Employee model."""

    model = models.Employee
    template_name = "team/employee/detail.html"
    context_object_name = "employee"
    permission_required = "team.view_employee"

    def get_queryset(self) -> QuerySet[models.Employee]:
        """Return queryset with related objects."""
        return models.Employee.objects.select_related(
            "position", "position__area", "user"
        )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": _("Employee: {first_name} {last_name}").format(
                    first_name=self.object.first_name,
                    last_name=self.object.paternal_last_name,
                ),
                "subtitle": _("Employee details and information"),
            }
        )
        return context


class EmployeeCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Create view for Employee model."""

    model = models.Employee
    form_class = forms.EmployeeForm
    template_name = "team/employee/form.html"
    permission_required = "team.add_employee"
    success_url = reverse_lazy("apps.team:employee-list")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": _("Create Employee"),
                "subtitle": _("Add new employee"),
                "form_action": _("Create"),
            }
        )
        return context

    def form_valid(self, form: Any) -> Any:
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class EmployeeUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Update view for Employee model."""

    model = models.Employee
    form_class = forms.EmployeeForm
    template_name = "team/employee/form.html"
    permission_required = "team.change_employee"
    success_url = reverse_lazy("apps.team:employee-list")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": _("Edit Employee: {first_name} {last_name}").format(
                    first_name=self.object.first_name,
                    last_name=self.object.paternal_last_name,
                ),
                "subtitle": _("Update employee information"),
                "form_action": _("Update"),
            }
        )
        return context

    def form_valid(self, form: Any) -> Any:
        form.instance.modified_by = self.request.user
        return super().form_valid(form)


class EmployeeDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Delete view for Employee model."""

    model = models.Employee
    template_name = "team/employee/confirm_delete.html"
    context_object_name = "employee"
    permission_required = "team.delete_employee"
    success_url = reverse_lazy("apps.team:employee-list")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": _("Delete Employee: {first_name} {last_name}").format(
                    first_name=self.object.first_name,
                    last_name=self.object.paternal_last_name,
                ),
                "subtitle": _("Confirm employee deletion"),
            }
        )
        return context
