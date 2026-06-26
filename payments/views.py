
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
        return JsonResponse(
            {"success": False, "message": "Invalid method"}, status=400)

    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        return JsonResponse(
            {"success": False, "message": "Cart not found"}, status=400)

    if not cart.items.exists():
        return JsonResponse(
            {"success": False, "message": "Cart is empty"}, status=400)

    coupon_code = (request.POST.get("coupon_code") or "").strip()

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
            coupon_applied = coupon.code if coupon else None
        except Exception:
            pass

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
        status="CREATED",
        payment_reference=razorpay_order["id"],  # IMPORTANT
        razorpay_event_id=None
    )

    return JsonResponse({
        "success": True,
        "key": settings.RAZORPAY_KEY_ID,
        "order_id": razorpay_order["id"],
        "amount": int(final_total * 100),
        "currency": "INR",
        "cart_total": float(cart_total),
        "discount": float(discount),
        "final_total": float(final_total),
        "coupon_applied": coupon_applied,
    })


import json
import hmac
import hashlib
from decimal import Decimal
@csrf_exempt
def razorpay_webhook(request):

    print("WEBHOOK HIT")

    try:
        payload = request.body
        signature = request.META.get("HTTP_X_RAZORPAY_SIGNATURE")

        # -------------------------
        # 1. Signature check
        # -------------------------
        if not signature:
            return JsonResponse({"status": "missing signature"}, status=400)

        secret = settings.RAZORPAY_WEBHOOK_SECRET

        generated_signature = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(generated_signature, signature):
            return JsonResponse({"status": "invalid signature"}, status=400)

        # -------------------------
        # 2. Parse event
        # -------------------------
        event = json.loads(payload)
        event_type = event.get("event")

        payment_entity = event.get("payload", {}).get("payment", {}).get("entity", {})
        razorpay_order_id = payment_entity.get("order_id")
        razorpay_payment_id = payment_entity.get("id")

        # 🔥 ONE CLEAN LOG ONLY
        print(f"RAZORPAY WEBHOOK | event={event_type} | order={razorpay_order_id}")

        # -------------------------
        # 3. Only required events
        # -------------------------
        if event_type not in ["payment.captured", "payment.authorized"]:
            return JsonResponse({"status": "ignored"})

        if not razorpay_order_id:
            return JsonResponse({"status": "missing order_id"}, status=400)

        event_key = f"{razorpay_order_id}:{razorpay_payment_id}:{event_type}"

        # -------------------------
        # 4. Transaction block
        # -------------------------
        with transaction.atomic():

            payment = Payment.objects.select_for_update().get(
                razorpay_order_id=razorpay_order_id
            )

            # idempotency
            if payment.status == "SUCCESS":
                return JsonResponse({"status": "already processed"})

            if Payment.objects.filter(razorpay_event_id=event_key).exists():
                return JsonResponse({"status": "duplicate ignored"})

            # update payment
            payment.status = "SUCCESS"
            payment.razorpay_payment_id = razorpay_payment_id
            payment.razorpay_event_id = event_key
            payment.save(update_fields=[
                "status",
                "razorpay_payment_id",
                "razorpay_event_id"
            ])

            # lock cart
            cart = Cart.objects.select_for_update().prefetch_related(
                "items__variant__product",
                "items__variant__size",
                "items__variant__color"
            ).get(user=payment.user)

            # stock validation
            for item in cart.items.all():
                variant = ProductVariant.objects.select_for_update().get(
                    id=item.variant_id
                )

                if variant.stock_quantity < item.quantity:
                    raise Exception(f"{variant.product.name} out of stock")

            # create order
            order = Order.objects.create(
                user=payment.user,
                order_id=generate_order_id(),
                subtotal=cart.subtotal,
                total=payment.amount,
                discount=Decimal("0.00"),
                payment_method="PREPAID",
                payment_status="PAID",
                status=OrderStatus.CONFIRMED,
                payment_reference=razorpay_order_id
            )

            payment.order = order
            payment.save(update_fields=["order"])

            # deduct stock
            for item in cart.items.all():
                variant = ProductVariant.objects.select_for_update().get(
                    id=item.variant_id
                )
                variant.stock_quantity -= item.quantity
                variant.save(update_fields=["stock_quantity"])

            # create order items
            OrderItem.objects.bulk_create([
                OrderItem(
                    order=order,
                    variant_id=item.variant_id,
                    product_name=item.variant.product.name,
                    product_image=(
                        item.variant.product.primary_image.image
                        if item.variant.product.primary_image else None
                    ),
                    size=item.variant.size.name,
                    color=item.variant.color.name,
                    price=item.variant.wholesale_price,
                    quantity=item.quantity
                )
                for item in cart.items.all()
            ])

            # clear cart
            cart.items.all().delete()

        # -------------------------
        # 5. Email OUTSIDE transaction
        # -------------------------
        try:
            send_order_email(
                order,
                "🎉 Payment Successful - Order Confirmed",
                "orders/order_confirmation.html"
            )
        except Exception:
            pass

        return JsonResponse({
            "success": True,
            "order_id": order.order_id
        })

    except Payment.DoesNotExist:
        return JsonResponse({"status": "payment not found"}, status=404)

    except Cart.DoesNotExist:
        return JsonResponse({"status": "cart not found"}, status=404)

    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": str(e)
        }, status=500)
