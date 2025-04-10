import uuid

from django.db import models
from django.db.models import F
from django.utils import timezone


class Wallet(models.Model):
    """
    Represents a user's wallet for managing platform funds.

    - Tracks available and locked balances for users.
    - Handles deposits, withdrawals, and refunds.
    - Instructor earnings are held in `locked_balance` for 14 days to ensure refund eligibility.
    - Provides a reliable transaction log via `WalletTransaction`.

    Fields:
    - user (ForeignKey): The user to whom the wallet belongs.
    - balance (DecimalField): The available funds in the wallet for withdrawal or purchases.
    - locked_balance (DecimalField): Funds locked temporarily (e.g., instructor earnings) to prevent early withdrawals.
    - created_at (DateTimeField): Timestamp when the wallet was created.
    - updated_at (DateTimeField): Timestamp of the last wallet update.

    Methods:
    - add_transaction(): Helper method to record wallet transactions.
    - deposit(): Adds funds to the wallet, typically from payments or refunds.
    - withdraw(): Deducts funds from the wallet for purchases or payouts.
    - refund(): Credits funds back to the wallet in case of a refund.
    """

    user = models.OneToOneField(
        "accounts.User", on_delete=models.CASCADE, related_name="wallet"
    )
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    locked_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.balance}"

    def add_transaction(
        self, transaction_type, amount, description="", order=None, status=None
    ):
        """
        Records a transaction in the WalletTransaction model.

        Args:
            transaction_type (str): Type of transaction (deposit, withdraw, refund, purchase).
            amount (Decimal): Transaction amount.
            description (str): Optional description of the transaction.
            order (Order, optional): Associated order (if applicable).
            status (str, optional): Status of the transaction. Defaults to 'Completed'.

        Returns:
            WalletTransaction: The created transaction object.
        """

        WalletTransaction.objects.create(
            wallet=self,
            transaction_type=transaction_type,
            amount=amount,
            description=description,
            order=order,
            status=status or WalletTransaction.TransactionStatus.COMPLETED,
        )

    def deposit(self, amount, description=""):
        """
        Adds funds to the user's wallet.

        Args:
            amount (Decimal): Amount to deposit.
            description (str): Optional description for the transaction.

        Raises:
            ValueError: If the amount is negative or zero.

        Returns:
            bool: True if deposit is successful.
        """

        if amount <= 0:
            raise ValueError("amount must be positive")
        self.balance += amount
        self.save()
        self.add_transaction(
            WalletTransaction.TransactionChoices.DEPOSIT,
            amount=amount,
            description=description,
        )
        return True

    def deposit_locked(self, amount, description="Locked deposit", order=None):
        """
        Adds funds to the locked balance of the wallet.

        Args:
            amount (Decimal): Amount to deposit.
            description (str): Optional description for the transaction.

        Raises:
            ValueError: If the amount is negative or zero.

        Returns:
            bool: True if deposit is successful.
        """

        if amount <= 0:
            raise ValueError("amount must be positive")
        self.locked_balance += amount
        self.save()
        self.add_transaction(
            WalletTransaction.TransactionChoices.DEPOSIT,
            amount=amount,
            description=description,
            order=order,
        )
        return True

    def withdraw(self, amount, description="", order=None):
        """
        Withdraws funds from the wallet, ensuring sufficient balance.

        Args:
            amount (Decimal): Amount to withdraw.
            description (str): Optional description for the transaction.
            order (Order, optional): Related order for this withdrawal.

        Raises:
            ValueError: If the balance is insufficient or the amount is invalid.

        Returns:
            bool: True if withdrawal is successful.
        """

        if amount <= 0:
            raise ValueError("Amount must be positive")
        if Wallet.objects.filter(id=self.id, balance__gte=amount).update(
            balance=F("balance") - amount
        ):
            self.add_transaction(
                WalletTransaction.TransactionChoices.WITHDRAW,
                amount=amount,
                description=description,
                order=order,
            )
            return True
        raise ValueError("Insufficient funds")

    def refund(self, amount, order, description=""):
        """
        Credits funds back to the wallet during a refund.

        Args:
            amount (Decimal): Amount to refund.
            order (Order): The related order for the refund.
            description (str): Optional description of the refund.

        Returns:
            bool: True if the refund is successful.
        """

        if amount <= 0:
            raise ValueError("Amount must be positive")
        self.balance += amount
        self.save()

        # create a transaction record for the refund
        self.add_transaction(
            WalletTransaction.TransactionChoices.REFUND,
            amount=amount,
            description=description,
            order=order,
        )
        return True


class WalletTransaction(models.Model):
    """
    Logs all wallet-related financial activities.

    - Tracks deposits, withdrawals, refunds, and purchases.
    - Provides a detailed transaction history for auditing purposes.
    - Each transaction is linked to a specific wallet and optionally to an order.
    - Transaction IDs are auto-generated using UUID for uniqueness.

    Fields:
    - wallet (ForeignKey): The wallet associated with the transaction.
    - transaction_no (CharField): Unique identifier for the transaction.
    - transaction_type (CharField): Type of transaction using `TransactionChoices`.
    - amount (DecimalField): Transaction amount.
    - description (CharField): Optional transaction description.
    - order (ForeignKey): Linked order if applicable.
    - status (CharField): Transaction status using `TransactionStatus`.
    - created_at (DateTimeField): Timestamp when the transaction was created.

    Methods:
    - save(): Auto-generates a unique transaction number before saving.
    """

    class TransactionChoices(models.TextChoices):
        DEPOSIT = "deposit", "Deposit"
        WITHDRAW = "withdraw", "Withdraw"
        REFUND = "refund", "Refund"
        PURCHASE = "purchase", "Purchase"

    class TransactionStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    wallet = models.ForeignKey(
        Wallet, on_delete=models.CASCADE, related_name="transactions"
    )
    transaction_no = models.CharField(
        max_length=100, unique=True, blank=True, null=True
    )
    transaction_type = models.CharField(
        max_length=10, choices=TransactionChoices.choices
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255, blank=True, null=True)
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="transactions",
        blank=True,
        null=True,
    )
    status = models.CharField(
        max_length=10,
        choices=TransactionStatus.choices,
        default=TransactionStatus.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        """
        Generates a unique transaction number before saving.

        - Combines a timestamp and a random UUID for uniqueness.
        - Ensures no duplicates by enforcing `unique=True` on `transaction_no`.
        """

        if not self.transaction_no:
            unique_id = unique_id = uuid.uuid4().hex[:10].upper()
            timestamp = timezone.now().strftime("%y%m%d%H%M%S")
            self.transaction_no = f"SKEXA-{timestamp}-{unique_id}"
        super().save(*args, **kwargs)
