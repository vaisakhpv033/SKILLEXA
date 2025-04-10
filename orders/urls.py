from django.urls import path
from .views import CreateOrderView, VerifyOrderView, StudentOrderHistoryView, AdminOrderHistoryView

urlpatterns = [
    path("", CreateOrderView.as_view(), name="create-order"),
    path("razorpay/", VerifyOrderView.as_view(), name="verify-order"),
    path("my-orders/", StudentOrderHistoryView.as_view(), name="my-orders"),
    path("admin/order-history/", AdminOrderHistoryView.as_view(), name="admin-order-history"),
]
