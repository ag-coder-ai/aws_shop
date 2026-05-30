from django.db import models

from django.contrib.auth.models import (
    AbstractUser,
    BaseUserManager
)


# =========================================
# CUSTOM USER MANAGER
# =========================================

class UserManager(BaseUserManager):

    def create_user(
        self,
        email,
        phone,
        password=None,
        **extra_fields
    ):

        if not email:

            raise ValueError(
                "Email is required"
            )

        if not phone:

            raise ValueError(
                "Phone number is required"
            )

        email = self.normalize_email(email)

        user = self.model(

            email=email,
            phone=phone,
            **extra_fields

        )

        user.set_password(password)

        user.save(using=self._db)

        return user

    def create_superuser(
        self,
        email,
        phone,
        password=None,
        **extra_fields
    ):

        extra_fields.setdefault(
            "is_staff",
            True
        )

        extra_fields.setdefault(
            "is_superuser",
            True
        )

        extra_fields.setdefault(
            "is_active",
            True
        )

        return self.create_user(

            email,
            phone,
            password,
            **extra_fields

        )


# =========================================
# USER MODEL
# =========================================

class User(AbstractUser):

    username = None

    email = models.EmailField(
        unique=True
    )

    phone = models.CharField(
        max_length=10,
        unique=True
    )

    full_name = models.CharField(
        max_length=150
    )

    is_email_verified = models.BooleanField(
        default=False
    )

    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = ["phone"]

    objects = UserManager()

    def __str__(self):

        return self.email


from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class UserProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    phone = models.CharField(
        max_length=15,
        blank=True,
        null=True
    )

    address = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.user.email