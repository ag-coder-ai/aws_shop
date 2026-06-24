from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import Coupon
from django.utils import timezone


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):

    list_display = (
        "code",
        "discount_type",
        "discount_value",
        "min_purchase",
        "max_discount",
        "usage_limit",
        "used_count",
        "active",
        "valid_from",
        "valid_to",
        "is_expired",
    )

    list_filter = (
        "active",
        "discount_type",
        "valid_from",
        "valid_to",
    )

    search_fields = ("code",)

    ordering = ("-created_at",)

    readonly_fields = ("used_count", "created_at")

    fieldsets = (
        ("Coupon Details", {
            "fields": (
                "code",
                "discount_type",
                "discount_value",
            )
        }),

        ("Rules", {
            "fields": (
                "min_purchase",
                "max_discount",
                "usage_limit",
                "used_count",
            )
        }),

        ("Validity", {
            "fields": (
                "active",
                "valid_from",
                "valid_to",
            )
        }),

        ("System Info", {
            "fields": (
                "created_at",
            )
        }),
    )

    def is_expired(self, obj):
        now = timezone.now()
        return obj.valid_to < now

    is_expired.boolean = True
    is_expired.short_description = "Expired?"