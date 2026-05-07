from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("notifications", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="adminnotification",
            name="kind",
            field=models.CharField(
                choices=[
                    ("client_registered", "Client registered"),
                    ("booking_requested", "Booking requested"),
                ],
                max_length=50,
            ),
        ),
    ]
