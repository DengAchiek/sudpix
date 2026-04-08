from django.conf import settings
from django.db import models

class CartItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cart_items",
    )
    media_asset = models.ForeignKey(
        "media_management.MediaAsset",
        on_delete=models.CASCADE,
        related_name="cart_items",
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-added_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("user", "media_asset"),
                name="unique_user_cart_item",
            )
        ]

    def __str__(self):
        return f"{self.user} -> {self.media_asset}"
