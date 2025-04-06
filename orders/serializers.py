from rest_framework import serializers
from .models import OrderItem, Order

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