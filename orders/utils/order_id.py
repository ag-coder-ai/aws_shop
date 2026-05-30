from django.utils import timezone

from orders.models import Order


def generate_order_id():

    today = timezone.now().strftime("%Y%m%d")

    prefix = f"ORD-{today}"

    # LAST ORDER TODAY
    last_order = Order.objects.filter(
        order_id__startswith=prefix
    ).order_by("-id").first()

    if last_order:

        try:

            last_number = int(
                last_order.order_id.split("-")[-1]
            )

        except:

            last_number = 0

    else:

        last_number = 0

    new_number = last_number + 1

    return f"{prefix}-{new_number:04d}"