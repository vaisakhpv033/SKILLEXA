from celery import shared_task
from django.utils import timezone
from .models import OrderItem

@shared_task
def unlock_instructor_earnings_task():
    print("task running");
    eligible_items = OrderItem.objects.filter(
        is_refunded=False,
        is_unlocked=False,
        locked_until__lte=timezone.now(),
        instructor_earning__gt=0,
    )

    for item in eligible_items:
        item.unlock_instructor_earnings()
    return f"Unlocked {eligible_items.count()} items"
