from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from products.models import ProductVariant
from .models import Cart, CartItem


# =========================================================
# ADD TO CART (API)
# =========================================================
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

@require_POST
def add_to_cart(request):

    # =====================================
    # LOGIN CHECK
    # =====================================

    if not request.user.is_authenticated:

        return JsonResponse({
            "success": False,
            "login_required": True,
            "message": "Please login to continue"
        }, status=401)

    variant_id = request.POST.get("variant_id")
    quantity = int(request.POST.get("quantity", 1))

    variant = get_object_or_404(
        ProductVariant.objects.select_related(
            "product",
            "size",
            "color"
        ),
        id=variant_id,
        is_active=True
    )

    # =====================================
    # STOCK CHECK
    # =====================================

    if variant.stock_quantity <= 0:

        return JsonResponse({
            "success": False,
            "message": "Out of stock"
        })

    if quantity > variant.stock_quantity:

        return JsonResponse({
            "success": False,
            "message": "Not enough stock"
        })

    # =====================================
    # CART
    # =====================================

    cart, _ = Cart.objects.get_or_create(
        user=request.user
    )

    item, created = CartItem.objects.get_or_create(
        cart=cart,
        variant=variant,
        defaults={
            "quantity": quantity
        }
    )

    if not created:

        new_qty = item.quantity + quantity

        if new_qty > variant.stock_quantity:

            return JsonResponse({
                "success": False,
                "message": "Stock limit exceeded"
            })

        item.quantity = new_qty
        item.save()

    return JsonResponse({

        "success": True,

        "message": "Added to cart successfully",

        "data": {

            "cart_count": cart.items.count(),

            "item_id": item.id,

            "quantity": item.quantity,

            "item_total": float(item.total_price),

            "cart_total": float(cart.total_amount)

        }

    })

# =========================================================
# CART PAGE
# =========================================================

@login_required

def cart_view(request):

    cart, _ = Cart.objects.get_or_create(user=request.user)

    items = (
        cart.items
        .select_related(
            "variant__product",
            "variant__size",
            "variant__color"
        )
        .all()
    )

    return render(request, "carts/carts.html", {
        "cart": cart,
        "items": items
    })


# =========================================================
# UPDATE QUANTITY (AJAX)
# =========================================================

from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from decimal import Decimal
@login_required
@require_POST
def update_cart_quantity(request):

    item_id = request.POST.get("item_id")
    action = request.POST.get("action")

    cart_item = get_object_or_404(
        CartItem.objects.select_related("variant", "cart"),
        id=item_id,
        cart__user=request.user
    )

    if action == "increase":
        if cart_item.quantity >= cart_item.variant.stock_quantity:
            return JsonResponse({"success": False, "message": "Stock limit reached"})
        cart_item.quantity += 1

    elif action == "decrease":
        if cart_item.quantity > 1:
            cart_item.quantity -= 1

    cart_item.save()

    # 🔥 FORCE FRESH CART FROM DB (IMPORTANT FIX)
    cart = Cart.objects.prefetch_related("items__variant").get(id=cart_item.cart.id)

    subtotal = cart.items.aggregate(
        total=Sum(
            ExpressionWrapper(
                F("quantity") * F("variant__wholesale_price"),
                output_field=DecimalField()
            )
        )
    )["total"] or Decimal("0.00")

    return JsonResponse({
        "success": True,
        "data": {
            "item_id": cart_item.id,
            "quantity": cart_item.quantity,
            "item_total": float(cart_item.total_price),
            "cart_total": float(cart.total_amount),
            "cart_subtotal": float(cart.subtotal),
            "cart_count": cart.total_items  # 🔥 MUST EXIST
        }
    })

@login_required
@require_POST
def remove_cart_item(request):

    item_id = request.POST.get("item_id")

    cart_item = get_object_or_404(
        CartItem,
        id=item_id,
        cart__user=request.user
    )

    cart = cart_item.cart
    cart_item.delete()

    subtotal = cart.items.aggregate(
        total=Sum(
            ExpressionWrapper(
                F("quantity") * F("variant__wholesale_price"),
                output_field=DecimalField()
            )
        )
    )["total"] or Decimal("0.00")

    return JsonResponse({
        "success": True,
        "data": {
            "cart_total": float(cart.total_amount),
            "cart_subtotal": float(cart.subtotal),
            "cart_count": cart.total_items  # 🔥 MUST ADD
        }
    })


@login_required
def cart_summary(request):

    cart, _ = Cart.objects.get_or_create(user=request.user)

    return JsonResponse({
        "success": True,
        "data": {
            "cart_total": float(cart.total_amount),
            "cart_subtotal": float(cart.subtotal),
            "cart_count": cart.total_items
        }
    })