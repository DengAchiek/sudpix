import mimetypes
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Count, Q
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import TemplateView

from apps.cart.models import CartItem
from apps.core.utils import format_currency
from apps.dashboard.models import DownloadEvent
from apps.media_management.models import MediaAsset
from apps.media_management.forms import ensure_protected_photo_preview
from apps.payments.models import Payment
from apps.payments.services import (
    MpesaConfigurationError,
    MpesaGatewayError,
    initiate_stk_push,
    prepare_stk_push_request,
)
from apps.projects.models import (
    FinalDelivery,
    Project,
    ProjectApproval,
    ProjectBrief,
    ProjectFeedback,
    ProjectMilestone,
    RevisionRequest,
    complete_project_milestone,
    ensure_project_workspace,
)

from .forms import (
    ProjectApprovalForm,
    ProjectBriefForm,
    ProjectFeedbackForm,
    RevisionRequestForm,
)

CLIENT_VISIBLE_MEDIA_KINDS = (
    MediaAsset.Kind.PHOTO,
    MediaAsset.Kind.VIDEO,
    MediaAsset.Kind.DESIGN,
    MediaAsset.Kind.DOCUMENT,
)
CLIENT_CHECKOUT_PAYMENT_METHODS = (Payment.Method.MPESA,)


class PortalAccessMixin(LoginRequiredMixin):
    login_url = "accounts:login"

    def get_portal_context(self):
        return build_portal_context(self.request.user)


class DashboardView(PortalAccessMixin, TemplateView):
    template_name = "client/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_portal_context())
        return context


class ProjectsView(PortalAccessMixin, TemplateView):
    template_name = "client/projects.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_portal_context())
        context["projects"] = list(get_project_queryset(self.request.user))
        return context


class ProjectDetailView(PortalAccessMixin, TemplateView):
    template_name = "client/project_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_portal_context())
        project = get_project_by_slug(self.request.user, self.kwargs["slug"])
        context.update(build_workspace_context(self.request.user, project))
        return context


class UpdateProjectBriefView(PortalAccessMixin, View):
    def post(self, request, slug):
        project = get_project_by_slug(request.user, slug)
        ensure_project_workspace(project)
        brief = ProjectBrief.objects.filter(project=project).first()
        form = ProjectBriefForm(request.POST, instance=brief)
        if not form.is_valid():
            return render_workspace_error(request, project, brief_form=form)

        brief = form.save(commit=False)
        brief.project = project
        brief.save()
        messages.success(request, "Your project brief has been saved.")
        return redirect(f"{project.get_absolute_url()}#brief")


class AddProjectFeedbackView(PortalAccessMixin, View):
    def post(self, request, slug):
        project = get_project_by_slug(request.user, slug)
        ensure_project_workspace(project)
        form = ProjectFeedbackForm(request.POST)
        if not form.is_valid():
            return render_workspace_error(request, project, feedback_form=form)

        feedback = form.save(commit=False)
        feedback.project = project
        feedback.author = request.user
        feedback.save()
        messages.success(request, "Your feedback has been shared with the SudPix team.")
        return redirect(f"{project.get_absolute_url()}#feedback")


class RequestProjectRevisionView(PortalAccessMixin, View):
    def post(self, request, slug):
        project = get_project_by_slug(request.user, slug)
        ensure_project_workspace(project)
        form = RevisionRequestForm(request.POST, project=project)
        if not form.is_valid():
            return render_workspace_error(request, project, revision_form=form)

        with transaction.atomic():
            revision = form.save(commit=False)
            revision.project = project
            revision.requested_by = request.user
            revision.save()
            ProjectApproval.objects.update_or_create(
                project=project,
                defaults={
                    "decision": ProjectApproval.Decision.REVISIONS_REQUESTED,
                    "note": revision.details,
                    "decided_by": request.user,
                    "decided_at": timezone.now(),
                },
            )

        messages.success(request, "Revision request sent. SudPix can now track it in this workspace.")
        return redirect(f"{project.get_absolute_url()}#revisions")


