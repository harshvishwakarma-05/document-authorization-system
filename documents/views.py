import base64
from io import BytesIO

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.core.mail import send_mail
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import DocumentEditForm, DocumentUploadForm, DocumentVerifyForm, ForgotPasswordForm, SignUpForm
from .models import DocumentRecord, LedgerBlock, UserProfile


class VerifiedLoginView(LoginView):
    template_name = "documents/login.html"

    def form_valid(self, form):
        user = form.get_user()
        profile, _ = UserProfile.objects.get_or_create(user=user)
        if not user.is_staff and not profile.email_verified:
            messages.warning(self.request, "Please verify your email before login.")
            return redirect("login")
        return super().form_valid(form)


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    form = SignUpForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.save(commit=False)
        user.is_active = True
        user.save()

        profile = UserProfile.objects.create(user=user)
        verification_url = public_url(
            request,
            redirect("verify_email", token=profile.email_token).url
        )

        send_verification_email(user, verification_url)

        messages.success(request, "Account created. Please verify your email before login.")

        if settings.EMAIL_BACKEND.endswith("console.EmailBackend"):
            messages.warning(request, f"Demo verification link: {verification_url}")

        return redirect("login")

    return render(request, "documents/signup.html", {"form": form})

def verify_email_view(request, token):
    profile = get_object_or_404(UserProfile.objects.select_related("user"), email_token=token)
    profile.email_verified = True
    profile.save(update_fields=["email_verified"])
    messages.success(request, "Email verified successfully. You can login now.")
    return redirect("login")


def forgot_password_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    form = ForgotPasswordForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = User.objects.filter(
            username=form.cleaned_data["username"],
            email=form.cleaned_data["email"],
        ).first()
        if not user:
            messages.warning(request, "Username and email do not match any account.")
            return render(request, "documents/forgot_password.html", {"form": form})

        user.set_password(form.cleaned_data["new_password"])
        user.save(update_fields=["password"])
        messages.success(request, "Password changed successfully. Please login with your new password.")
        return redirect("login")

    return render(request, "documents/forgot_password.html", {"form": form})


