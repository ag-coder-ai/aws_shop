from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from carts.models import Cart
from discounts.models import Coupon
from discounts.services import CouponService

@login_required
def apply_coupon(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid request"}, status=400)

    code = request.POST.get("coupon_code", "").strip()

    if not code:
        return JsonResponse({"success": False, "message": "Coupon code required"}, status=400)

    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        return JsonResponse({"success": False, "message": "Cart not found"}, status=400)

    if not cart.items.exists():
        return JsonResponse({"success": False, "message": "Cart is empty"}, status=400)

    try:
        from discounts.services import CouponService

        coupon, discount, final_total, message = CouponService.apply_coupon(
            cart.total_amount,
            code,
            user=request.user
        )

        return JsonResponse({
            "success": coupon is not None,
            "coupon": coupon.code if coupon else None,
            "discount": float(discount),
            "final_total": float(final_total),
            "message": message
        }, status=200 if coupon else 400)

    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": str(e)
        }, status=400)



