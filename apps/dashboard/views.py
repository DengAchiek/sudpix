from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.views.generic import TemplateView

from apps.bookings.models import BookingRequest
from apps.cart.models import CartItem
from apps.media_management.models import MediaAsset
from apps.notifications.models import AdminNotification
from apps.payments.models import Payment

from .forms import StaffBatchUploadForm
from .models import DownloadEvent


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = "accounts:admin_login"

    def test_func(self):
        return bool(self.request.user.is_staff)

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return redirect("client:dashboard")
        return super().handle_no_permission()


class StaffDashboardView(StaffRequiredMixin, TemplateView):
    template_name = "dashboard/staff_dashboard.html"

    def dispatch(self, request, *args, **kwargs):
        self.form = StaffBatchUploadForm()
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.form = StaffBatchUploadForm(request.POST, request.FILES)
        if self.form.is_valid():
            created_assets = self.form.save_batch()
            project = self.form.get_upload_folder()
            client = self.form.cleaned_data["client"]
            messages.success(
                request,
                f"{len(created_assets)} file(s) uploaded for {client.username} into {project.title}.",
            )
            return redirect("dashboard:home")
        return self.render_to_response(self.get_context_data())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payments = Payment.objects.select_related("user", "project").prefetch_related("media_assets__project")
        bookings = BookingRequest.objects.select_related("client_account", "converted_project")
        cart_items = CartItem.objects.select_related("user", "media_asset__project")
        downloads = DownloadEvent.objects.select_related(
            "user",
            "media_asset__project",
            "payment",
        )
        uploads = MediaAsset.objects.select_related("project__client", "project")
        notifications = AdminNotification.objects.select_related("related_user")

        context.update(
            {
                "form": self.form,
                "recent_notifications": list(notifications[:6]),
                "recent_selections": list(cart_items[:8]),
                "recent_downloads": list(downloads[:8]),
                "recent_payments": list(payments[:8]),
                "recent_bookings": list(bookings[:8]),
                "recent_uploads": list(uploads[:8]),
                "gallery_uploads": list(uploads[:12]),
                "selected_files_count": cart_items.count(),
                "downloads_count": downloads.count(),
                "pending_payments_count": payments.filter(status=Payment.Status.PENDING).count(),
                "confirmed_payments_count": payments.filter(status=Payment.Status.CONFIRMED).count(),
                "new_bookings_count": bookings.filter(status=BookingRequest.Status.NEW).count(),
                "unread_notifications_count": notifications.filter(is_read=False).count(),
                "projects_count": uploads.values("project_id").distinct().count(),
                "clients_count": uploads.values("project__client_id").distinct().count(),
            }
        )
        return context
