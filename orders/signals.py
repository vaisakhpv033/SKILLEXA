from django.db.models.signals import pre_save
from django.dispatch import receiver 
from django.utils import timezone 
from datetime import timedelta 
from decimal import Decimal 
from .models import OrderItem 


@receiver(pre_save, sender=OrderItem)
def order_item_pre_save(sender, instance, **kwargs):
    """ Automatically populate fields before saving """
    if not instance.course_title:
        instance.course_title = instance.course.title

    if not instance.instructor:
        instance.instructor = instance.course.instructor

    if not instance.price:
        instance.price = instance.course.price

    # Calculate earnings
    effective_price = instance.price - instance.discount
    instance.instructor_earning = (effective_price * Decimal("0.5")).quantize(Decimal("0.01"))
    instance.admin_earning = (effective_price - instance.instructor_earning).quantize(Decimal("0.01"))

    # Apply lock period8=
    if not instance.locked_until:
        instance.locked_until = timezone.now() + timedelta(days=14)
