import hashlib
from pathlib import Path

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import DocumentRecord

MAX_UPLOAD_SIZE = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".doc", ".docx", ".txt"}

class ForgotPasswordForm(forms.Form):
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    new_password = forms.CharField(widget=forms.PasswordInput, min_length=8)
    confirm_password = forms.CharField(widget=forms.PasswordInput, min_length=8)

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if new_password and confirm_password and new_password != confirm_password:
            raise forms.ValidationError("New password and confirm password do not match.")

        return cleaned_data


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=False)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})


class DocumentUploadForm(forms.Form):
    owner = forms.CharField(max_length=120)
    title = forms.CharField(max_length=160)
    document = forms.FileField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["owner"].widget.attrs.update({"placeholder": "Example: College Office"})
        self.fields["title"].widget.attrs.update({"placeholder": "Example: Degree Certificate"})

    def document_hash(self):
        uploaded_file = self.cleaned_data["document"]
        hasher = hashlib.sha256()
        for chunk in uploaded_file.chunks():
            hasher.update(chunk)
        uploaded_file.seek(0)
        return hasher.hexdigest()

    def clean_document(self):
        uploaded_file = self.cleaned_data["document"]
        validate_safe_document(uploaded_file)
        return uploaded_file


class DocumentVerifyForm(forms.Form):
    document = forms.FileField()

    def document_hash(self):
        uploaded_file = self.cleaned_data["document"]
        hasher = hashlib.sha256()
        for chunk in uploaded_file.chunks():
            hasher.update(chunk)
        uploaded_file.seek(0)
        return hasher.hexdigest()

    def clean_document(self):
        uploaded_file = self.cleaned_data["document"]
        validate_safe_document(uploaded_file)
        return uploaded_file

class DocumentEditForm(forms.ModelForm):

    document_file = forms.FileField(required=False, widget=forms.FileInput)

    class Meta:
        model = DocumentRecord
        fields = ["owner", "title", "document_file"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["owner"].widget.attrs.update({
            "placeholder": "Example: College Office"
        })

        self.fields["title"].widget.attrs.update({
            "placeholder": "Example: Degree Certificate"
        })
def validate_safe_document(uploaded_file):
    extension = Path(uploaded_file.name).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise forms.ValidationError(f"Unsupported file type. Allowed files: {allowed}")

    if uploaded_file.size > MAX_UPLOAD_SIZE:
        raise forms.ValidationError("File is too large. Maximum allowed size is 10 MB.")
