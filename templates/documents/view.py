from django.contrib.auth.models import User
from .forms import ForgotPasswordForm

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
