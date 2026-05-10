import hashlib
import json

from django.conf import settings
from django.db import models


class DocumentRecord(models.Model):
    owner = models.CharField(max_length=120)
    title = models.CharField(max_length=160)
    file_name = models.CharField(max_length=255)
    document_hash = models.CharField(max_length=64, unique=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.owner}"


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
            "uploaded_by": self.document.uploaded_by.username,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp.isoformat(),
        }

    def is_valid(self):
        return self.block_hash == self.make_hash(self.payload())