from django.contrib import admin

from .models import CartItem


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("user", "media_asset", "added_at")
    search_fields = ("user__username", "media_asset__title", "media_asset__project__title")
