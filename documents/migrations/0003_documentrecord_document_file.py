from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("documents", "0002_documentrecord_verification_token"),
    ]

    operations = [
        migrations.AddField(
            model_name="documentrecord",
            name="document_file",
            field=models.FileField(blank=True, upload_to="verified_documents/"),
        ),
    ]