class ApproveProjectView(PortalAccessMixin, View):
    def post(self, request, slug):
        project = get_project_by_slug(request.user, slug)
        ensure_project_workspace(project)
        form = ProjectApprovalForm(request.POST)
        if not form.is_valid():
            return render_workspace_error(request, project, approval_form=form)

        approval, _ = ProjectApproval.objects.get_or_create(project=project)
        approval.approve(request.user, form.cleaned_data["note"])
        approval.save()
        messages.success(request, "Project approved. Your delivery status remains visible below.")
        return redirect(f"{project.get_absolute_url()}#approval")


class FilesView(PortalAccessMixin, TemplateView):
    template_name = "client/files.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_portal_context())

        project = get_project_from_request(self.request)
        active_kind = self.request.GET.get("kind", "").strip().lower()

        files = get_media_queryset(self.request.user).order_by("-is_highlight", "-uploaded_at")
        if project:
            files = files.filter(project=project)
        if active_kind in CLIENT_VISIBLE_MEDIA_KINDS:
            files = files.filter(kind=active_kind)

        files = list(files)
        payment_context = build_payment_context(self.request.user)
        attach_media_access_state(files, payment_context)

        library_files = get_media_queryset(self.request.user)
        if project:
            library_files = library_files.filter(project=project)

        downloadable_files_count = sum(
            1
            for media_file in library_files
            if media_file.id in payment_context["confirmed_asset_ids"] and media_file.has_downloadable_file
        )

        context["selected_project"] = project
        context["active_kind"] = active_kind or "all"
        context["files"] = files
        context["projects"] = list(get_project_queryset(self.request.user))
        context["photo_files_count"] = library_files.filter(kind=MediaAsset.Kind.PHOTO).count()
        context["video_files_count"] = library_files.filter(kind=MediaAsset.Kind.VIDEO).count()
        context["design_files_count"] = library_files.filter(kind=MediaAsset.Kind.DESIGN).count()
        context["document_files_count"] = library_files.filter(kind=MediaAsset.Kind.DOCUMENT).count()
        context["downloadable_files_count"] = downloadable_files_count
        context["selected_files_count"] = payment_context["selected_file_count"]
        context["selected_photos_count"] = payment_context["selected_photo_count"]
        context["selected_videos_count"] = payment_context["selected_video_count"]
        context["selected_designs_count"] = payment_context["selected_design_count"]
        context["selected_documents_count"] = payment_context["selected_document_count"]
        return context


class CartView(PortalAccessMixin, TemplateView):
    template_name = "client/cart.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_portal_context())
        payment_context = build_payment_context(self.request.user)
        cart_items = payment_context["cart_items"]
        attach_media_access_state(
            [item.media_asset for item in cart_items],
            payment_context,
        )
        context["cart_items"] = cart_items
        context["photos_selected"] = payment_context["selected_photo_count"]
        context["videos_selected"] = payment_context["selected_video_count"]
        context["designs_selected"] = payment_context["selected_design_count"]
        context["documents_selected"] = payment_context["selected_document_count"]
        context["total_files"] = payment_context["selected_file_count"]
        context["pending_total"] = format_currency(payment_context["selected_total"])
        context["can_checkout"] = bool(cart_items)
        return context


