import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'documentauth.settings')
django.setup()

from django.contrib.auth.models import User

if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@gmail.com',
        password='Admin123@'
    )
    print("Superuser created")
else:
    print("Admin already exists")