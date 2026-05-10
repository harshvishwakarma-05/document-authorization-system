import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("documents", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="documentrecord",
            name="verification_token",
            field=models.CharField(default=uuid.uuid4, max_length=64, unique=True),
        ),
    ]
