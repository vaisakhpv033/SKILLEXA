import uuid
from datetime import timedelta
from decimal import Decimal

from django.db import models, IntegrityError
from django.utils import timezone


class Payments(models.Model):
    """
    Tracks payment transactions for orders.

    - Records payment data including transaction IDs and status.
    - Supports different payment statuses (Pending, Completed, Failed, Refunded).
    - Stores gateway-specific transaction details and error messages if applicable.
    - Provides a reliable payment history for auditing purposes.

    Fields:
    - user (ForeignKey): The user making the payment.
    - transaction_id (CharField): Unique payment identifier from the system.
    - payment_method (CharField): Payment method used (e.g., Razorpay, Credit Card, PayPal).
    - amount (DecimalField): Payment amount in platform currency.
    - status (CharField): Payment status using `PaymentStatus` choices.
    - gateway_transaction_id (CharField): ID from external payment gateways (e.g., Razorpay).
    - gateway_response (JSONField): Raw response from the payment gateway for reference.
    - error_message (TextField): Error message if payment fails.
    - created_at (DateTimeField): Timestamp when the payment was created.
    - updated_at (DateTimeField): Timestamp when the payment was last updated.

    """

    class PaymentStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"

    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    transaction_id = models.CharField(max_length=255, unique=True, db_index=True)
    payment_method = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=10, choices=PaymentStatus.choices, default=PaymentStatus.PENDING
    )
    gateway_transaction_id = models.CharField(max_length=255, null=True, blank=True)
    gateway_response = models.JSONField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.transaction_id}"

    def generate_transaction_no(self):
        """
        Generates a unique order number using timestamp and UUID
        """

        unique_id = uuid.uuid4().hex[:12].upper()
        timestamp = timezone.now().strftime("%y%m%d%H%M%S")
        return f"SKEXA-{timestamp}{unique_id}"
    
    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = self.generate_transaction_no()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Payments"
        ordering = ["-created_at"]


