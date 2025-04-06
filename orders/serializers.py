from rest_framework import serializers


class CreateOrderSerializer(serializers.Serializer):
    payment_method = serializers.ChoiceField(choices=["razorpay"], required=True)