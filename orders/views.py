
import json
import uuid
from django.http import JsonResponse
from django.shortcuts import render,redirect
from django.db import transaction
from django.contrib.auth.decorators import login_required
from carts.models import Cart
from .models import (
    Order,
    OrderItem,
    PaymentMethod,
    PaymentStatus,
    OrderStatus,
    ShippingAddress
)
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from orders.utils.order_id import generate_order_id

from django.core.exceptions import ValidationError

from .services import send_order_email

@login_required
def checkout_view(request):

    cart = Cart.objects.prefetch_related("items__variant").get(user=request.user)

    if cart.items.count() == 0:
        return redirect("carts")

    return render(request, "orders/checkout.html", {
        "cart": cart,
        "items": cart.items.all()
    })

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from django.core.exceptions import ValidationError

from .models import Order, OrderItem, ShippingAddress
from products.models import ProductVariant, InventoryLog
from orders.models import OrderItem
from orders.services import send_order_email
@login_required
@transaction.atomic
def create_checkout(request):

    if request.method != "POST":

        return JsonResponse({
            "success": False,
            "message": "Invalid request"
        })

    data = request.POST

    try:

        cart = Cart.objects.prefetch_related(
            "items__variant",
            "items__variant__product",
            "items__variant__size",
            "items__variant__color",
            "items__variant__product__images"
        ).get(user=request.user)

    except Cart.DoesNotExist:

        return JsonResponse({
            "success": False,
            "message": "Cart not found"
        })

    # =========================================
    # EMPTY CART CHECK
    # =========================================

    if not cart.items.exists():

        return JsonResponse({
            "success": False,
            "message": "Cart is empty"
        })

    payment_method = data.get("payment_method")

    # =========================================
    # STORE CHECKOUT DATA IN SESSION
    # =========================================

    request.session["checkout_data"] = {

        "full_name": data.get("full_name"),

        "phone": data.get("phone"),

        "email": data.get("email"),

        "address": data.get("address"),

        "city": data.get("city"),

        "state": data.get("state"),

        "pincode": data.get("pincode"),

        "payment_method": payment_method,
    }

    # =========================================
    # COD PAYMENT
    # =========================================

    if payment_method == "COD":

        # =========================================
        # CREATE ORDER
        # =========================================

        order = Order.objects.create(

            user=request.user,

            order_id=generate_order_id(),

            subtotal=cart.subtotal,

            total=cart.total_amount,

            payment_method="COD",

            payment_status=PaymentStatus.PENDING,

            status=OrderStatus.CONFIRMED
        )

        # =========================================
        # CREATE SHIPPING ADDRESS
        # =========================================

        try:

            ShippingAddress.objects.create(

                order=order,

                full_name=data.get("full_name"),

                phone=data.get("phone"),

                email=data.get("email"),

                address_line_1=data.get("address"),

                city=data.get("city"),

                state=data.get("state"),

                postal_code=data.get("pincode"),

                country="India"
            )

        except ValidationError as e:

            transaction.set_rollback(True)

            return JsonResponse({

                "success": False,

                "field_errors": e.message_dict

            }, status=400)

        # =========================================
        # CREATE ORDER ITEMS + REDUCE STOCK
        # =========================================

        for item in cart.items.select_related(
            "variant",
            "variant__product",
            "variant__size",
            "variant__color"
        ):

            variant = ProductVariant.objects.select_for_update().get(
                id=item.variant.id
            )

            # =========================================
            # STOCK CHECK
            # =========================================

            if variant.stock_quantity < item.quantity:

                transaction.set_rollback(True)

                return JsonResponse({

                    "success": False,

                    "message": (
                        f"{variant.product.name} "
                        f"does not have enough stock"
                    )

                })

            # =========================================
            # REDUCE STOCK
            # =========================================

            variant.stock_quantity -= item.quantity

            variant.save()

            # =========================================
            # CREATE ORDER ITEM
            # =========================================

            OrderItem.objects.create(

                order=order,

                product_name=variant.product.name,

                product_image=(
                    variant.product.primary_image.image
                    if variant.product.primary_image
                    else None
                ),

                variant_id=variant.id,

                sku=variant.sku,

                size=variant.size.name,

                color=variant.color.name,

                price=variant.wholesale_price,

                quantity=item.quantity
            )

            # =========================================
            # INVENTORY LOG
            # =========================================

            InventoryLog.objects.create(

                variant=variant,

                transaction_type="order",

                quantity=-item.quantity,

                note=f"Order ID: {order.order_id}"
            )

        # =========================================
        # UPDATE PRODUCT STATUS
        # =========================================

        for variant in cart.items.all():

            product = variant.variant.product

            if product.total_stock <= 0:

                product.status = "out_of_stock"

            else:

                product.status = "published"

            product.save()

        # =========================================
        # CLEAR CART
        # =========================================

        cart.items.all().delete()

        # =========================================
        # SEND EMAIL
        # =========================================

        send_order_email(

            order,

            "🎉 Order Confirmed",

            "orders/order_confirmation.html"
        )

        # =========================================
        # SUCCESS RESPONSE
        # =========================================

        return JsonResponse({

            "success": True,

            "order_id": order.order_id
        })

    # PREPAID → ONLY return cart summary
    return JsonResponse({
        "success": True,
        "amount": float(cart.total_amount)
    })