class CheckoutView(PortalAccessMixin, TemplateView):
    template_name = "client/checkout.html"

    def post(self, request, *args, **kwargs):
        payment_context = build_payment_context(request.user)
        cart_items = payment_context["cart_items"]

        if not cart_items:
            messages.warning(request, "Select one or more files before continuing to download.")
            return redirect("client:files")

        payment_method = request.POST.get("payment_method", Payment.Method.MPESA)
        if payment_method not in CLIENT_CHECKOUT_PAYMENT_METHODS:
            messages.error(
                request,
                "M-Pesa is the active payment method for client downloads right now.",
            )
            return redirect("client:checkout")

        if payment_method not in Payment.Method.values:
            payment_method = Payment.Method.MPESA

        phone_number = request.POST.get("phone_number", "").strip()
        if payment_method == Payment.Method.MPESA:
            try:
                phone_number, _ = prepare_stk_push_request(phone_number, request)
            except (MpesaConfigurationError, MpesaGatewayError) as exc:
                messages.error(request, str(exc))
                return redirect("client:checkout")

        selected_assets = [item.media_asset for item in cart_items]
        selected_asset_ids = [asset.id for asset in selected_assets]
        related_projects = {asset.project_id: asset.project for asset in selected_assets}
        payment = Payment.objects.create(
            user=request.user,
            project=next(iter(related_projects.values())) if len(related_projects) == 1 else None,
            amount=payment_context["selected_total"],
            method=payment_method,
            status=Payment.Status.PENDING,
            phone_number=phone_number,
        )
        payment.media_assets.add(*selected_asset_ids)

        try:
            initiate_stk_push(
                payment=payment,
                request=request,
                account_reference=build_payment_account_reference(payment),
                transaction_desc="SudPix file payment",
            )
        except (MpesaConfigurationError, MpesaGatewayError) as exc:
            payment.status = Payment.Status.FAILED
            payment.result_desc = str(exc)
            payment.save(update_fields=["status", "result_desc"])
            messages.error(request, str(exc))
            return redirect("client:payment_processing", payment_id=payment.pk)

        CartItem.objects.filter(
            user=request.user,
            media_asset_id__in=selected_asset_ids,
        ).delete()
        messages.success(
            request,
            "An M-Pesa payment prompt has been sent to your phone. Complete it to unlock your download.",
        )
        return redirect("client:payment_processing", payment_id=payment.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_portal_context())
        payment_context = build_payment_context(self.request.user)
        cart_items = payment_context["cart_items"]
        attach_media_access_state(
            [item.media_asset for item in cart_items],
            payment_context,
        )
        context["cart_items"] = cart_items
        context["selected_total"] = format_currency(payment_context["selected_total"])
        context["selected_file_count"] = payment_context["selected_file_count"]
        context["selected_photo_count"] = payment_context["selected_photo_count"]
        context["selected_video_count"] = payment_context["selected_video_count"]
        context["selected_design_count"] = payment_context["selected_design_count"]
        context["selected_document_count"] = payment_context["selected_document_count"]
        context["payment_methods"] = [
            (value, label)
            for value, label in Payment.Method.choices
            if value in CLIENT_CHECKOUT_PAYMENT_METHODS
        ]
        context["payment_phone_number"] = get_recent_payment_phone(self.request.user)
        return context


class PaymentsView(PortalAccessMixin, TemplateView):
    template_name = "client/payments.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_portal_context())
        context["payments"] = list(get_payment_queryset(self.request.user))
        return context


class PaymentProcessingView(PortalAccessMixin, TemplateView):
    template_name = "client/payment_processing.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_portal_context())
        payment = get_payment_for_user_or_404(self.request.user, self.kwargs["payment_id"])
        context["payment"] = payment
        context["selected_assets"] = list(payment.media_assets.all())
        context["retry_phone_number"] = payment.phone_number or get_recent_payment_phone(self.request.user)
        return context


class PaymentStatusView(PortalAccessMixin, View):
    def get(self, request, payment_id):
        payment = get_payment_for_user_or_404(request.user, payment_id)
        return JsonResponse(
            {
                "id": payment.id,
                "status": payment.status,
                "status_label": payment.get_status_display(),
                "status_message": payment.status_message,
                "formatted_amount": payment.formatted_amount,
                "reference": payment.reference,
                "downloads_url": reverse("client:downloads"),
                "payments_url": reverse("client:payments"),
                "download_ready": payment.status == Payment.Status.CONFIRMED,
                "can_retry": payment.method == Payment.Method.MPESA and payment.status != Payment.Status.CONFIRMED,
            }
        )


