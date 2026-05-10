from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render

from .forms import DocumentUploadForm, DocumentVerifyForm, SignUpForm
from .models import DocumentRecord, LedgerBlock


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Account created successfully.")
        return redirect("dashboard")

    return render(request, "documents/signup.html", {"form": form})


@login_required
def dashboard_view(request):
    context = {
        "document_count": DocumentRecord.objects.count(),
        "ledger_blocks": LedgerBlock.objects.select_related("document", "document__uploaded_by")[:10],
    }
    return render(request, "documents/dashboard.html", context)


@login_required
@transaction.atomic
def register_document_view(request):
    form = DocumentUploadForm(request.POST or None, request.FILES or None)

    if request.method == "POST" and form.is_valid():
        document_hash = form.document_hash()
        existing = DocumentRecord.objects.filter(document_hash=document_hash).first()
        if existing:
            messages.warning(request, "This document is already registered in the database.")
            return render(request, "documents/register.html", {"form": form, "document_hash": document_hash})

        last_block = LedgerBlock.objects.order_by("-index").first()
        previous_hash = last_block.block_hash if last_block else "GENESIS"

        document = DocumentRecord.objects.create(
            owner=form.cleaned_data["owner"],
            title=form.cleaned_data["title"],
            file_name=form.cleaned_data["document"].name,
            document_hash=document_hash,
            uploaded_by=request.user,
        )
        block = LedgerBlock.objects.create(
            document=document,
            index=(last_block.index + 1) if last_block else 1,
            previous_hash=previous_hash,
            block_hash="pending",
        )
        block.block_hash = LedgerBlock.make_hash(block.payload())
        block.save(update_fields=["block_hash"])

        messages.success(request, "Document registered and stored in the Django database.")
        return redirect("dashboard")

    return render(request, "documents/register.html", {"form": form})


@login_required
def verify_document_view(request):
    form = DocumentVerifyForm(request.POST or None, request.FILES or None)
    result = None
    document_hash = None

    if request.method == "POST" and form.is_valid():
        document_hash = form.document_hash()
        document = DocumentRecord.objects.filter(document_hash=document_hash).select_related("uploaded_by").first()

        if not document:
            result = {
                "status": "danger",
                "title": "Document not authentic",
                "message": "No matching hash was found in the Django database.",
            }
        elif not ledger_is_valid():
            result = {
                "status": "danger",
                "title": "Ledger tampered",
                "message": "The document exists, but the blockchain ledger links are invalid.",
            }
        else:
            result = {
                "status": "success",
                "title": "Document authentic",
                "message": f"Matched document '{document.title}' uploaded by {document.uploaded_by.username}.",
            }

    return render(request, "documents/verify.html", {