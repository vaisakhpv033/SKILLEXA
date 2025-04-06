import razorpay
from skillexa.settings import RZP_KEY_ID, RZP_KEY_SECRET
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from .utils import create_order
from rest_framework.exceptions import ValidationError
from .models import Payments
from students.permissions import IsStudent
from .serializers import CreateOrderSerializer

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

                return Response(razorpay_order, status=status.HTTP_201_CREATED)
            except razorpay.errors.BadRequestError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response({"error": "order creation failed"}, status=status.HTTP_400_BAD_REQUEST)
        

# class VerifyOrderView(APIView):
#     def post(self, request):
