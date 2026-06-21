# home/views.py

from django.shortcuts import render

from products.models import Product
from products.models import Category
from .models import BrandStory
#
# def home_view(request):
#     latest_products = Product.objects.order_by('-id')[:8]
#
#     featured_products = Product.objects.filter(
#         is_featured=True
#     ).order_by('-id')[:5]
#
#     categories = Category.objects.filter(is_active=True).order_by("id")[:6]
#     brand_story = BrandStory.objects.first()
#     best_sellers = Product.objects.filter(
#         is_active=True
#     ).select_related("category").order_by("-created_at")[:8]
#
#     context = {
#         "categories": categories,
#         "best_sellers": best_sellers,
#         "latest_products": latest_products,
#         "featured_products": featured_products,
#         "brand_story":brand_story,
#     }
#
#     print("FEATURED:", featured_products)
#
#     return render(request, "home/home.html", context)

def home_view(request):
    return render(request, "home/home.html", {})