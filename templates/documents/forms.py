class DocumentEditForm(forms.ModelForm):
    class Meta:
        model = DocumentRecord
        fields = ["owner", "title"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["owner"].widget.attrs.update({"placeholder": "Example: College Office"})
        self.fields["title"].widget.attrs.update({"placeholder": "Example: Degree Certificate"})


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


def validate_safe_document(uploaded_file):
    ...
