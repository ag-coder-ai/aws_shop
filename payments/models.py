# payments/models.py

from django.db import models
from orders.models import Order
from django.db import models

from django.conf import settings
class Payment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    order = models.OneToOneField(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    razorpay_order_id = models.CharField(max_length=100)
    razorpay_payment_id = models.CharField(max_length=100, null=True, blank=True)
    payment_reference = models.CharField(max_length=120, unique=True, null=True, blank=True)
    razorpay_event_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        unique=True
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    cart_snapshot = models.TextField(null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=[
            ("CREATED", "Created"),
            ("SUCCESS", "Success"),
            ("FAILED", "Failed"),
        ],
        default="CREATED"
    )

    created_at = models.DateTimeField(auto_now_add=True)
