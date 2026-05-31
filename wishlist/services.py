
from .models import Wishlist


def toggle_wishlist(user, variant):

    obj = Wishlist.objects.filter(
        user=user,
        variant=variant
    ).first()

    if obj:

        obj.delete()

        return {
            "action": "removed"
        }

    Wishlist.objects.create(
        user=user,
        variant=variant
    )

    return {
        "action": "added"
    }
