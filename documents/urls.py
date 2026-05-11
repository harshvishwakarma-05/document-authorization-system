from django.contrib.auth import views as auth_views

from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.dashboard_view, name="dashboard"),
    path("signup/", views.signup_view, name="signup"),
    path("login/", auth_views.LoginView.as_view(template_name="documents/login.html"), name="login"),
    path("forgot-password/", views.forgot_password_view, name="forgot_password"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("register-document/", views.register_document_view, name="register_document"),
    path("verify-document/", views.verify_document_view, name="verify_document"),
    path("documents/<int:pk>/open/", views.open_document_view, name="open_document"),
    path("documents/<int:pk>/edit/", views.edit_document_view, name="edit_document"),
    path("documents/<int:pk>/delete/", views.delete_document_view, name="delete_document"),
    path("certificate/<str:token>/", views.certificate_view, name="certificate"),
    path("certificate/<str:token>/document/", views.open_certificate_document_view, name="open_certificate_document"),
path(
    'download/<uuid:token>/',
    views.download_certificate_document,
    name='download_certificate_document'
),
]