class Order(models.Model):
    """
    Represents a user's order containing one or multiple courses.

    - Tracks order details including payment, status, and total amount.
    - Supports order lifecycle management with statuses (Pending, Completed, Cancelled, Refunded).
    - Maintains links to the payment record for reference.
    - Ensures only completed orders have valid payments.

    Fields:
    - user (ForeignKey): The user who placed the order.
    - order_number (CharField): Unique identifier for the order.
    - payment (ForeignKey): Payment linked to this order (optional until completed).
    - total (DecimalField): Total amount before applying discounts.
    - discount (DecimalField): Total discount applied.
    - status (CharField): Order status using `OrderStatus` choices.
    - created_at (DateTimeField): When the order was created.
    - updated_at (DateTimeField): Last update time.

    Methods:
    - clean(): Ensures a completed order always has a payment linked to it.
    """

    class OrderStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        REFUNDED = "refunded", "Refunded"

    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    order_number = models.CharField(max_length=255, unique=True, db_index=True)
    payment = models.ForeignKey(
        Payments, on_delete=models.CASCADE, related_name="orders", null=True, blank=True
    )
    total = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(
        max_length=10, choices=OrderStatus.choices, default=OrderStatus.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """
        Ensures that a completed order has a valid payment linked.
        Raises ValueError if the validation fails.
        """

        if self.status == self.OrderStatus.COMPLETED and not self.payment:
            raise ValueError("Completed orders must have a valid payment.")
        
    def generate_transaction_no(self):
        """
        Generates a unique order number using timestamp and UUID
        """

        unique_id = uuid.uuid4().hex[:12].upper()
        timestamp = timezone.now().strftime("%y%m%d%H%M%S")
        return f"{timestamp}{unique_id}"
    
    def save(self, *args, **kwargs):
        """
        Ensure transaction number generation on creation and handle duplicates
        """

        if self._state.adding and not self.order_number:
            for _ in range(5): # retry upto 5 times in case of collision
                self.order_number = self.generate_transaction_no()
                try:
                    super().save(*args, **kwargs)
                    return 
                except IntegrityError:
                    continue
            raise IntegrityError('Failed to generate a unique transaction number')
        else:
            super().save(*args, **kwargs)

    
    def __str__(self):
        return f"{self.user.email} - {self.order_number}"

    class Meta:
        verbose_name_plural = "Orders"
        ordering = ["-created_at"]


class OrderItem(models.Model):
    """
    Represents an individual course within an order.

    - Tracks course information, instructor details, and earnings at the time of purchase.
    - Ensures instructor earnings are locked for 14 days before release.
    - Handles refunds and reverses earnings if applicable.

    Fields:
    - order (ForeignKey): Associated order.
    - course (ForeignKey): Course purchased.
    - instructor (ForeignKey): Instructor at the time of purchase.
    - course_title (CharField): Captured course title to maintain history.
    - price (DecimalField): Final price of the course.
    - discount (DecimalField): Discount applied.
    - instructor_earning (DecimalField): Instructor's 50% share of the earnings.
    - admin_earning (DecimalField): Platform's 50% share of the earnings.
    - is_refunded (BooleanField): Whether the item was refunded.
    - refund_amount (DecimalField): Amount refunded to the user.
    - refund_initiated_at (DateTimeField): Timestamp when the refund was initiated.
    - refund_completed_at (DateTimeField): Timestamp when the refund was completed.
    - locked_until (DateTimeField): Earnings locked for 14 days to handle refunds.
    - created_at (DateTimeField): Creation timestamp.
    - updated_at (DateTimeField): Last update timestamp.

    Methods:
    - set_course_title_and_instructor(): Captures course title and instructor to ensure immutability.
    - calculate_earnings(): Calculates the instructor's and admin's earnings using a 50/50 split.
    - apply_lock_period(): Locks instructor earnings for 14 days.
    - save(): Overrides save to apply all necessary actions before saving the object.
    - initiate_refund(): Handles the refund process, including wallet refunds and earning reversals.
    - unlock_instructor_earnings(): Unlocks instructor earnings if no refund was initiated after 14 days.
    """

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    course = models.ForeignKey("courses.Course", on_delete=models.CASCADE)
    instructor = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    course_title = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    instructor_earning = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    admin_earning = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    is_unlocked = models.BooleanField(default=False)
    is_refunded = models.BooleanField(default=False)
    refund_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    refund_initiated_at = models.DateTimeField(null=True, blank=True)
    refund_completed_at = models.DateTimeField(null=True, blank=True)
    locked_until = models.DateTimeField(default=timezone.now() + timedelta(days=14))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def set_course_title_and_instructor(self):
        if not self.course_title:
            self.course_title = self.course.title
        if not self.instructor:
            self.instructor = self.course.instructor
        if not self.price:
            self.price = self.course.price

    def calculate_earnings(self):
        effective_price = self.price - self.discount
        self.instructor_earning = (effective_price * Decimal("0.5")).quantize(
            Decimal("0.01")
        )
        self.admin_earning = (effective_price - self.instructor_earning).quantize(
            Decimal("0.01")
        )

    def apply_lock_period(self):
        if not self.locked_until:
            self.locked_until = timezone.now() + timedelta(days=14)

    def save(self, *args, **kwargs):
        self.set_course_title_and_instructor()
        self.calculate_earnings()
        self.apply_lock_period()
        super().save(*args, **kwargs)

    def initiate_refund(self):
        """
        Process the refund to the users's wallet and reverse instructor earnings.
        """
        if not self.is_refunded and timezone.now() <= self.created_at + timedelta(
            days=14, hours=23, minutes=59
        ):
            self.is_refunded = True
            self.refund_amount = self.price - self.discount
            self.refund_initiated_at = timezone.now()

            # Refund to user wallet
            self.order.user.wallet.refund(
                self.refund_amount, order=self.order, description="Refund Completed"
            )

            # Reverse instructor earnings if locked
            self.instructor.wallet.locked_balance -= self.instructor_earning
            self.instructor_earning = 0
            self.admin_earning = 0
            self.save()

    def unlock_instructor_earnings(self):
        """
        Unlock instructor earnings after 14 days if no refund was initiated
        """

        if not self.is_refunded and not self.is_unlocked and timezone.now() >= self.locked_until:
            self.instructor.wallet.locked_balance -= self.instructor_earning
            self.instructor.wallet.deposit(
                self.instructor_earning,
                description=f"{self.course_title} purchased by {self.order.user}",
            )
            self.is_unlocked = True
            self.save()

    def __str__(self):
        return f"{self.order.order_number} - {self.course.title}"

    class Meta:
        verbose_name_plural = "Order Items"
        ordering = ["-created_at"]
