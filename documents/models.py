import hashlib
import json
import uuid

from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.db.utils import OperationalError, ProgrammingError
from django.dispatch import receiver


class DocumentRecord(models.Model):
    owner = models.CharField(max_length=120)
    title = models.CharField(max_length=160)
    file_name = models.CharField(max_length=255)
    document_file = models.FileField(upload_to="verified_documents/", blank=True)
    document_content = models.BinaryField(blank=True, null=True)
    content_type = models.CharField(max_length=120, blank=True, default="application/octet-stream")
    document_hash = models.CharField(max_length=64, unique=True)
    verification_token = models.CharField(max_length=64, unique=True, default=uuid.uuid4)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.owner}"

    @property
    def has_stored_document(self):
        return bool(self.document_content or self.document_file)


class LedgerBlock(models.Model):
    document = models.OneToOneField(DocumentRecord, on_delete=models.CASCADE, related_name="ledger_block")
    index = models.PositiveIntegerField(unique=True)
    previous_hash = models.CharField(max_length=64)
    block_hash = models.CharField(max_length=64, unique=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-index"]

    def __str__(self):
        return f"Block #{self.index}"

    @staticmethod
    def make_hash(payload):
        content = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(content).hexdigest()

    def payload(self):
        return {
            "index": self.index,
            "document_hash": self.document.document_hash,
            "owner": self.document.owner,
            "title": self.document.title,
            "file_name": self.document.file_name,
            "cost": float(self.document.cost),
            "uploaded_by": self.document.uploaded_by.username,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp.isoformat(),
        }

    def is_valid(self):
        return self.block_hash == self.make_hash(self.payload())


class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('reviewer', 'Reviewer'),
        ('uploader', 'Uploader'),
    )
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='uploader')

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        try:
            UserProfile.objects.create(user=instance)
        except (OperationalError, ProgrammingError):
            pass


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    try:
        if hasattr(instance, 'profile'):
            instance.profile.save()
    except (OperationalError, ProgrammingError):
        pass
