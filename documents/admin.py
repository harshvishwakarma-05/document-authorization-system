from django.contrib import admin

from .models import DocumentRecord, LedgerBlock


@admin.register(DocumentRecord)
class DocumentRecordAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "file_name", "uploaded_by", "created_at")
    search_fields = ("title", "owner", "file_name", "document_hash", "uploaded_by__username")
    readonly_fields = ("document_hash", "created_at")


@admin.register(LedgerBlock)
class LedgerBlockAdmin(admin.ModelAdmin):
    list_display = ("index", "document", "previous_hash", "block_hash", "timestamp")
    readonly_fields = ("index", "previous_hash", "block_hash", "timestamp")
