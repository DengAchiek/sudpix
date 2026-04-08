from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html

from .forms import MediaAssetAdminForm, infer_media_kind, save_uploaded_media_file
from .models import MediaAsset


@admin.register(MediaAsset)
class MediaAssetAdmin(admin.ModelAdmin):
    form = MediaAssetAdminForm
    list_display = ("title", "project", "kind", "has_uploaded_file", "uploaded_at")
    list_filter = ("kind",)
    readonly_fields = ("preview_image_tag", "file_link", "uploaded_at")
    search_fields = ("title", "project__title", "project__client__username")

    def get_fields(self, request, obj=None):
        if obj:
            return (
                "project",
                "title",
                "kind",
                "price",
                "preview_image",
                "preview_image_url",
                "preview_image_tag",
                "file",
                "file_url",
                "file_link",
                "is_highlight",
                "is_edited",
                "uploaded_at",
            )
        return (
            "client",
            "batch_files",
        )

    def save_model(self, request, obj, form, change):
        batch_files = list(form.cleaned_data.get("batch_files") or [])
        if change or not batch_files:
            super().save_model(request, obj, form, change)
            return

        obj.project = form.get_upload_folder()
        first_file = batch_files[0]
        obj.title = form.build_title(first_file, index=1, total=len(batch_files))
        obj.kind = infer_media_kind(first_file)
        obj.price = MediaAsset.default_price_for_kind(obj.kind)
        obj.is_highlight = False
        obj.is_edited = False
        obj.preview_image_url = ""
        obj.file_url = ""
        super().save_model(request, obj, form, change)
        self.attach_uploaded_file(obj, first_file)

        for index, uploaded_file in enumerate(batch_files[1:], start=2):
            extra_asset = MediaAsset.objects.create(
                project=obj.project,
                title=form.build_title(uploaded_file, index=index, total=len(batch_files)),
                kind=infer_media_kind(uploaded_file),
            )
            self.attach_uploaded_file(extra_asset, uploaded_file)

        messages.success(
            request,
            f"{len(batch_files)} files were uploaded to {obj.project.title}.",
        )

    def attach_uploaded_file(self, media_asset, uploaded_file):
        save_uploaded_media_file(media_asset, uploaded_file)

    @admin.display(boolean=True, description="Uploaded")
    def has_uploaded_file(self, obj):
        return bool(obj.file)

    @admin.display(description="Preview")
    def preview_image_tag(self, obj):
        if obj.preview_image or obj.is_previewable_image:
            return format_html(
                '<img src="{}" alt="{}" style="max-height: 120px; border-radius: 12px;" />',
                obj.preview_url,
                obj.title,
            )
        return "-"

    @admin.display(description="Asset file")
    def file_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">Open uploaded file</a>', obj.file.url)
        if obj.file_url:
            return format_html('<a href="{}" target="_blank">Open external file</a>', obj.file_url)
        return "-"
