from django.contrib import admin

from .models import Service, ServicePackage


class ServicePackageInline(admin.TabularInline):
    model = ServicePackage
    extra = 0
    fields = ("display_order", "name", "price_label", "description", "highlighted")
    ordering = ("display_order", "id")


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    inlines = (ServicePackageInline,)
    list_display = ("name", "slug", "display_order", "is_active", "packages_total")
    list_filter = ("is_active",)
    search_fields = ("name", "heading", "description")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("display_order", "is_active")

    fieldsets = (
        (
            "Service basics",
            {
                "fields": (
                    "name",
                    "slug",
                    "display_order",
                    "is_active",
                    "icon",
                )
            },
        ),
        (
            "Page content",
            {
                "fields": (
                    "badge",
                    "heading",
                    "description",
                    "teaser",
                )
            },
        ),
        (
            "Lists and actions",
            {
                "fields": (
                    "included_items",
                    "best_for_items",
                    "packages_heading",
                    "book_label",
                    "booking_service",
                )
            },
        ),
    )

    @admin.display(description="Packages")
    def packages_total(self, obj):
        return obj.packages.count()


@admin.register(ServicePackage)
class ServicePackageAdmin(admin.ModelAdmin):
    list_display = ("name", "service", "price_label", "display_order", "highlighted")
    list_filter = ("service", "highlighted")
    list_select_related = ("service",)
    search_fields = ("name", "service__name", "description", "price_label")
    list_editable = ("price_label", "display_order", "highlighted")
