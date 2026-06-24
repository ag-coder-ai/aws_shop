
import razorpay
import json
import hmac
import hashlib
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.db import transaction


from orders.models import Order
from payments.models import Payment
from carts.models import Cart
from django.contrib.auth.decorators import login_required
from orders.models import Order, OrderItem, OrderStatus, ShippingAddress
from products.models import ProductVariant
from orders.utils.order_id import generate_order_id
from orders.services import send_order_email
from django.db import models


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
        return JsonResponse({"success": False, "message": "Invalid method"})

    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        return JsonResponse({"success": False, "message": "Cart not found"})

    client = get_razorpay_client()

    razorpay_order = client.order.create({
        "amount": int(cart.total_amount * 100),
        "currency": "INR",
        "payment_capture": 1
    })

    Payment.objects.create(
        user=request.user,   # ✅ FIX: add user (IMPORTANT)
        order=None,
        razorpay_order_id=razorpay_order["id"],
        amount=cart.total_amount,
        status="CREATED"
    )

    return JsonResponse({
        "success": True,
        "key": settings.RAZORPAY_KEY_ID,
        "order_id": razorpay_order["id"],
        "amount": int(cart.total_amount * 100),
        "currency": "INR"
    })



@csrf_exempt
def razorpay_webhook(request):

    try:
        payload = request.body
        received_signature = request.headers.get("X-Razorpay-Signature")

        if not received_signature:
            return JsonResponse(
                {"status": "error", "message": "Missing signature"},
                status=400
            )

        secret = settings.RAZORPAY_WEBHOOK_SECRET

        generated_signature = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(generated_signature, received_signature):
            return JsonResponse({"status": "invalid signature"}, status=400)

        event = json.loads(payload)

        if event.get("event") == "payment.captured":

            payment_entity = event["payload"]["payment"]["entity"]
            razorpay_order_id = payment_entity["order_id"]
            razorpay_payment_id = payment_entity["id"]

            with transaction.atomic():

                if Order.objects.filter(payment_reference=razorpay_order_id).exists():
                    return JsonResponse({"status": "already processed"})

                payment = Payment.objects.select_for_update().get(
                    razorpay_order_id=razorpay_order_id
                )

                payment.status = "PAID"
                payment.razorpay_payment_id = razorpay_payment_id
                payment.save()

                cart = Cart.objects.get(user=payment.user)

                order = Order.objects.create(
                    user=payment.user,
                    order_id=generate_order_id(),
                    subtotal=cart.subtotal,
                    total=cart.total_amount,
                    payment_method="PREPAID",
                    payment_status="PAID",
                    status=OrderStatus.CONFIRMED,
                    payment_reference=razorpay_order_id
                )

                items = []

                for item in cart.items.select_for_update():

                    variant = ProductVariant.objects.select_for_update().get(
                        id=item.variant.id
                    )

                    if variant.stock_quantity < item.quantity:
                        raise Exception("Stock mismatch")

                    variant.stock_quantity -= item.quantity
                    variant.save(update_fields=["stock_quantity"])

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

        return JsonResponse({"status": "ok"})

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


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

        # ✅ FIX 1: support both JSON + POST
        data = {}
        if request.content_type == "application/json":
            data = json.loads(request.body.decode("utf-8"))
        else:
            data = request.POST

        order_id = data.get("razorpay_order_id")
        payment_id = data.get("razorpay_payment_id")
        signature = data.get("razorpay_signature")

        print("DEBUG DATA:", data)  # 🔥 IMPORTANT

        if not all([order_id, payment_id, signature]):
            return JsonResponse({
                "success": False,
                "message": "Missing payment data"
            }, status=400)

        params = {
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature
        }

        # ✅ VERIFY SIGNATURE
        client.utility.verify_payment_signature(params)

        # ⚠️ safer lookup
        payment = Payment.objects.filter(razorpay_order_id=order_id).first()

        if not payment:
            return JsonResponse({"success": False, "message": "Payment not found"}, status=400)

        payment.status = "PAID"
        payment.razorpay_payment_id = payment_id
        payment.save()

        # CART
        cart = Cart.objects.filter(user=payment.user).first()

        if not cart:
            return JsonResponse({"success": False, "message": "Cart not found"}, status=400)

        order = Order.objects.create(
            user=payment.user,
            order_id=generate_order_id(),
            subtotal=cart.subtotal,
            total=cart.total_amount,
            payment_method="PREPAID",
            payment_status="PAID",
            status=OrderStatus.CONFIRMED,
            payment_reference=order_id
        )

        items = []

        for item in cart.items.all():
            variant = ProductVariant.objects.get(id=item.variant.id)

            variant.stock_quantity -= item.quantity
            variant.save()

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

    except razorpay.errors.SignatureVerificationError:
        return JsonResponse({
            "success": False,
            "message": "Invalid signature"
        }, status=400)

    except Exception as e:
        print("ERROR:", str(e))  # 🔥 LOG REAL ERROR
        return JsonResponse({
            "success": False,
            "message": str(e)
        }, status=400)