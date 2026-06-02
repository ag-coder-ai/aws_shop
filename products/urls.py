# products/urls.py

from django.urls import path

from .views import ProductListView,ProductDetailView,category_products


urlpatterns = [

    path(
        'products/',
        ProductListView.as_view(),
        name='product_list'
    ),

    path(
        "product/<slug:slug>/",
        ProductDetailView.as_view(),
        name="product_detail"
    ),
    path(
        "category/<slug:slug>/",
        category_products,
        name="category_products"
    ),

]
