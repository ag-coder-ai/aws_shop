# orders/services.py

import uuid
from products.models import ProductVariant
from decimal import Decimal

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.template.loader import render_to_string

from .models import (
    Order,
    OrderItem,
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
    ShippingStatus,
)


# =========================================================
# SHIPPING CALCULATOR
# =========================================================

def calculate_shipping_charge(subtotal):

    # FREE SHIPPING
    if subtotal >= Decimal("999.00"):
        return Decimal("0.00")

    return Decimal("80.00")


# =========================================================
# CREATE ORDER FROM CART
# =========================================================

@transaction.atomic
def create_order_from_cart(
    user,
    cart,
    payment_method=PaymentMethod.PREPAID
):

    if not cart.items.exists():
        raise Exception("Cart is empty")

    # =====================================================
    # CALCULATE TOTALS
    # =====================================================

    subtotal = Decimal("0.00")

    cart_items = cart.items.select_related(
        "variant",
        "variant__product",
        "variant__size",
        "variant__color"
    )

    for item in cart_items:
        subtotal += item.total_price

    shipping_charge = calculate_shipping_charge(
        subtotal
    )

    discount = Decimal("0.00")

    total = (
        subtotal
        +
        shipping_charge
        -
        discount
    )

    # =====================================================
    # PAYMENT STATUS
    # =====================================================

    payment_status = PaymentStatus.PENDING

    if payment_method == PaymentMethod.PREPAID:
        payment_status = PaymentStatus.PAID

    # =====================================================
    # ORDER STATUS
    # =====================================================

    order_status = OrderStatus.CONFIRMED

    # =====================================================
    # CREATE ORDER
    # =====================================================

    order = Order.objects.create(

        user=user,

        order_id=(
            f"ORD{uuid.uuid4().hex[:10].upper()}"
        ),

        payment_method=payment_method,

        payment_status=payment_status,

        status=order_status,

        subtotal=subtotal,

        shipping_charge=shipping_charge,

        discount=discount,

        total=total,

        shipping_status=ShippingStatus.PENDING
    )

    # =====================================================
    # CREATE ORDER ITEMS
    # =====================================================

    order_items = []

    for item in cart_items:

        variant = item.variant

        # =================================================
        # STOCK CHECK
        # =================================================

        if variant.stock_quantity < item.quantity:

            raise Exception(
                f"{variant.product.name} is out of stock"
            )

        # =================================================
        # REDUCE STOCK
        # =================================================

        variant.stock_quantity -= item.quantity

        variant.save()

        # =================================================
        # PRODUCT IMAGE SNAPSHOT
        # =================================================

        product_image = None

        if hasattr(variant.product, "images"):

            first_image = (
                variant.product.images.first()
            )

            if first_image:
                product_image = first_image.image

        # =================================================
        # CREATE ORDER ITEM
        # =================================================

        order_items.append(

            OrderItem(

                order=order,

                product_name=variant.product.name,

                product_image=product_image,

                variant_id=variant.id,

                sku=getattr(
                    variant,
                    "sku",
                    ""
                ),

                size=variant.size.name,

                color=variant.color.name,

                price=variant.wholesale_price,

                quantity=item.quantity
            )
        )

    OrderItem.objects.bulk_create(order_items)

    # =====================================================
    # CLEAR CART
    # =====================================================

    cart.items.all().delete()

    # =====================================================
    # SEND EMAIL
    # =====================================================

    send_order_email(
        order=order,
        subject="Order Confirmed Successfully",
        template_name="orders/emails/order_confirmed.html"
    )

    return order


# =========================================================
# COMMON ORDER EMAIL SENDER
# =========================================================

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings




import resend

from django.template.loader import render_to_string

def send_order_email(order, subject, template_name, context_extra=None):

    if context_extra is None:
        context_extra = {}

    context = {
        "order": order,
        "user": order.user,
        **context_extra
    }

    html_content = render_to_string(template_name, context)

    try:
        response = resend.Emails.send({
            "from": "Your Store <onboarding@resend.dev>",
            "to": order.user.email,
            "subject": subject,
            "html": html_content,
        })

        print("RESEND RESPONSE:", response)

        print("EMAIL SENT SUCCESSFULLY")


    except Exception as e:
        print("EMAIL ERROR:", e)