class RetryPaymentPromptView(PortalAccessMixin, View):
    def post(self, request, payment_id):
        payment = get_payment_for_user_or_404(request.user, payment_id)
        if payment.method != Payment.Method.MPESA:
            messages.error(request, "Only M-Pesa prompts can be resent from the client portal.")
            return redirect("client:payments")

        if payment.status == Payment.Status.CONFIRMED:
            messages.success(request, "This payment is already confirmed and your files are unlocked.")
            return redirect("client:downloads")

        phone_number = request.POST.get("phone_number", "").strip() or payment.phone_number
        try:
            phone_number, _ = prepare_stk_push_request(phone_number, request)
        except (MpesaConfigurationError, MpesaGatewayError) as exc:
            messages.error(request, str(exc))
            return redirect("client:payment_processing", payment_id=payment.pk)

        payment.phone_number = phone_number
        payment.status = Payment.Status.PENDING
        payment.result_code = None
        payment.result_desc = ""
        payment.reference = ""
        payment.save(
            update_fields=[
                "phone_number",
                "status",
                "result_code",
                "result_desc",
                "reference",
            ]
        )

        try:
            initiate_stk_push(
                payment=payment,
                request=request,
                account_reference=build_payment_account_reference(payment),
                transaction_desc="SudPix file payment",
            )
        except (MpesaConfigurationError, MpesaGatewayError) as exc:
            payment.status = Payment.Status.FAILED
            payment.result_desc = str(exc)
            payment.save(update_fields=["status", "result_desc"])
            messages.error(request, str(exc))
            return redirect("client:payment_processing", payment_id=payment.pk)

        messages.success(request, "A fresh M-Pesa payment prompt has been sent to your phone.")
        return redirect("client:payment_processing", payment_id=payment.pk)


class DownloadsView(PortalAccessMixin, TemplateView):
    template_name = "client/downloads.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_portal_context())
        payment_context = build_payment_context(self.request.user)
        files = [
            media_file
            for media_file in get_media_queryset(self.request.user).order_by("-is_highlight", "-uploaded_at")
            if media_file.id in payment_context["confirmed_asset_ids"] and media_file.has_downloadable_file
        ]
        attach_media_access_state(files, payment_context)
        context["downloadable_files"] = files
        return context


class AddToCartView(PortalAccessMixin, View):
    def post(self, request, file_id):
        media_file = get_object_or_404(get_media_queryset(request.user), pk=file_id)
        payment_context = build_payment_context(request.user)
        next_url = get_next_url(request, reverse("client:files"))

        if media_file.id in payment_context["confirmed_asset_ids"]:
            if is_async_gallery_request(request):
                return JsonResponse({"redirect_url": reverse("client:downloads")})
            messages.success(
                request,
                "This file is already unlocked and ready for download.",
            )
            return redirect("client:downloads")

        if media_file.id in payment_context["pending_asset_ids"]:
            pending_payment = get_latest_pending_payment(request.user, media_file)
            if pending_payment:
                pending_url = reverse("client:payment_processing", args=[pending_payment.pk])
                if is_async_gallery_request(request):
                    return JsonResponse({"redirect_url": pending_url})
                messages.info(
                    request,
                    "This file is already included in a payment request awaiting verification.",
                )
                return redirect(pending_url)
            if is_async_gallery_request(request):
                return JsonResponse({"redirect_url": reverse("client:payments")})
            messages.info(
                request,
                "This file is already included in a payment request awaiting verification.",
            )
            return redirect("client:payments")

        _, created = CartItem.objects.get_or_create(
            user=request.user,
            media_asset=media_file,
        )
        if created:
            complete_project_milestone(media_file.project, "Client selections made")
        if is_async_gallery_request(request):
            return JsonResponse(build_selection_response_payload(request.user, selected=True, created=created))
        if created:
            messages.success(request, "File selected for download.")
        else:
            messages.info(request, "This file is already selected for download.")
        return redirect(next_url)


class RemoveFromCartView(PortalAccessMixin, View):
    def post(self, request, file_id):
        media_file = get_object_or_404(get_media_queryset(request.user), pk=file_id)
        CartItem.objects.filter(user=request.user, media_asset=media_file).delete()
        if is_async_gallery_request(request):
            return JsonResponse(build_selection_response_payload(request.user, selected=False))
        messages.info(request, "File removed from your download selection.")
        return redirect(get_next_url(request, reverse("client:files")))


