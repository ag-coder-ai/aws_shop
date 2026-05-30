from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model

from .models import UserProfile

User = get_user_model()

# =========================================================
# USER PROFILE INLINE (FOR USER PAGE)
# =========================================================

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    extra = 0
    verbose_name_plural = "Profile"


# =========================================================
# USER ADMIN (INDUSTRY STANDARD)
# =========================================================

@admin.register(User)
class UserAdmin(BaseUserAdmin):

    inlines = (UserProfileInline,)

    list_display = (
        "id",
        "email",
        "full_name",
        "phone",
        "is_active",
        "is_staff",
        "is_superuser",
        "is_email_verified",
    )

    list_filter = (
        "is_active",
        "is_staff",
        "is_superuser",
        "is_email_verified",
        "groups",
    )

    search_fields = (
        "email",
        "phone",
        "full_name",
    )

    ordering = ("-id",)

    # -------------------------
    # DISPLAY FIELDS
    # -------------------------
    fieldsets = (
        ("Login Credentials", {
            "fields": ("email", "password")
        }),

        ("Personal Information", {
            "fields": ("full_name", "phone")
        }),

        ("Permissions", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "is_email_verified",
                "groups",
                "user_permissions",
            )
        }),

        ("Important Dates", {
            "fields": ("last_login", "date_joined")
        }),
    )

    # -------------------------
    # ADD USER FORM (CREATE)
    # -------------------------
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email",
                "phone",
                "full_name",
                "password1",
                "password2",
                "is_active",
                "is_staff",
            ),
        }),
    )


# =========================================================
# USER PROFILE ADMIN
# =========================================================

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "phone",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "user__email",
        "user__full_name",
        "phone",
    )

    list_filter = (
        "created_at",
        "updated_at",
    )

    ordering = ("-created_at",)

    autocomplete_fields = ("user",)

    fieldsets = (
        ("User Link", {
            "fields": ("user",)
        }),

        ("Contact Details", {
            "fields": ("phone", "address")
        }),

        ("Timestamps", {
            "fields": ("created_at", "updated_at")
        }),
    )