from rest_framework import serializers
from .models import Wallet, WalletTransaction


class WalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransaction
        fields = [
            "transaction_no",
            "transaction_type",
            "amount",
            "description",
            "status",
            "created_at",
        ]


class WalletSerializer(serializers.ModelSerializer):
    transactions = WalletTransactionSerializer(many=True, read_only=True)

    class Meta:
        model = Wallet
        fields = [
            "balance",
            "locked_balance",
            "created_at",
            "updated_at",
            "transactions",
        ]
