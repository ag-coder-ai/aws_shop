# home/views.py

from django.shortcuts import render

from products.models import Product
from products.models import Category

def home_view(request):

    categories = Category.objects.filter(
        is_active=True
    ).order_by(
        "name"
    )[:6]

    best_sellers = Product.objects.filter(
        is_active=True
    ).select_related(
        "category"
    ).order_by(
        "-created_at"
    )[:8]

    context = {

        "categories": categories,

        "best_sellers": best_sellers,

    }

    return render(
        request,
        "home/home.html",
        context
    )