from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AdminNotification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kind", models.CharField(choices=[("client_registered", "Client registered")], max_length=50)),
                ("title", models.CharField(max_length=255)),
                ("message", models.TextField(blank=True)),
                ("is_read", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("related_user", models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name="admin_notifications", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ("is_read", "-created_at"),
            },
        ),
    ]
