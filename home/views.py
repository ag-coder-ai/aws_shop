# home/views.py

from django.shortcuts import render

from products.models import Product
from products.models import Category


def home_view(request):

    categories = Category.objects.all()[:8]

    best_sellers = Product.objects.filter(
        is_active=True
    ).order_by("-created_at")[:8]

    context = {

        "categories": categories,

        "best_sellers": best_sellers,

    }

    return render(
        request,
        "home/home.html",
        context
    )