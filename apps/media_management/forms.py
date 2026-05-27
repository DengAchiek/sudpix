from io import BytesIO
from pathlib import Path

from django import forms
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont, ImageOps, UnidentifiedImageError

from apps.projects.models import Project, complete_project_milestone, ensure_client_upload_folder

from .models import MediaAsset

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}
DESIGN_EXTENSIONS = {".svg", ".ai", ".eps", ".psd", ".indd", ".fig", ".sketch"}
DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt", ".ppt", ".pptx", ".key", ".zip"}
ACCEPTED_UPLOAD_TYPES = (
    "image/*,video/*,.svg,.ai,.eps,.psd,.indd,.fig,.sketch,"
    ".pdf,.doc,.docx,.txt,.ppt,.pptx,.key,.zip"
)
PROTECTED_PREVIEW_MAX_SIZE = (1400, 1400)


def infer_media_kind(uploaded_file, fallback_kind=MediaAsset.Kind.PHOTO):
    content_type = getattr(uploaded_file, "content_type", "") or ""
    suffix = Path(uploaded_file.name).suffix.lower()

    if suffix in DESIGN_EXTENSIONS:
        return MediaAsset.Kind.DESIGN
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


def build_protected_photo_preview(source_file):
    try:
        source_file.seek(0)
        with Image.open(source_file) as source_image:
            image = ImageOps.exif_transpose(source_image).convert("RGB")
            image.thumbnail(PROTECTED_PREVIEW_MAX_SIZE)
    except (OSError, UnidentifiedImageError, ValueError):
        return None
    finally:
        source_file.seek(0)

    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = ImageFont.load_default(size=max(16, min(image.size) // 26))
    label = "SUDPIX PREVIEW"
    padding_x = max(10, image.width // 40)
    padding_y = max(8, image.height // 55)
    text_box = draw.textbbox((0, 0), label, font=font)
    label_width = text_box[2] - text_box[0]
    label_height = text_box[3] - text_box[1]
    left = max(padding_x, image.width - label_width - (padding_x * 3))
    top = max(padding_y, image.height - label_height - (padding_y * 3))
    draw.rounded_rectangle(
        (
            left - padding_x,
            top - padding_y,
            left + label_width + padding_x,
            top + label_height + padding_y,
        ),
        radius=max(8, padding_y),
        fill=(0, 0, 0, 135),
    )
    draw.text((left, top), label, font=font, fill=(255, 255, 255, 210))

    watermarked = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
    output = BytesIO()
    watermarked.save(output, format="JPEG", quality=78, optimize=True)
    return ContentFile(output.getvalue())


def attach_protected_photo_preview(media_asset, source_file, filename):
    preview = build_protected_photo_preview(source_file)
    if preview is None:
        return False

    preview_filename = f"{Path(filename).stem}-preview.jpg"
    if media_asset.preview_image:
        media_asset.preview_image.delete(save=False)
    media_asset.preview_image.save(preview_filename, preview, save=False)
    media_asset.preview_is_protected = True
    return True


def ensure_protected_photo_preview(media_asset):
    if media_asset.preview_is_protected or media_asset.kind != MediaAsset.Kind.PHOTO or not media_asset.file:
        return

    with media_asset.file.open("rb") as source_file:
        if attach_protected_photo_preview(media_asset, source_file, media_asset.download_name):
            media_asset.save(update_fields=("preview_image", "preview_is_protected"))


def save_uploaded_media_file(media_asset, uploaded_file):
    filename = Path(uploaded_file.name).name
    if infer_media_kind(uploaded_file, media_asset.kind) == MediaAsset.Kind.PHOTO:
        attach_protected_photo_preview(media_asset, uploaded_file, filename)

    uploaded_file.seek(0)
    media_asset.file.save(filename, uploaded_file, save=False)
    media_asset.save()
    complete_project_milestone(media_asset.project, "Gallery uploaded")


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True
    template_name = "admin/media_management/multiple_file_dropzone.html"

    def get_context(self, name, value, attrs):
        attrs = attrs or {}
        existing_class = attrs.get("class", "")
        attrs["class"] = f"{existing_class} admin-batch-upload__input".strip()
        attrs.setdefault("accept", ACCEPTED_UPLOAD_TYPES)
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
        help_text="Choose the client who owns the files.",
    )
    project = ProjectChoiceField(
        queryset=Project.objects.none(),
        required=False,
        label="Project workspace",
        help_text="Optional. Choose the booked project, or leave blank to use the client's general file folder.",
    )
    batch_files = MultipleFileField(
        required=True,
        help_text="Upload photos, videos, design files, decks, or packaged delivery files. One item is created for each file.",
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
        self.fields["project"].queryset = Project.objects.select_related("client").order_by(
            "client__username",
            "-updated_at",
        )
        self.fields["batch_files"].required = not self.instance.pk

        if not self.instance.pk:
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
                project = cleaned_data.get("project")
                if project and project.client_id != client.pk:
                    self.add_error("project", "Choose a project owned by the selected client.")
                else:
                    cleaned_data["project"] = project or ensure_client_upload_folder(client)
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
