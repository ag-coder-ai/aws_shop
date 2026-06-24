from .views import apply_coupon
from django.urls import path

urlpatterns = [
    path("apply-coupon/", apply_coupon, name="apply_coupon"),
]