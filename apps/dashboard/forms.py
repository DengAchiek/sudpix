from django import forms
from django.contrib.auth import get_user_model

from apps.media_management.forms import (
    ClientChoiceField,
    MultipleFileField,
    ProjectChoiceField,
    ACCEPTED_UPLOAD_TYPES,
    build_media_title,
    infer_media_kind,
    save_uploaded_media_file,
)
from apps.media_management.models import MediaAsset
from apps.projects.models import Project, ensure_client_upload_folder


class StaffMultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

    def get_context(self, name, value, attrs):
        attrs = attrs or {}
        existing_class = attrs.get("class", "")
        attrs["class"] = f"{existing_class} staff-upload__input hidden".strip()
        attrs.setdefault("accept", ACCEPTED_UPLOAD_TYPES)
        attrs.setdefault("data-batch-upload-input", "true")
        return super().get_context(name, value, attrs)


class StaffMultipleFileField(MultipleFileField):
    widget = StaffMultipleFileInput


class StaffBatchUploadForm(forms.Form):
    client = ClientChoiceField(
        queryset=get_user_model().objects.none(),
        label="Client name",
        widget=forms.Select(
            attrs={
                "class": "w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-soft focus:border-accent focus:outline-none",
            }
        ),
    )
    project = ProjectChoiceField(
        queryset=Project.objects.none(),
        required=False,
        label="Project workspace",
        help_text="Optional. Leave blank to upload into the client's general file folder.",
        widget=forms.Select(
            attrs={
                "class": "w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-soft focus:border-accent focus:outline-none",
            }
        ),
    )
    batch_files = StaffMultipleFileField(
        required=True,
        help_text="Upload photos, videos, design files, decks, or packaged delivery files for the client.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["client"].queryset = get_user_model().objects.filter(is_staff=False).order_by(
            "username",
            "first_name",
            "last_name",
        )
        self.fields["project"].queryset = Project.objects.select_related("client").order_by(
            "client__username",
            "-updated_at",
        )

    def clean(self):
        cleaned_data = super().clean()
        client = cleaned_data.get("client")
        project = cleaned_data.get("project")
        if client and project and project.client_id != client.pk:
            self.add_error("project", "Choose a project owned by the selected client.")
        return cleaned_data

    def get_upload_folder(self):
        if hasattr(self, "_upload_folder"):
            return self._upload_folder

        self._upload_folder = self.cleaned_data.get("project") or ensure_client_upload_folder(
            self.cleaned_data["client"]
        )
        return self._upload_folder

    def save_batch(self):
        project = self.get_upload_folder()
        batch_files = list(self.cleaned_data["batch_files"])
        created_assets = []

        for index, uploaded_file in enumerate(batch_files, start=1):
            asset = MediaAsset.objects.create(
                project=project,
                title=build_media_title("", uploaded_file, index=index, total=len(batch_files)),
                kind=infer_media_kind(uploaded_file),
            )
            save_uploaded_media_file(asset, uploaded_file)
            created_assets.append(asset)

        return created_assets
