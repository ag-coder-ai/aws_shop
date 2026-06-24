from decimal import Decimal
from django.utils import timezone
from discounts.models import Coupon



class CouponService:

    @staticmethod
    def apply_coupon(cart_total, coupon_code, user=None):

        if not coupon_code:
            return None, Decimal("0.00"), cart_total, "No coupon applied"

        coupon = Coupon.objects.filter(
            code__iexact=coupon_code.strip(),
            active=True
        ).first()

        if not coupon:
            return None, Decimal("0.00"), cart_total, "❌ Invalid coupon code"

        now = timezone.now()

        if coupon.valid_from and now < coupon.valid_from:
            return None, Decimal("0.00"), cart_total, "⏳ Coupon not active yet"

        if coupon.valid_to and now > coupon.valid_to:
            return None, Decimal("0.00"), cart_total, "⚠️ Coupon has expired"

        if cart_total < coupon.min_purchase:
            return None, Decimal("0.00"), cart_total, f"🛒 Minimum order ₹{coupon.min_purchase} required"

        if coupon.used_count >= coupon.usage_limit:
            return None, Decimal("0.00"), cart_total, "🚫 Coupon usage limit reached"

        discount = Decimal("0.00")

        if coupon.discount_type == "PERCENT":
            discount = (cart_total * coupon.discount_value) / Decimal("100")
            if coupon.max_discount:
                discount = min(discount, coupon.max_discount)

        elif coupon.discount_type == "FIXED":
            discount = coupon.discount_value

        final_total = max(cart_total - discount, Decimal("0.00"))

        return coupon, discount, final_total, "🎉 Coupon applied successfully"