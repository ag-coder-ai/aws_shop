from django.urls import path

from .views import (
    create_payment,
    verify_payment,
)

urlpatterns = [

    path(
        "create/",
        create_payment,
        name="create_payment"
    ),
    path(
        "verify/",
        verify_payment,
        name="verify_payment"
    ),

]