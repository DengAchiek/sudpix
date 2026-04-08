from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordResetForm,
    SetPasswordForm,
    UserCreationForm,
)
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.projects.models import ensure_client_upload_folder


class PortalAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="Username or email",
        widget=forms.TextInput(
            attrs={
                "class": "w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 placeholder:text-muted focus:border-accent focus:outline-none",
                "placeholder": "your username or email",
                "autofocus": True,
            }
        ),
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 placeholder:text-muted focus:border-accent focus:outline-none",
                "placeholder": "Enter your password",
            }
        ),
    )

    def clean(self):
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if username and password:
            lookup_value = username.strip()
            user_model = get_user_model()

            if "@" in lookup_value:
                matched_users = list(
                    user_model._default_manager.filter(
                    email__iexact=lookup_value
                    )
                )
                if len(matched_users) > 1:
                    raise ValidationError(
                        "Multiple accounts use this email address. Please log in with your username instead.",
                    )
                if matched_users:
                    lookup_value = getattr(matched_users[0], user_model.USERNAME_FIELD)

            self.user_cache = authenticate(
                self.request,
                username=lookup_value,
                password=password,
            )

            if self.user_cache is None:
                raise ValidationError(
                    self.error_messages["invalid_login"],
                    code="invalid_login",
                    params={"username": self.username_field.verbose_name},
                )

            self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data


class StaffAuthenticationForm(PortalAuthenticationForm):
    def clean(self):
        cleaned_data = super().clean()

        if self.user_cache and not self.user_cache.is_staff:
            raise ValidationError("This login is reserved for SudPix administrators only.")

        return cleaned_data


class ClientRegistrationForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 placeholder:text-muted focus:border-accent focus:outline-none",
                "placeholder": "First name",
            }
        ),
    )
    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 placeholder:text-muted focus:border-accent focus:outline-none",
                "placeholder": "Last name",
            }
        ),
    )
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 placeholder:text-muted focus:border-accent focus:outline-none",
                "placeholder": "Choose a username",
            }
        ),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "class": "w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 placeholder:text-muted focus:border-accent focus:outline-none",
                "placeholder": "you@example.com",
            }
        )
    )
    password1 = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 placeholder:text-muted focus:border-accent focus:outline-none",
                "placeholder": "Create a password",
            }
        ),
    )
    password2 = forms.CharField(
        label=_("Confirm password"),
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 placeholder:text-muted focus:border-accent focus:outline-none",
                "placeholder": "Repeat your password",
            }
        ),
    )

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("first_name", "last_name", "username", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        user_model = get_user_model()

        if user_model._default_manager.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email already exists.")

        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]

        if commit:
            user.save()
            ensure_client_upload_folder(user)

        return user


class PortalPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "class": "w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 placeholder:text-muted focus:border-accent focus:outline-none",
                "placeholder": "you@example.com",
                "autofocus": True,
            }
        )
    )


class PortalSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["new_password1"].widget.attrs.update(
            {
                "class": "w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 placeholder:text-muted focus:border-accent focus:outline-none",
                "placeholder": "Create a new password",
            }
        )
        self.fields["new_password2"].widget.attrs.update(
            {
                "class": "w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 placeholder:text-muted focus:border-accent focus:outline-none",
                "placeholder": "Repeat your new password",
            }
        )
