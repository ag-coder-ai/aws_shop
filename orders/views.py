
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
from django.conf import settings

@login_required
@transaction.atomic
def create_checkout(request):
    import re

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

    phone = re.sub(r"\D", "", phone)

    if phone.startswith("91") and len(phone) == 12:
        phone = phone[2:]

    if len(phone) != 10:
        field_errors["phone"] = ["Enter valid 10 digit mobile number"]

    elif phone[0] not in "6789":
        field_errors["phone"] = ["Enter valid Indian mobile number"]

    elif phone in [
        "9999999999",
        "8888888888",
        "7777777777",
        "6666666666",
        "9876543210",
    ]:
        field_errors["phone"] = ["Enter valid mobile number"]

    try:
        validate_email(email)
    except ValidationError:
        field_errors["email"] = ["Enter valid email"]

    import re

    address = re.sub(r"\s+", " ", address)

    # Required
    if not address:
        field_errors["address"] = ["Address is required"]

    # Length limits
    elif len(address) < 10:
        field_errors["address"] = ["Enter complete address"]

    elif len(address) > 255:
        field_errors["address"] = ["Address too long"]

    # Must contain letters
    elif not re.search(r"[A-Za-z]", address):
        field_errors["address"] = ["Enter valid address"]

    # Prevent junk patterns
    elif re.match(r"^(.)\1+$", address.replace(" ", "")):
        field_errors["address"] = ["Enter meaningful address"]

    if not city:
        field_errors["city"] = ["City required"]

    if not state:
        field_errors["state"] = ["State required"]

    pincode = (pincode or "").strip()

    FAKE_PINS = {
        "000000", "111111", "222222", "333333",
        "444444", "555555", "666666", "777777",
        "888888", "999999", "123456", "654321"
    }

    if pincode in FAKE_PINS:
        field_errors["pincode"] = ["Enter valid pincode"]

    PIN_REGEX = r"^[1-9][0-9]{5}$"

    if not re.fullmatch(PIN_REGEX, pincode):
        field_errors["pincode"] = ["Enter valid 6-digit Indian pincode"]

    # 🚫 Known non-serviceable / difficult regions (India islands etc.)
    BLOCKED_PINCODES = {
        # Andaman & Nicobar Islands
        "744101", "744102", "744103", "744104", "744105",

        # Lakshadweep
        "682551", "682552", "682553", "682554",

        # Some very remote/high-risk test exclusions (optional)
        "000000", "111111", "999999", "123456"
    }

    if pincode in BLOCKED_PINCODES :
        field_errors["pincode"] = ["Enter valid pincode"]

    if field_errors:
        return JsonResponse({"success": False, "field_errors": field_errors},status=400)


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
    email_user = settings.EMAIL_HOST_USER
    print("EMAIL USER:", email_user)

    send_order_email(
        order,
        "🎉 Order Confirmed",
        "orders/order_confirmation.html"
    )

    return JsonResponse({
        "success": True,
        "order_id": order.order_id,
        "amount": float(order.total)  # ADD THIS
    })


@login_required
def order_success(request):

    order_id = request.GET.get("order_id")

    if not order_id:
        return redirect("home")  # or cart page

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

from django.core import signing
from django.http import Http404
from django.shortcuts import get_object_or_404

def track_order(request, token):

    try:
        order_id = signing.loads(
            token,
            salt="track-order",
            max_age=60 * 60 * 24 * 7  # optional: 7 days expiry
        )

    except (signing.BadSignature, signing.SignatureExpired):
        raise Http404("Invalid or expired tracking link")

    order = get_object_or_404(Order, order_id=order_id)

    tracking_url = None

    if order.courier_partner == "Delhivery":
        tracking_url = f"https://www.delhivery.com/track/package/{order.tracking_number}"

    elif order.courier_partner == "Shiprocket":
        tracking_url = f"https://shiprocket.co/tracking/{order.tracking_number}"

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