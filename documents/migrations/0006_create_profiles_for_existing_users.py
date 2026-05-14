import uuid

from django.conf import settings
from django.db import migrations


def create_profiles(apps, schema_editor):
    User = apps.get_model("auth", "User")
    UserProfile = apps.get_model("documents", "UserProfile")

    for user in User.objects.all():
        UserProfile.objects.get_or_create(
            user=user,
            defaults={
                "email_verified": True,
                "email_token": str(uuid.uuid4()),
            },
        )


def remove_profiles(apps, schema_editor):
    UserProfile = apps.get_model("documents", "UserProfile")
    UserProfile.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("documents", "0005_userprofile"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(create_profiles, remove_profiles),
    ]
