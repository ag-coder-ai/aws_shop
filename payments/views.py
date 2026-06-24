
import razorpay
import json
import hmac
import hashlib
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.db import transaction
from discounts.services import CouponService
from orders.models import Order
from payments.models import Payment
from carts.models import Cart
from django.contrib.auth.decorators import login_required
from orders.models import Order, OrderItem, OrderStatus, ShippingAddress
from products.models import ProductVariant
from orders.utils.order_id import generate_order_id
from orders.services import send_order_email
from django.db import models
from decimal import Decimal
from django.utils import timezone

def get_razorpay_client():
    return razorpay.Client(
        auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET
        )
    )


@login_required
def create_payment(request):

    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=400)

    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        return JsonResponse({"success": False, "message": "Cart not found"}, status=400)

    if not cart.items.exists():
        return JsonResponse({"success": False, "message": "Cart is empty"}, status=400)

    coupon_code = (request.POST.get("coupon_code") or request.POST.get("code") or "").strip()

    cart_total = cart.total_amount
    discount = Decimal("0.00")
    final_total = cart_total
    coupon_applied = None

    if coupon_code:
        try:
            coupon, discount, final_total = CouponService.apply_coupon(
                cart_total,
                coupon_code,
                user=request.user
            )
            if coupon:
                coupon_applied = coupon.code
        except Exception:
            discount = Decimal("0.00")
            final_total = cart_total
            coupon_applied = None

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
        "coupon_applied": coupon_applied,
    })


@csrf_exempt
def razorpay_webhook(request):

    try:
        payload = request.body
        signature = request.headers.get("X-Razorpay-Signature")

        if not signature:
            return JsonResponse({"status": "missing signature"}, status=400)

        secret = settings.RAZORPAY_WEBHOOK_SECRET

        generated = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(generated, signature):
            return JsonResponse({"status": "invalid signature"}, status=400)

        event = json.loads(payload)

        if event.get("event") != "payment.captured":
            return JsonResponse({"status": "ignored"})

        payment_entity = event["payload"]["payment"]["entity"]
        razorpay_order_id = payment_entity["order_id"]
        razorpay_payment_id = payment_entity["id"]

        with transaction.atomic():

            payment = Payment.objects.select_for_update().get(
                razorpay_order_id=razorpay_order_id
            )

            if payment.status == "PAID":
                return JsonResponse({"status": "already processed"})

            payment.status = "PAID"
            payment.razorpay_payment_id = razorpay_payment_id
            payment.save()

            cart = Cart.objects.select_for_update().get(user=payment.user)

            coupon_code = payment.coupon_code

            cart_total = cart.total_amount
            discount = Decimal("0.00")
            final_total = cart_total
            used_coupon = None

            # =========================
            # APPLY COUPON AGAIN SAFELY
            # =========================
            if coupon_code:
                try:
                    used_coupon, discount, final_total = CouponService.apply_coupon(
                        cart_total,
                        coupon_code,
                        user=payment.user
                    )
                except Exception:
                    pass

            # =========================
            # STOCK VALIDATION FIRST
            # =========================
            for item in cart.items.select_for_update():

                variant = ProductVariant.objects.select_for_update().get(
                    id=item.variant.id
                )

                if variant.stock_quantity < item.quantity:
                    raise Exception(f"{variant.product.name} out of stock")

                variant.stock_quantity -= item.quantity
                variant.save(update_fields=["stock_quantity"])

            # =========================
            # CREATE ORDER
            # =========================
            order = Order.objects.create(
                user=payment.user,
                order_id=generate_order_id(),
                subtotal=cart.subtotal,
                total=final_total,
                discount=discount,
                payment_method="PREPAID",
                payment_status="PAID",
                status=OrderStatus.CONFIRMED,
                payment_reference=razorpay_order_id
            )

            # coupon usage
            if used_coupon:
                used_coupon.used_count += 1
                used_coupon.save(update_fields=["used_count"])

            # order items
            items = []
            for item in cart.items.all():

                variant = item.variant

                items.append(OrderItem(
                    order=order,
                    variant_id=variant.id,
                    product_name=variant.product.name,
                    product_image=variant.product.primary_image.image if variant.product.primary_image else None,
                    size=variant.size.name,
                    color=variant.color.name,
                    price=variant.wholesale_price,
                    quantity=item.quantity
                ))

            OrderItem.objects.bulk_create(items)

            cart.items.all().delete()

            send_order_email(
                order,
                "🎉 Order Confirmed",
                "orders/order_confirmation.html"
            )

        return JsonResponse({
            "success": True,
            "order_id": order.order_id
        })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": str(e)
        }, status=500)







import json
import razorpay
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def verify_payment(request):

    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=405)

    try:
        client = get_razorpay_client()

        data = json.loads(request.body.decode("utf-8")) if request.content_type == "application/json" else request.POST

        order_id = data.get("razorpay_order_id")
        payment_id = data.get("razorpay_payment_id")
        signature = data.get("razorpay_signature")

        if not all([order_id, payment_id, signature]):
            return JsonResponse({"success": False, "message": "Missing payment data"}, status=400)

        client.utility.verify_payment_signature({
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature
        })

        payment = Payment.objects.filter(razorpay_order_id=order_id).first()

        if not payment:
            return JsonResponse({"success": False, "message": "Payment not found"}, status=400)

        payment.status = "PAID"
        payment.razorpay_payment_id = payment_id
        payment.save()

        return JsonResponse({
            "success": True,
            "message": "Payment verified successfully. Order will be created shortly."
        })

    except razorpay.errors.SignatureVerificationError:
        return JsonResponse({
            "success": False,
            "message": "Payment verification failed (invalid signature)"
        }, status=400)

    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": str(e)
        }, status=400)