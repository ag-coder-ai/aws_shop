# orders/models.py

from django.db import models
from django.conf import settings
from decimal import Decimal
from django.utils import timezone
import re
from django.db import transaction
from products.models import ProductVariant
from django.core.validators import validate_email

from django.core.exceptions import ValidationError

# =========================================================
# ENUMS
# =========================================================

class PaymentMethod(models.TextChoices):
    COD = "COD", "Cash On Delivery"
    PREPAID = "PREPAID", "Prepaid"


class PaymentStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    PAID = "PAID", "Paid"
    FAILED = "FAILED", "Failed"
    REFUNDED = "REFUNDED", "Refunded"


class OrderStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    CONFIRMED = "CONFIRMED", "Confirmed"
    PROCESSING = "PROCESSING", "Processing"
    SHIPPED = "SHIPPED", "Shipped"
    DELIVERED = "DELIVERED", "Delivered"
    CANCELLED = "CANCELLED", "Cancelled"
    RETURN_REQUESTED = "RETURN_REQUESTED", "Return Requested"
    RETURN_APPROVED = "RETURN_APPROVED", "Return Approved"
    RETURN_REJECTED = "RETURN_REJECTED", "Return Rejected"
    RETURN_PICKED = "RETURN_PICKED", "Return Picked"
    REFUNDED = "REFUNDED", "Refunded"


class ShippingStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    PACKED = "PACKED", "Packed"
    SHIPPED = "SHIPPED", "Shipped"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY", "Out For Delivery"
    DELIVERED = "DELIVERED", "Delivered"


# =========================================================
# ORDER
# =========================================================

class Order(models.Model):

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders")
    order_id = models.CharField(max_length=20, unique=True)

    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.COD)
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)

    status = models.CharField(max_length=30, choices=OrderStatus.choices, default=OrderStatus.PENDING)
    shipping_status = models.CharField(max_length=30, choices=ShippingStatus.choices, default=ShippingStatus.PENDING)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    shipping_charge = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    courier_partner = models.CharField(max_length=100, blank=True, null=True)
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    estimated_delivery = models.DateField(blank=True, null=True)

    shipped_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # =========================
    # REFUND INFO (MANUAL)
    # =========================

    refund_status = models.CharField(
        max_length=20,
        choices=[
            ("NOT_REQUESTED", "Not Requested"),
            ("REQUESTED", "Requested"),
            ("APPROVED", "Approved"),
            ("COMPLETED", "Completed"),
            ("REJECTED", "Rejected"),
        ],
        default="NOT_REQUESTED"
    )

    refund_method = models.CharField(
        max_length=20,
        choices=[
            ("UPI", "UPI"),
            ("BANK", "Bank Transfer"),
            ("WALLET", "Wallet"),
            ("CASH", "Cash Adjustment"),
        ],
        blank=True,
        null=True
    )

    refund_reference = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    refunded_at = models.DateTimeField(
        blank=True,
        null=True
    )

    def cancel_order(self):
        from django.core.exceptions import ValidationError

        if self.status in ["DELIVERED", "CANCELLED"]:
            raise ValidationError("Order cannot be cancelled")

        with transaction.atomic():

            # restore stock
            for item in self.items.all():
                variant = ProductVariant.objects.select_for_update().get(
                    id=item.variant_id
                )

                variant.stock_quantity += item.quantity
                variant.save()

            # update order
            self.status = "CANCELLED"
            self.shipping_status = "CANCELLED"
            self.save()

    # =========================
    # HELPERS
    # =========================

    def mark_shipped(self):
        self.shipping_status = ShippingStatus.SHIPPED
        self.status = OrderStatus.SHIPPED
        self.shipped_at = timezone.now()
        self.save()

        ShipmentEvent.objects.create(
            order=self,
            status="SHIPPED",
            message="Order shipped via courier"
        )

    def mark_delivered(self):
        self.shipping_status = ShippingStatus.DELIVERED
        self.status = OrderStatus.DELIVERED
        self.delivered_at = timezone.now()
        self.save()

        ShipmentEvent.objects.create(
            order=self,
            status="DELIVERED",
            message="Order delivered"
        )

    from django.utils import timezone

    def mark_refund_requested(self):
        self.refund_status = "REQUESTED"
        self.save()

    def mark_refunded(self, method, reference=None):
        self.refund_status = "COMPLETED"
        self.refund_method = method
        self.refund_reference = reference
        self.refunded_at = timezone.now()

        self.payment_status = "REFUNDED"
        self.status = "REFUNDED"

        self.save()

    def save(self, *args, **kwargs):

        is_update = self.pk is not None

        old_shipping_status = None

        if is_update:
            old_order = Order.objects.get(pk=self.pk)

            old_shipping_status = (
                old_order.shipping_status
            )

        # SAVE FIRST
        super().save(*args, **kwargs)

        # =========================================
        # SHIPPING STATUS CHANGED
        # =========================================

        if (
                is_update
                and
                old_shipping_status != self.shipping_status
        ):

            from .services import send_order_email

            # =====================================
            # SHIPPED
            # =====================================

            if self.shipping_status == "SHIPPED":

                send_order_email(

                    order=self,

                    subject="Your Order Has Been Shipped 🚚",

                    template_name=(
                        "orders/shipped.html"
                    )
                )

            # =====================================
            # OUT FOR DELIVERY
            # =====================================

            elif (
                    self.shipping_status
                    ==
                    "OUT_FOR_DELIVERY"
            ):

                send_order_email(

                    order=self,

                    subject="Out For Delivery 🚛",

                    template_name=(
                        "orders/out_for_delivery.html"
                    )
                )

            # =====================================
            # DELIVERED
            # =====================================

            elif self.shipping_status == "DELIVERED":

                send_order_email(

                    order=self,

                    subject="Order Delivered ✅",

                    template_name=(
                        "orders/delivered.html"
                    )
                )

            # =====================================
            # RETURNED
            # =====================================

            elif self.shipping_status == "RETURNED":

                send_order_email(

                    order=self,

                    subject="Order Returned",

                    template_name=(
                        "orders/refunded.html"
                    )
                )

    def __str__(self):
        return self.order_id




