from rest_framework import serializers
from .models import OrderItem, Order, Payments
from django.utils import timezone


class CreateOrderSerializer(serializers.Serializer):
    payment_method = serializers.ChoiceField(choices=["razorpay"], required=True)


class OrderItemSerializer(serializers.ModelSerializer):
    instructor = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ["id", "course_title", "instructor", "discount", "price"]

    def get_instructor(self, obj):
        return obj.instructor.full_name if (hasattr(obj.instructor, "full_name") and obj.instructor.full_name) else None
    

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    razorpay_order_id = serializers.CharField(source="payment.gateway_transaction_id", read_only=True)
    payment_method = serializers.CharField(source="payment.payment_method", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "items",
            "total",
            "discount",
            "status",
            "payment_method",
            "razorpay_order_id",
            "created_at",
        ]




class OrderItemDetialSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrderItem
        fields = [
            "id", "course", "course_title", "price", "discount",
            "instructor_earning", "admin_earning", "is_refunded",
            "refund_amount", "refund_initiated_at", "refund_completed_at",
        ]


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payments
        fields = [
            "payment_method", "amount", "status",
            "gateway_transaction_id", "created_at"
        ]


class StudentOrderHistorySerializer(serializers.ModelSerializer):
    items = OrderItemDetialSerializer(many=True, read_only=True)
    payment = PaymentSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id", "order_number", "total", "discount", "status", "created_at",
            "items", "payment"
        ]






class AdminOrderItemSerializer(serializers.ModelSerializer):
    instructor = serializers.StringRelatedField()

    class Meta:
        model = OrderItem
        fields = [
            "id", "course", "course_title", "price", "discount",
            "instructor", "instructor_earning", "admin_earning",
            "is_refunded", "refund_amount", "refund_initiated_at", "refund_completed_at",
        ]

class AdminOrderHistorySerializer(serializers.ModelSerializer):
    items = AdminOrderItemSerializer(many=True, read_only=True)
    payment = PaymentSerializer(read_only=True)
    user = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id", "order_number", "user", "total", "discount", "status",
            "created_at", "items", "payment"
        ]

    def get_user(self, obj):
        return {
            "id": obj.user.id,
            "email": obj.user.email,
            "full_name": obj.user.full_name if hasattr(obj.user, "full_name") else None,
        }



class CourseRefundSerializer(serializers.Serializer):
    order_item_id = serializers.IntegerField()

    def validate_order_item_id(self, value):
        user = self.context['request'].user 
        try: 
            item = OrderItem.objects.select_related('order', 'order__user').get(id=value)
        except OrderItem.DoesNotExist:
            raise serializers.ValidationError("order item not found")
        
        # Ensuring item belongs to the requesting student
        if item.order.user != user:
            raise serializers.ValidationError("You do not own this order item")
        
        # only completed order can be refunded 
        if item.order.status != Order.OrderStatus.COMPLETED:
            raise serializers.ValidationError("Cannot refund an incomplete order")
        
        # check whether already refunded?
        if item.is_refunded:
            raise serializers.ValidationError("This course has already been refunded")
        
        # Refund window check: within 14 days of purchase
        deadline = item.created_at + timezone.timedelta(days=14, hours=23, minutes=59)
        if timezone.now() > deadline:
            raise serializers.ValidationError("Refund period has expired for this course")
        
        return value