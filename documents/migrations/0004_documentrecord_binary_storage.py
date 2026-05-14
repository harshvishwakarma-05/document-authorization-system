from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("documents", "0003_documentrecord_document_file"),
    ]

    operations = [
        migrations.AddField(
            model_name="documentrecord",
            name="document_content",
            field=models.BinaryField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="documentrecord",
            name="content_type",
            field=models.CharField(blank=True, default="application/octet-stream", max_length=120),
        ),
    ]