# =========================================================
# ORDER ITEM
# =========================================================

class OrderItem(models.Model):

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")

    product_name = models.CharField(max_length=255)
    product_image = models.ImageField(upload_to="orders/products/", blank=True, null=True)

    variant_id = models.IntegerField()
    sku = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    size = models.CharField(max_length=50)
    color = models.CharField(max_length=50)

    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    @property
    def total_price(self):
        return (self.price or Decimal("0")) * (self.quantity or 0)

    def __str__(self):
        return f"{self.product_name}"


# =========================================================
# SHIPPING ADDRESS
# =========================================================

import re

from django.db import models

from django.core.exceptions import ValidationError

from django.core.validators import validate_email


class ShippingAddress(models.Model):

    order = models.OneToOneField(

        "Order",

        on_delete=models.CASCADE,

        related_name="shipping_address"
    )

    full_name = models.CharField(
        max_length=120
    )

    phone = models.CharField(
        max_length=10
    )

    email = models.EmailField()

    address_line_1 = models.CharField(
        max_length=255
    )

    address_line_2 = models.CharField(

        max_length=255,

        blank=True,

        null=True
    )

    city = models.CharField(
        max_length=100
    )

    state = models.CharField(
        max_length=100
    )

    postal_code = models.CharField(
        max_length=6
    )

    country = models.CharField(

        max_length=100,

        default="India"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    # =====================================================
    # META
    # =====================================================

    class Meta:

        verbose_name = "Shipping Address"

        verbose_name_plural = "Shipping Addresses"

        ordering = ["-created_at"]

        indexes = [

            models.Index(fields=["postal_code"]),

            models.Index(fields=["phone"]),

            models.Index(fields=["email"]),

        ]

    # =====================================================
    # VALIDATIONS
    # =====================================================

    def clean(self):

        errors = {}

        # =========================================
        # NORMALIZE VALUES
        # =========================================

        self.full_name = (
            self.full_name or ""
        ).strip()

        self.phone = (
            self.phone or ""
        ).strip()

        self.email = (
            self.email or ""
        ).strip().lower()

        self.address_line_1 = (
            self.address_line_1 or ""
        ).strip()

        self.address_line_2 = (
            self.address_line_2 or ""
        ).strip()

        self.city = (
            self.city or ""
        ).strip()

        self.state = (
            self.state or ""
        ).strip()

        self.postal_code = (
            self.postal_code or ""
        ).strip()

        self.country = (
            self.country or ""
        ).strip()

        # =========================================
        # INDIA ONLY
        # =========================================

        if self.country.lower() != "india":

            errors["country"] = (
                "Currently delivery is available only within India."
            )

        # =========================================
        # FULL NAME VALIDATION
        # =========================================

        if not self.full_name:

            errors["full_name"] = (
                "Full name is required."
            )

        elif len(self.full_name) < 3:

            errors["full_name"] = (
                "Enter valid full name."
            )

        elif not re.match(

            r"^[A-Za-z\s\d\.]+$",

            self.full_name

        ):

            errors["full_name"] = (
                "Full name can contain only letters."
            )

        # =========================================
        # PHONE VALIDATION
        # =========================================

        phone = re.sub(
            r"\D",
            "",
            self.phone
        )

        # REMOVE COUNTRY CODE

        if phone.startswith("91") and len(phone) == 12:

            phone = phone[2:]

        if not phone:

            errors["phone"] = (
                "Mobile number is required."
            )

        elif not re.match(
            r"^[6-9]\d{9}$",
            phone
        ):

            errors["phone"] = (
                "Enter valid Indian mobile number."
            )

        # BLOCK FAKE NUMBERS

        blocked_numbers = [

            "9999999999",
            "8888888888",
            "7777777777",
            "6666666666",
            "9876543210",

        ]

        if phone in blocked_numbers:

            errors["phone"] = (
                "Enter valid mobile number."
            )

        self.phone = phone

        # =========================================
        # EMAIL VALIDATION
        # =========================================

        if not self.email:

            errors["email"] = (
                "Email address is required."
            )

        else:

            # REMOVE SPACES

            self.email = self.email.replace(
                " ",
                ""
            )

            try:

                validate_email(self.email)

            except ValidationError:

                errors["email"] = (
                    "Enter valid email address."
                )

            # =====================================
            # BLOCK DISPOSABLE EMAILS
            # =====================================

            blocked_domains = [

                "tempmail.com",
                "10minutemail.com",
                "mailinator.com",
                "guerrillamail.com",
                "yopmail.com",
                "trashmail.com",
                "fakeinbox.com",
                "sharklasers.com",

            ]

            domain = self.email.split("@")[-1]

            if domain in blocked_domains:

                errors["email"] = (
                    "Disposable email addresses are not allowed."
                )

        # =========================================
        # ADDRESS VALIDATION
        # =========================================

        if not self.address_line_1:

            errors["address_line_1"] = (
                "Address is required."
            )

        elif len(self.address_line_1) < 10:

            errors["address_line_1"] = (
                "Please enter complete address."
            )

        elif len(self.address_line_1) > 255:

            errors["address_line_1"] = (
                "Address is too long."
            )

        # =========================================
        # CITY VALIDATION
        # =========================================

        if not self.city:

            errors["city"] = (
                "City is required."
            )

        elif len(self.city) < 2:

            errors["city"] = (
                "Enter valid city."
            )

        elif not re.match(
            r"^[A-Za-z\s\-]+$",
            self.city
        ):

            errors["city"] = (
                "Enter valid city name."
            )

        # =========================================
        # STATE VALIDATION
        # =========================================

        if not self.state:

            errors["state"] = (
                "State is required."
            )

        elif len(self.state) < 2:

            errors["state"] = (
                "Enter valid state."
            )

        elif not re.match(
            r"^[A-Za-z\s\-]+$",
            self.state
        ):

            errors["state"] = (
                "Enter valid state name."
            )

        # =========================================
        # PINCODE VALIDATION
        # =========================================

        if not self.postal_code:

            errors["postal_code"] = (
                "Pincode is required."
            )

        elif not re.match(
            r"^\d{6}$",
            self.postal_code
        ):

            errors["postal_code"] = (
                "Enter valid 6 digit pincode."
            )

        # =========================================
        # SERVICEABLE PINCODE CHECK
        # =========================================

        # Replace later with:
        # Shiprocket / Delhivery API

        blocked_pincodes = [

            "744301",
            "744302",

        ]

        if self.postal_code in blocked_pincodes:

            errors["postal_code"] = (
                "Delivery is currently unavailable for this pincode."
            )

        # =========================================
        # FINAL VALIDATION
        # =========================================

        if errors:

            raise ValidationError(errors)

    # =====================================================
    # AUTO VALIDATE BEFORE SAVE
    # =====================================================

    def save(self, *args, **kwargs):

        self.full_clean()

        super().save(*args, **kwargs)

    # =====================================================
    # STRING REPRESENTATION
    # =====================================================

    def __str__(self):

        return (
            f"{self.full_name} "
            f"- {self.postal_code}"
        )

class Pincode(models.Model):
    pin_code = models.CharField(max_length=6, unique=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.pin_code} - {self.city}"
# =========================================================
# SHIPMENT EVENTS (TRACKING TIMELINE)
# =========================================================

class ShipmentEvent(models.Model):

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="events")
    status = models.CharField(max_length=100)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.order.order_id} - {self.status}"


