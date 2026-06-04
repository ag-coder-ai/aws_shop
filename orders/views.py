
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
import logging
logger = logging.getLogger(__name__)
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

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Order, OrderItem, ShippingAddress
from products.models import ProductVariant, InventoryLog
from orders.models import OrderItem
from orders.services import send_order_email
import re
from django.core.validators import validate_email

import re
import threading
from django.http import JsonResponse
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

@login_required
@transaction.atomic
def create_checkout(request):

    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid request"}, status=400)

    data = request.POST

    # =========================================
    # CART
    # =========================================
    try:
        cart = Cart.objects.prefetch_related(
            "items__variant__product",
            "items__variant__size",
            "items__variant__color"
        ).get(user=request.user)
    except Cart.DoesNotExist:
        return JsonResponse({"success": False, "message": "Cart not found"}, status=400)

    if not cart.items.exists():
        return JsonResponse({"success": False, "message": "Cart is empty"}, status=400)

    payment_method = data.get("payment_method")

    # =========================================
    # VALIDATION
    # =========================================
    field_errors = {}

    full_name = data.get("full_name", "").strip()
    phone = data.get("phone", "").strip()
    email = data.get("email", "").strip().lower()
    address = data.get("address", "").strip()
    city = data.get("city", "").strip()
    state = data.get("state", "").strip()
    pincode = data.get("pincode", "").strip()

    if not full_name or len(full_name) < 3:
        field_errors["full_name"] = ["Enter valid full name"]

    if not re.match(r"^[6-9]\d{9}$", phone):
        field_errors["phone"] = ["Enter valid 10 digit mobile"]

    try:
        validate_email(email)
    except ValidationError:
        field_errors["email"] = ["Enter valid email"]

    if not address or len(address) < 10:
        field_errors["address"] = ["Enter valid address"]

    if not city:
        field_errors["city"] = ["City required"]

    if not state:
        field_errors["state"] = ["State required"]

    if not re.match(r"^[1-9][0-9]{5}$", pincode):
        field_errors["pincode"] = ["Enter valid pincode"]

    if field_errors:
        return JsonResponse({"success": False, "field_errors": field_errors}, status=400)

    # =========================================
    # COD LIMIT
    # =========================================
    if payment_method == "COD" and cart.total_amount > 2000:
        return JsonResponse({
            "success": False,
            "message": "COD allowed only below ₹2000"
        }, status=400)

    # =========================================
    # PREPAID FLOW (ONLY RETURN AMOUNT)
    # =========================================
    if payment_method == "PREPAID":

        request.session["checkout_data"] = {
            "full_name": full_name,
            "phone": phone,
            "email": email,
            "address": address,
            "city": city,
            "state": state,
            "pincode": pincode,
        }

        return JsonResponse({
            "success": True,
            "amount": float(cart.total_amount)
        })

    # =========================================
    # COD ORDER CREATE
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

    ShippingAddress.objects.create(
        order=order,
        full_name=full_name,
        phone=phone,
        email=email,
        address_line_1=address,
        city=city,
        state=state,
        postal_code=pincode,
        country="India"
    )

    for item in cart.items.select_related("variant__product"):

        variant = ProductVariant.objects.select_for_update().get(id=item.variant.id)

        if variant.stock_quantity < item.quantity:
            transaction.set_rollback(True)
            return JsonResponse({
                "success": False,
                "message": f"{variant.product.name} out of stock"
            }, status=400)

        variant.stock_quantity -= item.quantity
        variant.save()

        OrderItem.objects.create(
            order=order,
            product_name=variant.product.name,
            product_image=variant.product.primary_image.image if variant.product.primary_image else None,
            variant_id=variant.id,
            sku=variant.sku,
            size=variant.size.name,
            color=variant.color.name,
            price=variant.wholesale_price,
            quantity=item.quantity
        )

    cart.items.all().delete()

    # =========================================
    # EMAIL (ASYNC)
    # =========================================
    def async_email():
        try:
            send_order_email(
                order,
                "🎉 Order Confirmed",
                "orders/order_confirmation.html"
            )
        except Exception as e:
            logger.error(f"Email failed: {e}")

    threading.Thread(target=async_email).start()

    return JsonResponse({
        "success": True,
        "order_id": order.order_id,
        "amount": float(order.total)  # ADD THIS
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