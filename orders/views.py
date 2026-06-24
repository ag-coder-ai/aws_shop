
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
from .utils.redis_lock import RedisLock
from .services import send_order_email
from discounts.services import CouponService
from decimal import Decimal

from django.db import models
from django.utils import timezone
from discounts.models import Coupon

@login_required
def checkout_view(request):

    cart = Cart.objects.prefetch_related("items__variant").get(user=request.user)

    if cart.items.count() == 0:
        return redirect("carts")

    now = timezone.now()

    # ==============================
    # ACTIVE COUPONS (SAFE VERSION)
    # ==============================
    coupons = Coupon.objects.filter(
        active=True
    ).filter(
        models.Q(valid_from__isnull=True) | models.Q(valid_from__lte=now),
        models.Q(valid_to__isnull=True) | models.Q(valid_to__gte=now),
        used_count__lt=models.F("usage_limit")
    )

    return render(request, "orders/checkout.html", {
        "cart": cart,
        "items": cart.items.all(),
        "coupons": coupons
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
from payments.models import Payment

@login_required
@transaction.atomic
def create_checkout(request):
    import re
    from decimal import Decimal
    from django.core.exceptions import ValidationError
    from django.conf import settings
    from .utils.redis_lock import RedisLock

    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid request"}, status=400)

    data = request.POST

    lock_key = f"checkout_lock_user_{request.user.id}"
    lock = RedisLock(lock_key, timeout=20)

    if not lock.acquire():
        return JsonResponse({
            "success": False,
            "message": "Checkout already in progress. Please wait..."
        }, status=429)

    try:

        # =========================
        # CART
        # =========================
        cart = Cart.objects.prefetch_related(
            "items__variant__product",
            "items__variant__size",
            "items__variant__color"
        ).get(user=request.user)

        if not cart.items.exists():
            return JsonResponse({"success": False, "message": "Cart is empty"}, status=400)

        payment_method = data.get("payment_method")

        coupon_code = (data.get("coupon_code") or data.get("code") or "").strip()

        # =========================
        # VALIDATION
        # =========================
        field_errors = {}

        full_name = data.get("full_name", "").strip()
        phone = re.sub(r"\D", "", data.get("phone", ""))
        email = data.get("email", "").strip().lower()
        address = re.sub(r"\s+", " ", data.get("address", "").strip())
        city = data.get("city", "").strip()
        state = data.get("state", "").strip()
        pincode = data.get("pincode", "").strip()

        if not full_name or len(full_name) < 3:
            field_errors["full_name"] = ["Enter valid full name"]

        if len(phone) != 10 or phone[0] not in "6789":
            field_errors["phone"] = ["Enter valid mobile number"]

        try:
            validate_email(email)
        except ValidationError:
            field_errors["email"] = ["Enter valid email"]

        if not address:
            field_errors["address"] = ["Address is required"]

        if field_errors:
            return JsonResponse({"success": False, "field_errors": field_errors}, status=400)

        # =========================
        # PAYMENT METHOD FLOW
        # =========================
        if payment_method not in ["COD", "PREPAID"]:
            return JsonResponse({
                "success": False,
                "message": "Invalid payment method"
            }, status=400)

        # =========================
        # COUPON (SAFE)
        # =========================
        cart_total = cart.total_amount
        discount = Decimal("0.00")
        final_total = cart_total
        used_coupon = None
        coupon_msg = "No coupon applied"

        if coupon_code:
            try:
                from discounts.services import CouponService

                used_coupon, discount, final_total, coupon_msg = CouponService.apply_coupon(
                    cart_total,
                    coupon_code,
                    user=request.user
                )

            except Exception as e:
                used_coupon = None
                discount = Decimal("0.00")
                final_total = cart_total
                coupon_msg = str(e)

        # =========================
        # STOCK CHECK (ONLY RESERVE LOGIC CAN BE ADDED LATER)
        # =========================
        for item in cart.items.select_for_update():

            variant = ProductVariant.objects.select_for_update().get(
                id=item.variant.id
            )

            if variant.stock_quantity < item.quantity:
                return JsonResponse({
                    "success": False,
                    "message": f"{variant.product.name} out of stock"
                }, status=400)

        # =========================
        # PREPAID FLOW (ONLY PAYMENT INIT)
        # =========================
        if payment_method == "PREPAID":

            from payments.views import get_razorpay_client
            client = get_razorpay_client()

            razorpay_order = client.order.create({
                "amount": int(final_total * 100),
                "currency": "INR",
                "payment_capture": 1
            })

            Payment.objects.create(
                user=request.user,
                order=None,
                razorpay_order_id=razorpay_order["id"],
                amount=final_total,
                status="CREATED"
            )

            return JsonResponse({
                "success": True,
                "payment_required": True,

                "key": settings.RAZORPAY_KEY_ID,
                "order_id": razorpay_order["id"],
                "amount": int(final_total * 100),
                "currency": "INR",

                "cart_total": float(cart_total),
                "discount": float(discount),
                "final_total": float(final_total),
                "coupon_applied": used_coupon.code if used_coupon else None,
                "message": coupon_msg
            })

        # =========================
        # COD FLOW (ORDER CREATED HERE)
        # =========================
        order = Order.objects.create(
            user=request.user,
            order_id=generate_order_id(),
            subtotal=cart.subtotal,
            total=final_total,
            discount=discount,
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

            OrderItem.objects.create(
                order=order,
                product_name=item.variant.product.name,
                product_image=item.variant.product.primary_image.image if item.variant.product.primary_image else None,
                variant_id=item.variant.id,
                sku=item.variant.sku,
                size=item.variant.size.name,
                color=item.variant.color.name,
                price=item.variant.wholesale_price,
                quantity=item.quantity
            )

        cart.items.all().delete()

        send_order_email(
            order,
            "🎉 Order Confirmed (COD)",
            "orders/order_confirmation.html"
        )

        if used_coupon:
            used_coupon.used_count += 1
            used_coupon.save(update_fields=["used_count"])

        return JsonResponse({
            "success": True,
            "order_id": order.order_id,
            "amount": float(order.total),
            "discount": float(discount),
            "coupon": used_coupon.code if used_coupon else None,
            "message": (
                "Order placed successfully with coupon"
                if used_coupon else
                "Order placed successfully"
            )
        })

    finally:
        lock.release()

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

def track_order(request, order_id):

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




import resend
import logging
from django.template.loader import render_to_string
BASE_URL = "https://www.unitythreads.lifestyle"
logger = logging.getLogger(__name__)

def send_order_email(order, subject, template_name, context_extra=None):

    if not order.user or not order.user.email:
        logger.error(f"Order {order.id} has invalid user/email")
        return False

    try:
        # 🔥 Ensure fresh DB relation (prevents lazy loading issues)
        order = order.__class__.objects.select_related("user").get(id=order.id)

        # ✅ Clean production context (NO nested ORM in templates)
        context = {
            "username": order.user.username or order.user.email.split("@")[0],
            "order_id": order.order_id,
            "payment_method": order.payment_method,
            "status": order.status,
            "total": order.total,
            "track_url": f"{BASE_URL}/orders/track/{order.order_id}/"
        }

        if context_extra:
            context.update(context_extra)

        # Render email template
        html_content = render_to_string(template_name, context)

        # Send email via Resend
        response = resend.Emails.send({
            "from": "Unity Threads <fashion@unitythreads.lifestyle>",
            "to": [order.user.email],
            "subject": subject,
            "html": html_content,
        })

        logger.info(f"Email sent successfully for order {order.id}: {response}")

        return True

    except Exception as e:
        logger.exception(f"Email failed for order {order.id}")
        return False