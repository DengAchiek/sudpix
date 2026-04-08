from pathlib import Path

from django import forms
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile

from apps.projects.models import Project, ensure_client_upload_folder

from .models import MediaAsset

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}
DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt"}


def infer_media_kind(uploaded_file, fallback_kind=MediaAsset.Kind.PHOTO):
    content_type = getattr(uploaded_file, "content_type", "") or ""
    suffix = Path(uploaded_file.name).suffix.lower()

    if content_type.startswith("image/") or suffix in IMAGE_EXTENSIONS:
        return MediaAsset.Kind.PHOTO
    if content_type.startswith("video/") or suffix in VIDEO_EXTENSIONS:
        return MediaAsset.Kind.VIDEO
    if suffix in DOCUMENT_EXTENSIONS:
        return MediaAsset.Kind.DOCUMENT
    return fallback_kind


def build_media_title(base_title, uploaded_file, index=1, total=1):
    cleaned_title = (base_title or "").strip()
    if total == 1 and cleaned_title:
        return cleaned_title
    if total > 1 and cleaned_title:
        return f"{cleaned_title} {index}"
    return Path(uploaded_file.name).stem.replace("_", " ").replace("-", " ")


def save_uploaded_media_file(media_asset, uploaded_file):
    filename = Path(uploaded_file.name).name
    uploaded_file.seek(0)
    content = uploaded_file.read()

    media_asset.file.save(filename, ContentFile(content), save=False)
    if infer_media_kind(uploaded_file, media_asset.kind) == MediaAsset.Kind.PHOTO:
        media_asset.preview_image.save(filename, ContentFile(content), save=False)

    media_asset.save()


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True
    template_name = "admin/media_management/multiple_file_dropzone.html"

    def get_context(self, name, value, attrs):
        attrs = attrs or {}
        existing_class = attrs.get("class", "")
        attrs["class"] = f"{existing_class} admin-batch-upload__input".strip()
        attrs.setdefault("accept", "image/*,video/*")
        attrs.setdefault("data-batch-upload-input", "true")
        return super().get_context(name, value, attrs)


class MultipleFileField(forms.FileField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if not data:
            return []
        if isinstance(data, (list, tuple)):
            return [single_file_clean(item, initial) for item in data]
        return [single_file_clean(data, initial)]


class ProjectChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.title} ({obj.client.username})"


class ClientChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        full_name = obj.get_full_name().strip() if hasattr(obj, "get_full_name") else ""
        if full_name:
            return f"{full_name} ({obj.username})"
        return obj.username


class MediaAssetAdminForm(forms.ModelForm):
    client = ClientChoiceField(
        queryset=get_user_model().objects.none(),
        label="Client name",
        help_text="Choose the client and SudPix will use that client's assigned folder automatically.",
    )
    batch_files = MultipleFileField(
        required=True,
        help_text="Drag and drop many local images or videos here, or click to browse. One media item will be created for each file.",
    )

    class Meta:
        model = MediaAsset
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["client"].queryset = get_user_model().objects.filter(is_staff=False).order_by(
            "username",
            "first_name",
            "last_name",
        )
        self.fields["batch_files"].required = not self.instance.pk

        if not self.instance.pk:
            if "project" in self.fields:
                self.fields["project"].required = False
            hidden_add_fields = (
                "title",
                "kind",
                "price",
                "preview_image",
                "preview_image_url",
                "file",
                "file_url",
                "is_highlight",
                "is_edited",
            )
            for field_name in hidden_add_fields:
                if field_name in self.fields:
                    self.fields[field_name].required = False

    def clean(self):
        cleaned_data = super().clean()
        batch_files = cleaned_data.get("batch_files") or []

        if not self.instance.pk:
            client = cleaned_data.get("client")
            if not client:
                self.add_error("client", "Choose the client who should receive these files.")
            else:
                cleaned_data["project"] = ensure_client_upload_folder(client)
            if not batch_files:
                self.add_error("batch_files", "Upload one or more files.")

        return cleaned_data

    def build_title(self, uploaded_file, index=1, total=1):
        return build_media_title("", uploaded_file, index=index, total=total)

    def get_upload_folder(self):
        if hasattr(self, "_upload_folder"):
            return self._upload_folder

        if self.instance.pk:
            self._upload_folder = self.instance.project
        else:
            self._upload_folder = self.cleaned_data["project"]

        return self._upload_folder

    def save_batch(self):
        batch_files = list(self.cleaned_data["batch_files"])
        upload_folder = self.get_upload_folder()
        created_assets = []

        for index, uploaded_file in enumerate(batch_files, start=1):
            asset = MediaAsset.objects.create(
                project=upload_folder,
                title=self.build_title(uploaded_file, index=index, total=len(batch_files)),
                kind=infer_media_kind(uploaded_file),
            )
            save_uploaded_media_file(asset, uploaded_file)
            created_assets.append(asset)

        return created_assets
