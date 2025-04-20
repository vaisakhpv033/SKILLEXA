from django.contrib import admin
from .models import Wallet, WalletTransaction


class CustomWalletAdmin(admin.ModelAdmin):
    """Custom admin for Wallet model."""
    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()

    list_display = (
        "user",
        "balance",
        "locked_balance",
    )
    ordering = ("-created_at",)

class CustomWalletTransactionAdmin(admin.ModelAdmin):
    """Custom admin for walletTransactions model."""
    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()

    list_display = (
        "wallet",
        "transaction_type",
        "amount",
        "order",
    )
    ordering = ("-created_at",)

admin.site.register(Wallet, CustomWalletAdmin)
admin.site.register(WalletTransaction, CustomWalletTransactionAdmin)

