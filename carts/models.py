from django.db import models
from django.conf import settings
from decimal import Decimal

from products.models import ProductVariant


# =========================================================
# CART
# =========================================================

from django.db.models import F, Sum, ExpressionWrapper, DecimalField
from decimal import Decimal


class Cart(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ============================
    # FAST SUBTOTAL (DB LEVEL)
    # ============================
    @property
    def subtotal(self):

        result = self.items.aggregate(
            total=Sum(
                ExpressionWrapper(
                    F('quantity') * F('variant__wholesale_price'),
                    output_field=DecimalField()
                )
            )
        )['total']

        return result or Decimal("0.00")

    # ============================
    # TOTAL ITEMS
    # ============================
    @property
    def total_items(self):

        return self.items.aggregate(
            total=Sum('quantity')
        )['total'] or 0

    # ============================
    # FINAL TOTAL
    # ============================
    @property
    def total_amount(self):

        return self.subtotal
# =========================================================
# CART ITEM
# =========================================================

class CartItem(models.Model):

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )

    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name='cart_items'
    )

    quantity = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)

    # ----------------------------
    # NEW: MODERN CONSTRAINT (replaces unique_together)
    # ----------------------------
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['cart', 'variant'],
                name='unique_cart_variant'
            )
        ]

    def __str__(self):
        return f"{self.variant} x {self.quantity}"

    # ----------------------------
    # ITEM TOTAL
    # ----------------------------
    @property
    def total_price(self):
        if not self.variant:
            return Decimal("0.00")

        return self.quantity * self.variant.wholesale_price