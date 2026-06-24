from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Payment
from django.utils.html import format_html

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):

    # ✅ Clean table view
    list_display = (
        "id",
        "user",
        "order",
        "razorpay_order_id",
        "razorpay_payment_id",
        "amount",
        "status",
        "created_at",
    )

    # 🎯 Filters on the right side
    list_filter = (
        "status",
        "created_at",
        "user",
    )

    # 🔎 Search bar
    search_fields = (
        "razorpay_order_id",
        "razorpay_payment_id",
        "payment_reference",
        "user__username",
        "order__order_id",
    )

    # 👀 Click to view only (no edit)
    readonly_fields = (
        "user",
        "order",
        "razorpay_order_id",
        "razorpay_payment_id",
        "payment_reference",
        "amount",
        "status",
        "created_at",
    )

    # 🎨 Nice grouping layout
    fieldsets = (
        ("👤 User & Order Info", {
            "fields": ("user", "order")
        }),
        ("💳 Razorpay Details", {
            "fields": ("razorpay_order_id", "razorpay_payment_id", "payment_reference")
        }),
        ("💰 Payment Info", {
            "fields": ("amount", "status")
        }),
        ("📅 Timestamps", {
            "fields": ("created_at",)
        }),
    )

    # 🚀 Better UI behavior
    ordering = ("-created_at",)
    list_per_page = 20

    # 🟢 Colored status (nice UI improvement)
    def status_tag(self, obj):
        colors = {
            "SUCCESS": "green",
            "FAILED": "red",
            "CREATED": "orange",
        }
        color = colors.get(obj.status, "black")
        return format_html(
            f'<span style="color:white;background:{color};padding:3px 8px;border-radius:6px;">{obj.status}</span>'
        )

    status_tag.short_description = "Status"