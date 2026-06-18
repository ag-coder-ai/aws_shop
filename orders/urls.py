# orders/urls.py

from django.urls import path
from .views import checkout_view,create_checkout, order_success, order_history, order_detail, track_order,tracking_status_api,download_invoice,cancel_order,request_return


urlpatterns = [
    path("create-checkout/", create_checkout, name="checkout"),
    path("checkout/", checkout_view, name="checkout"),
    path("success/", order_success, name="success"),
    path(
        "history/",
        order_history,
        name="order_history"
    ),
    path(
        "detail/<str:order_id>/",
        order_detail,
        name="order_detail"
    ),
    path(
        "track/<str:order_id>/",
        track_order,
        name="track_order"
    ),

    path(
        "track-api/<str:order_id>/",
        tracking_status_api,
        name="tracking_status_api"
    ),

    path(
        "invoice/<str:order_id>/",
        download_invoice,
        name="download_invoice"
    ),
    path("cancel/<str:order_id>/",
         cancel_order,
         name="cancel_order"),
    path("return/<str:order_id>/",
         request_return,
         name="request_return"),

]