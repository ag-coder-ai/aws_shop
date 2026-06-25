from django.urls import path

from .views import (
    create_payment,
    razorpay_webhook,
)

urlpatterns = [

    path(
        "create/",
        create_payment,
        name="create_payment"
    ),
    path("webhook/", razorpay_webhook),

]