class DownloadAssetView(PortalAccessMixin, View):
    def get(self, request, file_id):
        media_file = get_object_or_404(get_media_queryset(request.user), pk=file_id)

        if not asset_is_unlocked(request.user, media_file.id):
            pending_payment = get_latest_pending_payment(request.user, media_file)
            if pending_payment:
                messages.info(
                    request,
                    "This file is still waiting for payment confirmation. Complete the M-Pesa prompt to continue.",
                )
                return redirect("client:payment_processing", payment_id=pending_payment.pk)
            messages.warning(
                request,
                "Complete payment for this file before the download can begin.",
            )
            return redirect("client:cart")

        record_download_event(request.user, media_file)

        if media_file.file:
            return FileResponse(
                media_file.file.open("rb"),
                as_attachment=True,
                filename=media_file.download_name,
            )

        if media_file.file_url:
            return redirect(media_file.file_url)

        messages.warning(
            request,
            "This file is not available for download yet. Please check back after processing is completed.",
        )
        return redirect(get_next_url(request, reverse("client:files")))


class PreviewAssetView(PortalAccessMixin, View):
    def get(self, request, file_id):
        media_file = get_object_or_404(get_preview_media_queryset(request.user), pk=file_id)
        ensure_protected_photo_preview(media_file)

        if media_file.preview_image and media_file.preview_is_protected:
            content_type = mimetypes.guess_type(media_file.preview_image.name)[0] or "image/jpeg"
            return FileResponse(media_file.preview_image.open("rb"), content_type=content_type)

        return redirect(media_file.preview_url)


def get_project_queryset(user):
    visible_files_filter = Q(media_files__kind__in=CLIENT_VISIBLE_MEDIA_KINDS)
    return Project.objects.filter(client=user).annotate(
        photo_count=Count(
            "media_files",
            filter=Q(media_files__kind=MediaAsset.Kind.PHOTO),
            distinct=True,
        ),
        video_count=Count(
            "media_files",
            filter=Q(media_files__kind=MediaAsset.Kind.VIDEO),
            distinct=True,
        ),
        design_count=Count(
            "media_files",
            filter=Q(media_files__kind=MediaAsset.Kind.DESIGN),
            distinct=True,
        ),
        document_count=Count(
            "media_files",
            filter=Q(media_files__kind=MediaAsset.Kind.DOCUMENT),
            distinct=True,
        ),
        file_count=Count(
            "media_files",
            filter=visible_files_filter,
            distinct=True,
        ),
    )


def get_project_by_slug(user, slug):
    try:
        return get_project_queryset(user).get(slug=slug)
    except Project.DoesNotExist as exc:
        raise Http404("Project not found.") from exc


def get_media_queryset(user):
    return MediaAsset.objects.filter(
        project__client=user,
        kind__in=CLIENT_VISIBLE_MEDIA_KINDS,
    ).select_related("project")


def get_preview_media_queryset(user):
    files = MediaAsset.objects.select_related("project")
    if user.is_staff:
        return files
    return files.filter(
        project__client=user,
        kind__in=CLIENT_VISIBLE_MEDIA_KINDS,
    )


def get_payment_queryset(user):
    return Payment.objects.filter(user=user).select_related("project").prefetch_related(
        "media_assets__project",
        "project__media_files",
    )


def get_cart_queryset(user):
    return CartItem.objects.filter(user=user).select_related("media_asset__project")


def get_project_from_request(request):
    project_slug = request.GET.get("project", "").strip()
    if not project_slug:
        return None
    return get_object_or_404(Project, client=request.user, slug=project_slug)


def attach_media_access_state(files, payment_context):
    for media_file in files:
        media_file.is_download_unlocked = media_file.id in payment_context["confirmed_asset_ids"]
        media_file.has_pending_payment = media_file.id in payment_context["pending_asset_ids"]
        media_file.is_selected = media_file.id in payment_context["selected_asset_ids"]