from .models import Pincode
import requests

def get_pincode_data(request, pin):

    if len(pin) != 6 or not pin.isdigit():
        return JsonResponse({
            "success": False,
            "message": "Invalid pincode"
        })

    try:
        cached = Pincode.objects.filter(pin_code=pin).first()

        if cached:
            return JsonResponse({
                "success": True,
                "city": cached.city,
                "state": cached.state,
                "source": "cache"
            })

        url = f"https://api.postalpincode.in/pincode/{pin}"
        res = requests.get(url, timeout=5, verify=False)
        if res.status_code != 200:
            return JsonResponse({
                "success": False,
                "message": "External API failed"
            })

        data = res.json()

        if not data or data[0]["Status"] != "Success":
            return JsonResponse({
                "success": False,
                "message": "Pincode not found"
            })

        post_office = data[0]["PostOffice"][0]

        city = post_office["District"]
        state = post_office["State"]

        Pincode.objects.create(
            pin_code=pin,
            city=city,
            state=state
        )

        return JsonResponse({
            "success": True,
            "city": city,
            "state": state,
            "source": "api"
        })

    except Exception as e:
        print("ERROR:", str(e))  # 🔥 DEBUG
        return JsonResponse({
            "success": False,
            "message": str(e)
        })

@login_required
def order_success(request):

    order_id = request.GET.get("order_id")

    order = Order.objects.filter(
        order_id=order_id,
        user=request.user
    ).first()

    return render(request, "orders/success.html", {
        "order": order
    })


# orders/views.py

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404

from .models import Order


# =========================================================
# ORDER HISTORY
# =========================================================

@login_required
def order_history(request):

    orders = Order.objects.filter(
        user=request.user
    ).prefetch_related(
        "items"
    ).order_by("-created_at")

    return render(request, "orders/history.html", {
        "orders": orders
    })


# =========================================================
# ORDER DETAIL
# =========================================================

@login_required
def order_detail(request, order_id):

    order = get_object_or_404(

        Order.objects.prefetch_related(
            "items"
        ),

        order_id=order_id,
        user=request.user
    )

    return render(request, "orders/detail.html", {
        "order": order,
        "items": order.items.all()
    })

def track_order(request, order_id):

    order = get_object_or_404(
        Order,
        order_id=order_id,
        user=request.user
    )

    tracking_url = None

    if order.courier_partner == "Delhivery":

        tracking_url = (
            f"https://www.delhivery.com/track/package/{order.tracking_number}"
        )

    elif order.courier_partner == "Shiprocket":

        tracking_url = (
            f"https://shiprocket.co/tracking/{order.tracking_number}"
        )

    return render(request, "orders/track_order.html", {
        "order": order,
        "tracking_url": tracking_url
    })



from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

@require_POST
@login_required
def cancel_order(request, order_id):

    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "message": "Invalid request"
        })

    order = get_object_or_404(
        Order,
        order_id=order_id,
        user=request.user
    )

    try:
        with transaction.atomic():
            order.cancel_order()

            # =========================
            # SEND EMAIL (IMPORTANT)
            # =========================

            send_order_email(
                order=order,
                subject="❌ Your Order Has Been Cancelled",
                template_name="orders/order_cancelled.html",
                context_extra={
                    "message": "Your order was successfully cancelled."
                }
            )


        return JsonResponse({
            "success": True,
            "message": "Order cancelled successfully"
        })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": str(e)
        })


# orders/views.py

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Order

@login_required
def request_return(request, order_id):

    order = Order.objects.get(order_id=order_id, user=request.user)

    # ONLY AFTER DELIVERY
    if order.status != "DELIVERED":
        return JsonResponse({
            "success": False,
            "message": "Return allowed only after delivery"
        })

    reason = request.POST.get("reason")
    comment = request.POST.get("comment")

    order.status = "RETURN_REQUESTED"
    order.save()

    order.returns.create(
        reason=reason,
        comment=comment
    )

    return JsonResponse({
        "success": True,
        "message": "Return request submitted"
    })



@login_required
def tracking_status_api(request, order_id):

    order = get_object_or_404(
        Order,
        order_id=order_id,
        user=request.user
    )

    return JsonResponse({

        "shipping_status":
            order.shipping_status,

        "tracking_number":
            order.tracking_number,

        "courier_partner":
            order.courier_partner,

        "estimated_delivery":
            str(order.estimated_delivery)
    })


from django.template.loader import render_to_string
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from weasyprint import HTML
from .models import Order

def download_invoice(request, order_id):

    order = get_object_or_404(
        Order.objects.prefetch_related("items"),
        order_id=order_id,
        user=request.user
    )

    html_string = render_to_string(
        "orders/invoice_pdf.html",
        {"order": order}
    )

    html = HTML(string=html_string)

    pdf = html.write_pdf()

    response = HttpResponse(pdf, content_type="application/pdf")
    response['Content-Disposition'] = f'attachment; filename="invoice_{order.order_id}.pdf"'

    return response