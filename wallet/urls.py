from django.urls import path
from .views import MyWalletView

urlpatterns = [
    path("my-wallet/", MyWalletView.as_view(), name="my-wallet"),
]
