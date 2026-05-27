from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("media_management", "0002_mediaasset_file_mediaasset_preview_image"),
    ]

    operations = [
        migrations.AddField(
            model_name="mediaasset",
            name="preview_is_protected",
            field=models.BooleanField(default=False, editable=False),
        ),
    ]
