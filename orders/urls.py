from django.urls import path
from .views import CreateOrderView

urlpatterns = [
    path("", CreateOrderView.as_view(), name="create-order"),
]
