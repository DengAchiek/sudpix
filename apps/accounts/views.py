from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import FormView, TemplateView

from apps.notifications.models import create_client_registration_notification

from .forms import ClientRegistrationForm, PortalAuthenticationForm, StaffAuthenticationForm


class LoginChoiceView(TemplateView):
    template_name = "accounts/login_choice.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_staff:
                return redirect("dashboard:home")
            return redirect("client:dashboard")
        return super().dispatch(request, *args, **kwargs)


class ClientLoginView(LoginView):
    authentication_form = PortalAuthenticationForm
    template_name = "accounts/client_login.html"
    redirect_authenticated_user = True

    def get_default_redirect_url(self):
        if self.request.user.is_staff:
            return str(reverse_lazy("dashboard:home"))
        return str(reverse_lazy("client:dashboard"))


class AdminLoginView(LoginView):
    authentication_form = StaffAuthenticationForm
    template_name = "accounts/admin_login.html"
    redirect_authenticated_user = True

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_staff:
                return redirect("dashboard:home")
            return redirect("client:dashboard")
        return super().dispatch(request, *args, **kwargs)

    def get_default_redirect_url(self):
        return str(reverse_lazy("dashboard:home"))


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/profile.html"


class LogoutRedirectView(View):
    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect("core:home")

    post = get


class RegisterView(FormView):
    form_class = ClientRegistrationForm
    success_url = reverse_lazy("client:dashboard")
    template_name = "accounts/register.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(self.get_success_url())
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        create_client_registration_notification(user)
        login(self.request, user)
        return super().form_valid(form)
