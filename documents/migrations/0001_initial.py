from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="DocumentRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("owner", models.CharField(max_length=120)),
                ("title", models.CharField(max_length=160)),
                ("file_name", models.CharField(max_length=255)),
                ("document_hash", models.CharField(max_length=64, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("uploaded_by", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="LedgerBlock",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("index", models.PositiveIntegerField(unique=True)),
                ("previous_hash", models.CharField(max_length=64)),
                ("block_hash", models.CharField(max_length=64, unique=True)),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                ("document", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="ledger_block", to="documents.documentrecord")),
            ],
            options={
                "ordering": ["-index"],
            },
        ),
    ]
