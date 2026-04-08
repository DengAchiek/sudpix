from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from .forms import PortalPasswordResetForm, PortalSetPasswordForm
from .views import (
    AdminLoginView,
    ClientLoginView,
    LoginChoiceView,
    LogoutRedirectView,
    ProfileView,
    RegisterView,
)

app_name = "accounts"

urlpatterns = [
    path("admin-login/", AdminLoginView.as_view(), name="admin_login"),
    path("client-login/", ClientLoginView.as_view(), name="client_login"),
    path("login/", LoginChoiceView.as_view(), name="login"),
    path("register/", RegisterView.as_view(), name="register"),
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="accounts/password_reset_form.html",
            email_template_name="accounts/password_reset_email.txt",
            subject_template_name="accounts/password_reset_subject.txt",
            form_class=PortalPasswordResetForm,
            success_url=reverse_lazy("accounts:password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="accounts/password_reset_done.html",
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html",
            form_class=PortalSetPasswordForm,
            success_url=reverse_lazy("accounts:password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),
    path("logout/", LogoutRedirectView.as_view(), name="logout"),
    path("profile/", ProfileView.as_view(), name="profile"),
]
