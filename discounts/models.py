from django.db import models

# Create your models here.
from django.db import models
from django.utils import timezone

class Coupon(models.Model):

    DISCOUNT_TYPES = (
        ("PERCENT", "Percentage"),
        ("FIXED", "Fixed Amount"),
    )

    code = models.CharField(max_length=50, unique=True)

    discount_type = models.CharField(
        max_length=20,
        choices=DISCOUNT_TYPES
    )

    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    min_purchase = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    max_discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    active = models.BooleanField(default=True)

    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()

    usage_limit = models.PositiveIntegerField(default=100)
    used_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)



    def __str__(self):
        return self.code

    def is_valid(self):
        now = timezone.now()

        if not self.active:
            return False

        if self.valid_from > now or self.valid_to < now:
            return False

        if self.used_count >= self.usage_limit:
            return False

        return True