def get_next_url(request, fallback_url):
    next_url = request.POST.get("next") or request.GET.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return fallback_url


def is_async_gallery_request(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


def build_selection_response_payload(user, *, selected, created=None):
    payment_context = build_payment_context(user)
    payload = {
        "selected": selected,
        "selected_files_count": payment_context["selected_file_count"],
        "selected_photo_count": payment_context["selected_photo_count"],
        "selected_video_count": payment_context["selected_video_count"],
        "selected_design_count": payment_context["selected_design_count"],
        "selected_document_count": payment_context["selected_document_count"],
    }
    if created is not None:
        payload["created"] = created
    return payload


def build_payment_context(user):
    payments = list(get_payment_queryset(user))
    confirmed_asset_ids = set()
    pending_asset_ids = set()

    for payment in payments:
        asset_ids = get_payment_asset_ids(payment)
        if payment.status == Payment.Status.CONFIRMED:
            confirmed_asset_ids.update(asset_ids)
        elif payment.status == Payment.Status.PENDING:
            pending_asset_ids.update(asset_ids)

    pending_asset_ids -= confirmed_asset_ids
    cart_items = [
        item
        for item in get_cart_queryset(user)
        if item.media_asset_id not in confirmed_asset_ids
        and item.media_asset_id not in pending_asset_ids
    ]
    selected_assets = [item.media_asset for item in cart_items]
    selected_total = sum(
        (media_file.client_price for media_file in selected_assets),
        Decimal("0"),
    )

    return {
        "payments": payments,
        "confirmed_asset_ids": confirmed_asset_ids,
        "pending_asset_ids": pending_asset_ids,
        "selected_asset_ids": {item.media_asset_id for item in cart_items},
        "selected_file_count": len(selected_assets),
        "selected_photo_count": sum(1 for media_file in selected_assets if media_file.kind == MediaAsset.Kind.PHOTO),
        "selected_video_count": sum(1 for media_file in selected_assets if media_file.kind == MediaAsset.Kind.VIDEO),
        "selected_design_count": sum(1 for media_file in selected_assets if media_file.kind == MediaAsset.Kind.DESIGN),
        "selected_document_count": sum(1 for media_file in selected_assets if media_file.kind == MediaAsset.Kind.DOCUMENT),
        "selected_total": selected_total,
        "cart_items": cart_items,
    }


def asset_is_unlocked(user, media_asset_id):
    for payment in get_payment_queryset(user):
        if payment.status != Payment.Status.CONFIRMED:
            continue
        if media_asset_id in get_payment_asset_ids(payment):
            return True
    return False


def get_payment_asset_ids(payment):
    selected_assets = list(payment.media_assets.all())
    if selected_assets:
        return {asset.id for asset in selected_assets}
    if payment.project_id:
        return set(
            payment.project.media_files.filter(kind__in=CLIENT_VISIBLE_MEDIA_KINDS).values_list("id", flat=True)
        )
    return set()


def build_portal_context(user):
    projects = list(get_project_queryset(user))
    payment_context = build_payment_context(user)
    payments = payment_context["payments"]
    recent_project = next((project for project in projects if project.file_count), None)
    if recent_project is None and projects:
        recent_project = projects[0]

    recent_files = []
    if recent_project:
        recent_files = list(
            get_media_queryset(user)
            .filter(project=recent_project)
            .order_by("-is_highlight", "-uploaded_at")[:2]
        )
        attach_media_access_state(recent_files, payment_context)

    downloadable_files = [
        media_file
        for media_file in get_media_queryset(user).order_by("-is_highlight", "-uploaded_at")
        if media_file.id in payment_context["confirmed_asset_ids"] and media_file.has_downloadable_file
    ]
    attach_media_access_state(downloadable_files, payment_context)
    ready_downloads_list = downloadable_files[:2]

    return {
        "projects_count": len(projects),
        "projects": projects,
        "files_available": get_media_queryset(user).count(),
        "pending_payments": sum(
            1 for payment in payments if payment.status == Payment.Status.PENDING
        ),
        "downloads_ready": len(downloadable_files),
        "photos_available": get_media_queryset(user).filter(kind=MediaAsset.Kind.PHOTO).count(),
        "videos_available": get_media_queryset(user).filter(kind=MediaAsset.Kind.VIDEO).count(),
        "designs_available": get_media_queryset(user).filter(kind=MediaAsset.Kind.DESIGN).count(),
        "documents_available": get_media_queryset(user).filter(kind=MediaAsset.Kind.DOCUMENT).count(),
        "selected_files_count": payment_context["selected_file_count"],
        "recent_project": recent_project,
        "recent_files": recent_files,
        "recent_payment": payments[0] if payments else None,
        "ready_downloads_list": ready_downloads_list,
    }


def build_payment_account_reference(payment):
    if payment.project_id:
        return payment.project.title[:12]
    return f"SudPix{payment.pk}"


def record_download_event(user, media_file):
    DownloadEvent.objects.create(
        user=user,
        media_asset=media_file,
        payment=get_latest_confirmed_payment(user, media_file),
    )


def get_latest_confirmed_payment(user, media_file):
    payments = get_payment_queryset(user).filter(status=Payment.Status.CONFIRMED)
    for payment in payments:
        if media_file.id in get_payment_asset_ids(payment):
            return payment
    return None


def get_latest_pending_payment(user, media_file):
    payments = get_payment_queryset(user).filter(status=Payment.Status.PENDING)
    for payment in payments:
        if media_file.id in get_payment_asset_ids(payment):
            return payment
    return None


def get_payment_for_user_or_404(user, payment_id):
    return get_object_or_404(get_payment_queryset(user), pk=payment_id)


def get_recent_payment_phone(user):
    return (
        Payment.objects.filter(user=user)
        .exclude(phone_number="")
        .values_list("phone_number", flat=True)
        .first()
    )


def build_workspace_context(
    user,
    project,
    *,
    brief_form=None,
    feedback_form=None,
    revision_form=None,
    approval_form=None,
):
    ensure_project_workspace(project)
    payment_context = build_payment_context(user)
    files = list(
        get_media_queryset(user)
        .filter(project=project)
        .order_by("-is_highlight", "-uploaded_at")
    )
    attach_media_access_state(files, payment_context)
    milestones = list(project.milestones.all())
    completed_milestones = sum(
        1 for milestone in milestones if milestone.status == ProjectMilestone.Status.COMPLETED
    )
    progress_percent = round((completed_milestones / len(milestones)) * 100) if milestones else 0
    brief = ProjectBrief.objects.filter(project=project).first()
    approval = ProjectApproval.objects.filter(project=project).first()
    delivery = FinalDelivery.objects.filter(project=project).first()

    return {
        "project": project,
        "files": files,
        "brief": brief,
        "brief_form": brief_form or ProjectBriefForm(instance=brief),
        "milestones": milestones,
        "milestones_complete": completed_milestones,
        "progress_percent": progress_percent,
        "feedback_entries": list(project.feedback_entries.select_related("author")),
        "feedback_form": feedback_form or ProjectFeedbackForm(),
        "revision_requests": list(project.revision_requests.select_related("media_asset", "requested_by")),
        "revision_form": revision_form or RevisionRequestForm(project=project),
        "approval": approval,
        "approval_form": approval_form or ProjectApprovalForm(),
        "delivery": delivery,
        "latest_project_payment": get_payment_queryset(user).filter(project=project).first(),
        "downloadable_files": [
            media_file
            for media_file in files
            if media_file.id in payment_context["confirmed_asset_ids"] and media_file.has_downloadable_file
        ],
    }


def render_workspace_error(request, project, **form_overrides):
    context = build_portal_context(request.user)
    context.update(build_workspace_context(request.user, project, **form_overrides))
    return render(request, "client/project_detail.html", context, status=400)
