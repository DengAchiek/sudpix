from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bookings", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="bookingrequest",
            name="phone",
            field=models.CharField(blank=True, max_length=50),
        ),
    ]
