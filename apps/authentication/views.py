from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import CreateView, TemplateView
from django.views.decorators.csrf import csrf_exempt

from apps.authentication import forms


@method_decorator(csrf_exempt, name="dispatch")
class ChangePasswordView(View):
    def post(self, request, *args, **kwargs):
        form = PasswordChangeForm(request.user, request.POST)
        response = {"status": "error", "errors": {}}

        if not form.is_valid():
            return JsonResponse(response, status=400)

        user = form.save()
        update_session_auth_hash(request, user)
        return JsonResponse(
            {"status": "success", "message": "Password changed successfully."}
        )


@method_decorator(csrf_exempt, name="dispatch")
class DeactivateAccountView(View):
    def post(self, request, *args, **kwargs):
        form = forms.DeactivateAccountForm(request.POST)
        response = {"status": "error", "errors": {}}

        if not form.is_valid():
            return JsonResponse(response, status=400)

        user = form.save()
        user.is_active = False
        user.save()
        return JsonResponse(
            {"status": "success", "message": "Account deactivated successfully."}
        )


class ProspectRegistrationView(CreateView):
    template_name = "account/prospect_register.html"
    form_class = forms.ProspectRegistrationForm
    success_url = reverse_lazy("apps.authentication:prospect_register_success")

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.ip_address = self.request.META.get("REMOTE_ADDR")
        self.object.user_agent = self.request.META.get("HTTP_USER_AGENT")
        self.object.source = "landing_page_registration"
        self.object.save()
        return super().form_valid(form)


class ProspectRegistrationSuccessView(TemplateView):
    template_name = "account/prospect_register_success.html"