# =========================================================
# RETURN SYSTEM
# =========================================================
from django.utils import timezone
from .services import send_order_email


class OrderReturn(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="returns"
    )

    reason = models.CharField(max_length=255)
    comment = models.TextField(blank=True, null=True)

    status = models.CharField(
        max_length=30,
        choices=[
            ("REQUESTED", "Requested"),
            ("APPROVED", "Approved"),
            ("REJECTED", "Rejected"),
            ("PICKUP_SCHEDULED", "Pickup Scheduled"),
            ("PICKED", "Picked"),
            ("RECEIVED", "Received"),
            ("REFUNDED", "Refunded"),
        ],
        default="REQUESTED"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Return {self.order.order_id}"

    # =========================================
    # SAVE WITH EMAIL + STATUS FLOW
    # =========================================

    def save(self, *args, **kwargs):

        is_update = self.pk is not None
        old_status = None

        if is_update:
            old_status = (
                OrderReturn.objects.get(pk=self.pk).status
            )

        super().save(*args, **kwargs)

        # ONLY TRIGGER IF STATUS CHANGED
        if is_update and old_status != self.status:

            # =====================================
            # REQUESTED
            # =====================================
            if self.status == "REQUESTED":

                self.order.status = "RETURN_REQUESTED"
                self.order.save()

            # =====================================
            # APPROVED
            # =====================================
            elif self.status == "APPROVED":

                self.order.status = "RETURN_APPROVED"
                self.order.save()

                send_order_email(
                    self.order,
                    "Return Request Approved ✅",
                    "orders/return_approved.html"
                )

            # =====================================
            # PICKUP SCHEDULED
            # =====================================
            elif self.status == "PICKUP_SCHEDULED":

                self.order.status = "RETURN_PICKUP_SCHEDULED"
                self.order.save()

                send_order_email(
                    self.order,
                    "Return Pickup Scheduled 🚚",
                    "orders/return_pickup_scheduled.html"
                )

            # =====================================
            # PICKED
            # =====================================
            elif self.status == "PICKED":

                self.order.status = "RETURN_PICKED"
                self.order.save()

                send_order_email(
                    self.order,
                    "Return Picked Successfully 📦",
                    "orders/return_picked.html"
                )

            # =====================================
            # RECEIVED (WAREHOUSE)
            # =====================================
            elif self.status == "RECEIVED":

                self.order.status = "RETURN_RECEIVED"
                self.order.save()

                send_order_email(
                    self.order,
                    "Return Received at Warehouse 🏬",
                    "orders/return_received.html"
                )

            # =====================================
            # REFUNDED
            # =====================================
            elif self.status == "REFUNDED":

                self.order.status = "REFUNDED"
                self.order.payment_status = "REFUNDED"
                self.order.save()

                send_order_email(
                    self.order,
                    "Refund Completed 💰",
                    "orders/refunded.html"
                )