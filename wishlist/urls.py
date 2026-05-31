
from django.urls import path
from .views import (
    toggle_wishlist,
    wishlist_page,
    wishlist_count
)

urlpatterns = [

    path("toggle/", toggle_wishlist, name="toggle_wishlist"),
    path("", wishlist_page,name="wishlist"),
    path("count/", wishlist_count),

]
