from decimal import Decimal

from django.db.models import F, Sum 
from rest_framework.exceptions import ValidationError

from cart.models import Cart
from .models import Order, OrderItem
from courses.models import Course





def create_order(request):
    cart_items = Cart.objects.select_related("course").filter(
        student=request.user, course__status=Course.CourseStatus.PUBLISHED
    )
    if not cart_items.exists():
        raise ValidationError("Your Cart is Empty")

    total = cart_items.aggregate(total=Sum(F("course__price")))["total"] or Decimal("0.00") 
    order = Order.objects.create(
        user = request.user,
        total = total, 
        status = Order.OrderStatus.PENDING,
    )

    order_items = [
        OrderItem(
            order=order, 
            course=item.course,
            course_title=item.course.title,
            instructor=item.course.instructor,
            price=item.course.price,
        ) 
        for item in cart_items
    ]
    
    OrderItem.objects.bulk_create(order_items)
    
    
    return order

