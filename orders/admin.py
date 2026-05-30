# orders/admin.py

from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Order,
    OrderItem,
    ShippingAddress,
    ShipmentEvent,
    OrderReturn
)


# =========================
# ORDER ITEM INLINE
# =========================

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product_preview", "product_name", "size", "color", "price", "quantity", "item_total")

    def product_preview(self, obj):
        if obj.product_image:
            return format_html('<img src="{}" width="50"/>', obj.product_image.url)
        return "-"

    def item_total(self, obj):
        return obj.total_price


# =========================
# EVENTS INLINE
# =========================

class ShipmentEventInline(admin.TabularInline):
    model = ShipmentEvent
    extra = 0
    readonly_fields = ("status", "message", "created_at")


# =========================
# RETURN INLINE
# =========================

class OrderReturnInline(admin.TabularInline):
    model = OrderReturn
    extra = 0
    readonly_fields = ("reason", "comment", "status", "created_at")

class ShippingAddressInline(admin.StackedInline):

    model = ShippingAddress

    extra = 0

    can_delete = False

    readonly_fields = ()

    fieldsets = (

        ("Customer Information", {

            "fields": (

                "full_name",
                "phone",
                "email",

            )

        }),

        ("Shipping Address", {

            "fields": (

                "address_line_1",
                "address_line_2",
                "city",
                "state",
                "postal_code",
                "country",

            )

        }),

    )

# =========================
# ORDER ADMIN
# =========================

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = ("order_id", "status", "shipping_status", "tracking_number", "total", "created_at")

    list_filter = ("status", "shipping_status", "payment_status")

    search_fields = ("order_id", "tracking_number")

    inlines = [

        ShippingAddressInline,

        OrderItemInline,

        ShipmentEventInline,

        OrderReturnInline

    ]


# =========================================================
# RETURN ADMIN
# =========================================================

@admin.register(OrderReturn)
class OrderReturnAdmin(admin.ModelAdmin):

    list_display = (

        "id",

        "order",

        "reason",

        "status_badge",

        "created_at",

    )

    list_filter = (

        "status",

        "created_at",

    )

    search_fields = (

        "order__order_id",

        "reason",

    )

    readonly_fields = (

        "order",

        "reason",

        "comment",

        "created_at",

    )

    actions = [

        "approve_returns",

        "reject_returns",

        "mark_picked",

        "mark_refunded",

        "mark_refund_completed",

    ]

    fieldsets = (

        ("Return Information", {

            "fields": (

                "order",

                "reason",

                "comment",

                "status",

            )

        }),

        ("Timeline", {

            "fields": (

                "created_at",

            )

        }),

    )

    # =====================================================
    # STATUS BADGE
    # =====================================================

    def status_badge(self, obj):

        colors = {

            "REQUESTED": "#f59e0b",

            "APPROVED": "#3b82f6",

            "REJECTED": "#ef4444",

            "PICKED": "#8b5cf6",

            "REFUNDED": "#10b981",

        }

        return format_html(

            '''
            <span style="
                background:{};
                color:white;
                padding:6px 12px;
                border-radius:30px;
                font-size:12px;
                font-weight:600;
            ">
                {}
            </span>
            ''',

            colors.get(obj.status, "#111827"),

            obj.status

        )

    status_badge.short_description = "Status"

    # =====================================================
    # APPROVE RETURN
    # =====================================================

    def approve_returns(self, request, queryset):

        for obj in queryset:

            obj.status = "APPROVED"
            obj.order.status = "RETURN_APPROVED"

            obj.order.save()
            obj.save()

        self.message_user(
            request,
            "Selected returns approved successfully."
        )

    approve_returns.short_description = (
        "Approve selected returns"
    )

    # =====================================================
    # REJECT RETURN
    # =====================================================

    def reject_returns(self, request, queryset):

        for obj in queryset:

            obj.status = "REJECTED"
            obj.order.status = "RETURN_REJECTED"

            obj.order.save()
            obj.save()

        self.message_user(
            request,
            "Selected returns rejected."
        )

    reject_returns.short_description = (
        "Reject selected returns"
    )

    # =====================================================
    # MARK RETURN PICKED
    # =====================================================

    def mark_picked(self, request, queryset):

        for obj in queryset:

            obj.status = "PICKED"
            obj.order.status = "RETURN_PICKED"

            obj.order.save()
            obj.save()

        self.message_user(
            request,
            "Selected returns marked as picked."
        )

    mark_picked.short_description = (
        "Mark selected returns picked"
    )


    # =====================================================
    # MARK REFUNDED
    # =====================================================

    def mark_refund_completed(self, request, queryset):

        for obj in queryset:
            obj.order.mark_refunded(
                method="UPI",
                reference="MANUAL_REFUND"
            )

        self.message_user(
            request,
            "Refund marked as completed successfully."
        )