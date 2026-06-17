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
        order = order.__class__.objects.select_related("user").prefetch_related("items").get(id=order.id)
        # ✅ Clean production context (NO nested ORM in templates)
        context = {
            "username": order.user.username or order.user.email.split("@")[0],
            "order_id": order.order_id,
            "payment_method": order.payment_method,
            "status": order.status,
            "total": order.total,
            "items":items,
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