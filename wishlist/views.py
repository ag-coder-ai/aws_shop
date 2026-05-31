from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from products.models import Product
from .models import Wishlist
from django.shortcuts import render

@login_required
def toggle_wishlist(request):

    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid request"}, status=400)

    product_id = request.POST.get("product_id")

    if not product_id:
        return JsonResponse({"success": False, "message": "Product ID required"}, status=400)

    try:
        product = Product.objects.get(id=product_id)

    except Product.DoesNotExist:
        return JsonResponse({"success": False, "message": "Product not found"}, status=404)

    wishlist_item, created = Wishlist.objects.get_or_create(
        user=request.user,
        product=product
    )

    if not created:
        wishlist_item.delete()
        return JsonResponse({
            "success": True,
            "message": "Removed from wishlist",
            "added": False
        })

    return JsonResponse({
        "success": True,
        "message": "Added to wishlist",
        "added": True
    })


@login_required
def wishlist_page(request):

    items = Wishlist.objects.select_related(
        "product",
        "product__brand",
        "product__category"
    ).filter(
        user=request.user
    ).order_by("-created_at")

    return render(
        request,
        "wishlist/wishlist.html",
        {
            "items": items
        }
    )

@login_required
def wishlist_count(request):

    count = Wishlist.objects.filter(
        user=request.user
    ).count()

    return JsonResponse({"count": count})
