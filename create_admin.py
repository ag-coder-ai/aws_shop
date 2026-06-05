import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Fashion_Hub.settings")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

EMAIL = "admin@shop.com"
PASSWORD = "Admin@12345"

if not User.objects.filter(email=EMAIL).exists():
    User.objects.create_superuser(
        email=EMAIL,
        password=PASSWORD,
        full_name="Admin"
    )
    print("Superuser created")
else:
    print("Already exists")