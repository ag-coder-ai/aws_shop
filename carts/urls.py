from django.urls import path

from .views import (

    cart_view,
    add_to_cart,
    update_cart_quantity,
    remove_cart_item,
    cart_summary,

)

urlpatterns = [

    path(
        "add/",
        add_to_cart,
        name="add_to_cart"
    ),

    path(
        '',
        cart_view,
        name='carts'
    ),
    path(
        'update/',
        update_cart_quantity,
        name='update_cart_quantity'
    ),

    path(
        'remove/',
        remove_cart_item,
        name='remove_cart_item'
    ),
    path(
        "summary/",
        cart_summary,
        name="cart_summary"
    ),
]