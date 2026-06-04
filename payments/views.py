from django.shortcuts import render

import razorpay
from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from orders.models import Order
from payments.models import Payment
from django.views.decorators.csrf import csrf_exempt
from orders.services import send_order_email
from orders.models import OrderItem
from carts.models import Cart

import razorpay
from django.conf import settings

import razorpay
from django.conf import settings

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

    checkout_data = request.session.get("checkout_data")

    if not checkout_data:
        return JsonResponse({
            "success": False,
            "message": "Checkout session expired"
        })

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


    payment = Payment.objects.create(
        order=None,  # IMPORTANT: no order yet
        razorpay_order_id=razorpay_order["id"],
        amount=cart.total_amount,
        status="CREATED"
    )

    request.session["razorpay_order_id"] = razorpay_order["id"]

    return JsonResponse({
        "success": True,
        "key": settings.RAZORPAY_KEY_ID,
        "order_id": razorpay_order["id"],
        "amount": int(cart.total_amount * 100),
        "currency": "INR"
    })


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction

from carts.models import Cart
from orders.models import OrderStatus
from orders.utils.order_id import generate_order_id
import logging
from orders.models import ShippingAddress

logger = logging.getLogger(__name__)


@csrf_exempt
@transaction.atomic
def verify_payment(request):

    data = request.POST

    try:
        client = get_razorpay_client()

        client.utility.verify_payment_signature({
            "razorpay_order_id": data["razorpay_order_id"],
            "razorpay_payment_id": data["razorpay_payment_id"],
            "razorpay_signature": data["razorpay_signature"]
        })

        payment = Payment.objects.get(
            razorpay_order_id=data["razorpay_order_id"]
        )

        payment.status = "PAID"
        payment.razorpay_payment_id = data["razorpay_payment_id"]
        payment.save()

        cart = Cart.objects.get(user=request.user)
        checkout_data = request.session.get("checkout_data")

        if not checkout_data:
            return JsonResponse({"success": False, "message": "Session expired"})

        # 🔥 CREATE ORDER ONLY NOW
        order = Order.objects.create(
            user=request.user,
            order_id=generate_order_id(),
            subtotal=cart.subtotal,
            total=cart.total_amount,
            payment_method="PREPAID",
            payment_status="PAID",
            status=OrderStatus.CONFIRMED
        )

        ShippingAddress.objects.create(
            order=order,
            full_name=checkout_data["full_name"],
            phone=checkout_data["phone"],
            email=checkout_data["email"],
            address_line_1=checkout_data["address"],
            city=checkout_data["city"],
            state=checkout_data["state"],
            postal_code=checkout_data["pincode"],
            country="India"
        )

        # move cart items → order items
        items = []

        for item in cart.items.select_related("variant"):

            variant = item.variant

            variant.stock_quantity -= item.quantity
            variant.save()

            items.append(OrderItem(
                order=order,
                variant_id=variant.id,
                product_name=variant.product.name,
                product_image=None,
                size=variant.size.name,
                color=variant.color.name,
                price=variant.wholesale_price,
                quantity=item.quantity
            ))

        OrderItem.objects.bulk_create(items)

        cart.items.all().delete()


        request.session.pop("checkout_data", None)

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