import razorpay
from skillexa.settings import RZP_KEY_ID, RZP_KEY_SECRET
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from .utils import create_order, verify_signature
from rest_framework.exceptions import ValidationError
from .models import Payments, Order
from cart.models import Cart
from students.permissions import IsStudent
from .serializers import CreateOrderSerializer, OrderSerializer

client = razorpay.Client(auth=(RZP_KEY_ID, RZP_KEY_SECRET))

class CreateOrderView(APIView):
    permission_classes = [IsStudent]

    def post(self, request):
        serializer = CreateOrderSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user 
        payment_method = serializer.validated_data['payment_method']
        
        try:
            # create the order
            order = create_order(request)

        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

        if payment_method == "razorpay":
            amount = int(order.total * 100) # amount in paisa
            data = {
                "amount": amount,
                "currency": "INR",
                "receipt": f"RZP-{order.order_number}",
            }
            try:
                razorpay_order = client.order.create(data=data)
                rzp_order_id = razorpay_order["id"]

                payment = Payments.objects.create(
                    user = user,
                    payment_method = "Razorpay",
                    amount = amount,
                    gateway_transaction_id = rzp_order_id,
                )

                order.payment = payment 
                order.save()

                serialized_order = OrderSerializer(order)
                return Response(serialized_order.data, status=status.HTTP_201_CREATED)
            except razorpay.errors.BadRequestError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response({"error": "order creation failed"}, status=status.HTTP_400_BAD_REQUEST)
        

class VerifyOrderView(APIView):
     def post(self, request):
        data = request.data 
        razorpay_order_id = data.get("razorpay_order_id")
        razorpay_payment_id = data.get("razorpay_payment_id")
        razorpay_signature = data.get("razorpay_signature")
        order_id = data.get("order_id")

        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature, order_id]):
            return Response({"error": "Missing required parameters"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify the signature
        if not verify_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
            return Response({"error": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        # Check if already completed
        if order.status == Order.OrderStatus.COMPLETED:
            return Response({"message": "Order already verified"}, status=status.HTTP_200_OK)

        try:
            payment = Payments.objects.get(gateway_transaction_id=razorpay_order_id)
        except Payments.DoesNotExist:
            return Response({"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)

        # Update payment and order status
        payment.gateway_response = data
        payment.status = Payments.PaymentStatus.COMPLETED
        payment.save()

        order.payment = payment 
        order.status = Order.OrderStatus.COMPLETED
        order.save()

        # Re-trigger save logic for each order item (earnings etc)
        for item in order.items.all():
            item.save()
        
        # Clear the cart after successful payment
        Cart.objects.filter(student=request.user).delete()
        
        return Response({"message": "Payment verified successfully"}, status=status.HTTP_200_OK)