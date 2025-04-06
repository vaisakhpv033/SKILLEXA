from django.urls import path
from .views import CreateOrderView, VerifyOrderView

urlpatterns = [
    path("", CreateOrderView.as_view(), name="create-order"),
    path("razorpay/", VerifyOrderView.as_view(), name="verify-order"),
]
