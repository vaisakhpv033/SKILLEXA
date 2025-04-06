from decimal import Decimal

from django.db.models import F, Sum 
from rest_framework.exceptions import ValidationError

from cart.models import Cart
from .models import Order, OrderItem
from courses.models import Course
from skillexa.settings import RZP_KEY_SECRET
import hmac
import hashlib




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


def verify_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
    # Use the key_secret from your Razorpay account
    key_secret = RZP_KEY_SECRET
    message = f"{razorpay_order_id}|{razorpay_payment_id}"

    # Generate the HMAC SHA256 signature
    generated_signature = hmac.new(
        key_secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()

    # Compare signatures
    return generated_signature == razorpay_signature