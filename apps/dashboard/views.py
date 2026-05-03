import csv
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.views.generic import TemplateView

from apps.bookings.models import BookingRequest
from apps.cart.models import CartItem
from apps.core.utils import format_currency
from apps.media_management.models import MediaAsset
from apps.notifications.models import AdminNotification
from apps.payments.models import Payment
from apps.projects.models import Project

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
    period_options = (
        ("30", "Last 30 days"),
        ("90", "Last 90 days"),
        ("180", "Last 180 days"),
        ("365", "Last 365 days"),
    )
    chart_months = 9

    def dispatch(self, request, *args, **kwargs):
        self.form = StaffBatchUploadForm()
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if request.GET.get("export") == "csv":
            return self.render_export()
        return super().get(request, *args, **kwargs)

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

    def get_selected_period_value(self):
        allowed_values = {value for value, _ in self.period_options}
        selected_value = self.request.GET.get("period", "180")
        if selected_value not in allowed_values:
            return "180"
        return selected_value

    def get_period_days(self):
        return int(self.get_selected_period_value())

    def get_period_label(self):
        return dict(self.period_options)[self.get_selected_period_value()]

    def get_recent_month_starts(self, count):
        today = timezone.localdate()
        starts = []

        for offset in range(count - 1, -1, -1):
            month = today.month - offset
            year = today.year

            while month <= 0:
                month += 12
                year -= 1

            starts.append(date(year, month, 1))

        return starts

    def percentage(self, numerator, denominator):
        if denominator <= 0:
            return 0.0
        return round((numerator / denominator) * 100, 2)

    def delta_payload(self, current_value, previous_value):
        if previous_value == 0:
            if current_value > 0:
                return {
                    "text": "New activity",
                    "positive": True,
                }
            return {
                "text": "No change",
                "positive": True,
            }

        delta = ((current_value - previous_value) / previous_value) * 100
        return {
            "text": f"{delta:+.2f}%",
            "positive": delta >= 0,
        }

    def compact_number(self, value):
        if value >= 1_000_000:
            return f"{value / 1_000_000:.1f}M"
        if value >= 1_000:
            return f"{value / 1_000:.1f}K"
        return str(value)

    def build_activity_lookup(self, queryset, field_name):
        activity_lookup = defaultdict(int)

        for value in queryset.values_list(field_name, flat=True):
            if not value:
                continue

            if hasattr(value, "astimezone"):
                value = timezone.localtime(value)
            key = f"{value.year:04d}-{value.month:02d}"
            activity_lookup[key] += 1

        return activity_lookup

    def build_metric_cards(
        self,
        period_uploads,
        previous_uploads,
        period_cart_items,
        previous_cart_items,
        period_payments,
        previous_payments,
    ):
        period_upload_count = period_uploads.count()
        previous_upload_count = previous_uploads.count()
        period_selection_count = period_cart_items.count()
        previous_selection_count = previous_cart_items.count()
        period_payment_count = period_payments.count()
        previous_payment_count = previous_payments.count()
        period_confirmed_count = period_payments.filter(status=Payment.Status.CONFIRMED).count()
        previous_confirmed_count = previous_payments.filter(status=Payment.Status.CONFIRMED).count()
        period_confirmed_total = sum(
            (payment.amount for payment in period_payments.filter(status=Payment.Status.CONFIRMED)),
            Decimal("0"),
        )
        previous_confirmed_total = sum(
            (payment.amount for payment in previous_payments.filter(status=Payment.Status.CONFIRMED)),
            Decimal("0"),
        )

        selection_rate = self.percentage(period_selection_count, period_upload_count)
        previous_selection_rate = self.percentage(previous_selection_count, previous_upload_count)
        payment_success_rate = self.percentage(period_confirmed_count, period_payment_count)
        previous_payment_success_rate = self.percentage(previous_confirmed_count, previous_payment_count)

        return [
            {
                "label": "File Selection Rate",
                "value": f"{selection_rate:.2f}%",
                "delta": self.delta_payload(selection_rate, previous_selection_rate),
                "footnote": f"{period_selection_count} client picks from {period_upload_count} uploaded files",
                "target": "selected-files",
                "accent": "gold",
                "export_value": selection_rate,
            },
            {
                "label": "Payment Completion",
                "value": f"{payment_success_rate:.2f}%",
                "delta": self.delta_payload(payment_success_rate, previous_payment_success_rate),
                "footnote": f"{period_confirmed_count} confirmed payments out of {period_payment_count} prompts",
                "target": "payments",
                "accent": "accent",
                "export_value": payment_success_rate,
            },
            {
                "label": "Revenue Secured",
                "value": format_currency(period_confirmed_total),
                "delta": self.delta_payload(float(period_confirmed_total), float(previous_confirmed_total)),
                "footnote": "Confirmed M-Pesa payments unlocked for downloads",
                "target": "downloads",
                "accent": "soft",
                "export_value": str(period_confirmed_total),
            },
        ]

    def build_analytics_chart(self, uploads, cart_items, payments):
        month_starts = self.get_recent_month_starts(self.chart_months)
        chart_start = month_starts[0]

        upload_lookup = self.build_activity_lookup(
            uploads.filter(uploaded_at__date__gte=chart_start),
            "uploaded_at",
        )
        selection_lookup = self.build_activity_lookup(
            cart_items.filter(added_at__date__gte=chart_start),
            "added_at",
        )
        payment_lookup = self.build_activity_lookup(
            payments.filter(created_at__date__gte=chart_start),
            "created_at",
        )

        months = []
        uploads_total = 0
        selections_total = 0
        payments_total = 0
        max_total = 1

        for month_start in month_starts:
            key = f"{month_start.year:04d}-{month_start.month:02d}"
            uploads_count = upload_lookup[key]
            selections_count = selection_lookup[key]
            payments_count = payment_lookup[key]
            total = uploads_count + selections_count + payments_count
            max_total = max(max_total, total)
            uploads_total += uploads_count
            selections_total += selections_count
            payments_total += payments_count
            months.append(
                {
                    "label": month_start.strftime("%b"),
                    "uploads_count": uploads_count,
                    "selections_count": selections_count,
                    "payments_count": payments_count,
                    "total": total,
                }
            )

        for month in months:
            total_height = 224
            month["upload_height"] = 0
            month["selection_height"] = 0
            month["payment_height"] = 0

            if month["uploads_count"]:
                month["upload_height"] = max(18, round((month["uploads_count"] / max_total) * total_height))
            if month["selections_count"]:
                month["selection_height"] = max(18, round((month["selections_count"] / max_total) * total_height))
            if month["payments_count"]:
                month["payment_height"] = max(18, round((month["payments_count"] / max_total) * total_height))

        scale_values = [
            self.compact_number(max_total),
            self.compact_number(round(max_total * 0.75)),
            self.compact_number(round(max_total * 0.5)),
            self.compact_number(round(max_total * 0.25)),
            "0",
        ]

        return {
            "months": months,
            "scale_values": scale_values,
            "totals": [
                {"label": "Uploads", "value": uploads_total, "tone": "gold"},
                {"label": "Selections", "value": selections_total, "tone": "accent"},
                {"label": "Payments", "value": payments_total, "tone": "soft"},
            ],
        }

    def build_file_type_stats(self, uploads):
        file_type_choices = [
            (MediaAsset.Kind.PHOTO, "Photos"),
            (MediaAsset.Kind.VIDEO, "Videos"),
            (MediaAsset.Kind.DESIGN, "Design"),
            (MediaAsset.Kind.DOCUMENT, "Documents"),
        ]
        total_uploads = uploads.count()
        stats = []

        for index, (kind, label) in enumerate(file_type_choices):
            count = uploads.filter(kind=kind).count()
            percent = self.percentage(count, total_uploads)
            active_bars = max(1, round((percent / 100) * 22)) if count else 0
            stats.append(
                {
                    "label": label,
                    "count": count,
                    "percent": f"{percent:.2f}%",
                    "meter": [{"active": bar_index < active_bars} for bar_index in range(22)],
                    "tone": ("gold", "accent", "soft", "muted")[index],
                }
            )

        return stats

    def build_client_folder_rows(self):
        projects = (
            Project.objects.select_related("client")
            .annotate(
                asset_count=Count("media_files", distinct=True),
                selection_count=Count("media_files__cart_items", distinct=True),
                download_count=Count("media_files__download_events", distinct=True),
            )
            .order_by("-asset_count", "-updated_at")
        )
        folder_rows = []

        for project in projects[:10]:
            folder_rows.append(
                {
                    "title": project.title,
                    "client": project.client.get_username(),
                    "status": project.get_status_display(),
                    "status_key": project.status,
                    "asset_count": project.asset_count,
                    "selection_count": project.selection_count,
                    "download_count": project.download_count,
                    "engagement": f"{self.percentage(project.selection_count, project.asset_count):.0f}%",
                    "search_text": " ".join(
                        [
                            project.title,
                            project.client.get_username(),
                            project.get_status_display(),
                            project.service_type or "",
                        ]
                    ),
                }
            )

        status_counts = {
            "all": Project.objects.count(),
            Project.Status.READY: Project.objects.filter(status=Project.Status.READY).count(),
            Project.Status.PROCESSING: Project.objects.filter(status=Project.Status.PROCESSING).count(),
            Project.Status.PENDING: Project.objects.filter(status=Project.Status.PENDING).count(),
            Project.Status.COMPLETED: Project.objects.filter(status=Project.Status.COMPLETED).count(),
        }

        folder_tabs = [
            {"key": "all", "label": "All", "count": status_counts["all"]},
            {"key": Project.Status.READY, "label": "Ready", "count": status_counts[Project.Status.READY]},
            {
                "key": Project.Status.PROCESSING,
                "label": "Processing",
                "count": status_counts[Project.Status.PROCESSING],
            },
            {"key": Project.Status.PENDING, "label": "Pending", "count": status_counts[Project.Status.PENDING]},
            {
                "key": Project.Status.COMPLETED,
                "label": "Completed",
                "count": status_counts[Project.Status.COMPLETED],
            },
        ]

        return folder_rows, folder_tabs

    def build_workflow_nodes(self, notifications, bookings, uploads, payments, downloads):
        return [
            {
                "label": "Client Signups",
                "value": notifications.count(),
                "detail": "Admin alerts created",
                "style": "top: 12%; left: 10%;",
                "tone": "gold",
            },
            {
                "label": "Bookings",
                "value": bookings.count(),
                "detail": "Service requests in view",
                "style": "top: 18%; right: 12%;",
                "tone": "accent",
            },
            {
                "label": "Uploads",
                "value": uploads.count(),
                "detail": "Files delivered to folders",
                "style": "top: 48%; left: 14%;",
                "tone": "soft",
            },
            {
                "label": "Pending Payments",
                "value": payments.filter(status=Payment.Status.PENDING).count(),
                "detail": "Awaiting confirmation",
                "style": "bottom: 18%; left: 18%;",
                "tone": "muted",
            },
            {
                "label": "Downloads",
                "value": downloads.count(),
                "detail": "Completed releases",
                "style": "bottom: 14%; right: 14%;",
                "tone": "gold",
            },
        ]

    def render_export(self):
        context = self.get_context_data()
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            f'attachment; filename="sudpix-analytics-{timezone.localdate().isoformat()}.csv"'
        )
        writer = csv.writer(response)

        writer.writerow(["SudPix Analytics Dashboard"])
        writer.writerow(["Period", context["period_label"]])
        writer.writerow([])
        writer.writerow(["Headline Metric", "Value"])
        for card in context["dashboard_cards"]:
            writer.writerow([card["label"], card["value"]])

        writer.writerow([])
        writer.writerow(["Month", "Uploads", "Selections", "Payments"])
        for month in context["analytics_chart"]["months"]:
            writer.writerow(
                [
                    month["label"],
                    month["uploads_count"],
                    month["selections_count"],
                    month["payments_count"],
                ]
            )

        writer.writerow([])
        writer.writerow(["File Type", "Share", "Total Files"])
        for item in context["file_type_stats"]:
            writer.writerow([item["label"], item["percent"], item["count"]])

        writer.writerow([])
        writer.writerow(["Folder", "Client", "Status", "Files", "Selections", "Downloads"])
        for row in context["client_folder_rows"]:
            writer.writerow(
                [
                    row["title"],
                    row["client"],
                    row["status"],
                    row["asset_count"],
                    row["selection_count"],
                    row["download_count"],
                ]
            )

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        period_days = self.get_period_days()
        period_start = now - timedelta(days=period_days)
        previous_period_start = period_start - timedelta(days=period_days)

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
        projects = Project.objects.select_related("client")

        period_uploads = uploads.filter(uploaded_at__gte=period_start)
        previous_uploads = uploads.filter(
            uploaded_at__gte=previous_period_start,
            uploaded_at__lt=period_start,
        )
        period_cart_items = cart_items.filter(added_at__gte=period_start)
        previous_cart_items = cart_items.filter(
            added_at__gte=previous_period_start,
            added_at__lt=period_start,
        )
        period_payments = payments.filter(created_at__gte=period_start)
        previous_payments = payments.filter(
            created_at__gte=previous_period_start,
            created_at__lt=period_start,
        )
        folder_rows, folder_tabs = self.build_client_folder_rows()
        analytics_chart = self.build_analytics_chart(uploads, cart_items, payments)
        file_type_scope = period_uploads if period_uploads.exists() else uploads

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
                "period_label": self.get_period_label(),
                "selected_period": self.get_selected_period_value(),
                "period_options": [
                    {
                        "value": value,
                        "label": label,
                        "selected": value == self.get_selected_period_value(),
                    }
                    for value, label in self.period_options
                ],
                "dashboard_cards": self.build_metric_cards(
                    period_uploads,
                    previous_uploads,
                    period_cart_items,
                    previous_cart_items,
                    period_payments,
                    previous_payments,
                ),
                "analytics_chart": analytics_chart,
                "file_type_stats": self.build_file_type_stats(file_type_scope),
                "client_folder_rows": folder_rows,
                "folder_tabs": folder_tabs,
                "workflow_nodes": self.build_workflow_nodes(
                    notifications,
                    bookings,
                    uploads,
                    payments,
                    downloads,
                ),
                "ready_projects_count": projects.filter(status=Project.Status.READY).count(),
                "processing_projects_count": projects.filter(status=Project.Status.PROCESSING).count(),
                "completed_projects_count": projects.filter(status=Project.Status.COMPLETED).count(),
                "pending_revenue": format_currency(
                    sum(
                        (
                            payment.amount
                            for payment in payments.filter(status=Payment.Status.PENDING)
                        ),
                        Decimal("0"),
                    )
                ),
            }
        )
        return context