@login_required
def dashboard_view(request):
    if request.user.is_superuser:
        documents = DocumentRecord.objects.all()
        ledger_blocks = LedgerBlock.objects.select_related("document", "document__uploaded_by")
    else:
        documents = DocumentRecord.objects.filter(uploaded_by=request.user)
        ledger_blocks = LedgerBlock.objects.select_related("document", "document__uploaded_by").filter(
            document__uploaded_by=request.user
        )

    context = {
        "document_count": documents.count(),
        "ledger_blocks": ledger_blocks[:10],
        "site_base_url": getattr(settings, "SITE_BASE_URL", ""),
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
            messages.warning(request, "This file is already saved as an original document.")
            return render(request, "documents/register.html", {"form": form, "document_hash": document_hash})

        last_block = LedgerBlock.objects.order_by("-index").first()
        previous_hash = last_block.block_hash if last_block else "GENESIS"

        uploaded_file = form.cleaned_data["document"]
        document_content = uploaded_file.read()
        uploaded_file.seek(0)
        document = DocumentRecord.objects.create(
            owner=form.cleaned_data["owner"],
            title=form.cleaned_data["title"],
            file_name=uploaded_file.name,
            document_file=uploaded_file,
            document_content=document_content,
            content_type=getattr(uploaded_file, "content_type", "") or "application/octet-stream",
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

        messages.success(request, "Original document saved successfully. A QR certificate is now available.")
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
                "title": "Fake or Changed Document",
                "message": "This file does not match any saved original document.",
            }
        elif not ledger_is_valid():
            result = {
                "status": "danger",
                "title": "Ledger Problem Found",
                "message": "The file exists, but the verification record has been changed.",
            }
        else:
            result = {
                "status": "success",
                "title": "Original Document",
                "message": f"This file matches '{document.title}' saved by {document.uploaded_by.username}.",
            }

    return render(request, "documents/verify.html", {
        "form": form,
        "result": result,
        "document_hash": document_hash,
    })


@login_required
@transaction.atomic
def edit_document_view(request, pk):
    document = get_user_document(request, pk)
    form = DocumentEditForm(request.POST or None, instance=document)

    if request.method == "POST" and form.is_valid():
        form.save()
        rebuild_ledger()
        messages.success(request, "Document details updated successfully.")
        return redirect("dashboard")

    return render(request, "documents/edit_document.html", {
        "form": form,
        "document": document,
    })


@login_required
@transaction.atomic
def delete_document_view(request, pk):
    document = get_user_document(request, pk)

    if request.method == "POST":
        if document.document_file:
            document.document_file.delete(save=False)
        document.delete()
        rebuild_ledger()
        messages.success(request, "Document deleted successfully.")
        return redirect("dashboard")

    return render(request, "documents/delete_document.html", {"document": document})


def certificate_view(request, token):
    document = get_object_or_404(
        DocumentRecord.objects.select_related("uploaded_by", "ledger_block"),
        verification_token=token,
    )
    certificate_url = public_url(request, redirect("certificate", token=document.verification_token).url)
    file_url = public_url(
        request,
        redirect("download_certificate_document", token=document.verification_token).url,
    ) if document.has_stored_document else None
    file_qr_code = make_qr_code(file_url) if file_url else None

    return render(request, "documents/certificate.html", {
        "document": document,
        "certificate_url": certificate_url,
        "file_url": file_url,
        "file_qr_code": file_qr_code,
        "ledger_valid": ledger_is_valid(),
    })


def make_qr_code(value):
    try:
        import qrcode
    except ImportError:
        return None

    image = qrcode.make(value)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def public_url(request, path):
    base_url = getattr(settings, "SITE_BASE_URL", "").strip().rstrip("/")
    if base_url:
        return f"{base_url}{path}"
    return request.build_absolute_uri(path)


def send_verification_email(user, verification_url):
    if not user.email:
        return

    send_mail(
        subject="Verify your Document Authorization account",
        message=f"Hello {user.username},\n\nClick this link to verify your email:\n{verification_url}\n\nThank you.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )


def open_certificate_document_view(request, token):
    document = get_object_or_404(DocumentRecord, verification_token=token)
    return document_response(document, as_attachment=False)


def download_certificate_document_view(request, token):
    document = get_object_or_404(DocumentRecord, verification_token=token)
    return document_response(document, as_attachment=True)


@login_required
def open_document_view(request, pk):
    document = get_user_document(request, pk)
    return document_response(document, as_attachment=False)


def document_response(document, as_attachment):
    if document.document_content:
        response = HttpResponse(document.document_content, content_type=document.content_type or "application/octet-stream")
        disposition = "attachment" if as_attachment else "inline"
        response["Content-Disposition"] = f'{disposition}; filename="{document.file_name}"'
        return response

    if document.document_file:
        try:
            return FileResponse(
                document.document_file.open("rb"),
                as_attachment=as_attachment,
                filename=document.file_name,
            )
        except FileNotFoundError:
            pass

    raise Http404("Document file not found.")


def get_user_document(request, pk):
    queryset = DocumentRecord.objects.select_related("uploaded_by", "ledger_block")
    if not request.user.is_superuser:
        queryset = queryset.filter(uploaded_by=request.user)
    return get_object_or_404(queryset, pk=pk)


def rebuild_ledger():
    previous_hash = "GENESIS"
    for index, block in enumerate(
        LedgerBlock.objects.select_related("document", "document__uploaded_by").order_by("timestamp", "id"),
        start=1,
    ):
        block.index = index
        block.previous_hash = previous_hash
        block.block_hash = LedgerBlock.make_hash(block.payload())
        block.save(update_fields=["index", "previous_hash", "block_hash"])
        previous_hash = block.block_hash


def ledger_is_valid():
    previous_hash = "GENESIS"
    for block in LedgerBlock.objects.select_related("document", "document__uploaded_by").order_by("index"):
        if block.previous_hash != previous_hash or not block.is_valid():
            return False
        previous_hash = block.block_hash
    return True
