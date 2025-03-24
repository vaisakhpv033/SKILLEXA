from rest_framework import viewsets, permissions, status
from .serializers import CartSerializer
from students.permissions import IsStudent
from .models import Cart
from rest_framework.response import Response
from rest_framework.decorators import action
from courses.models import Course

class CartViewSet(viewsets.ModelViewSet):
    """
    API for managing student carts
    """

    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated, IsStudent]


    def get_queryset(self):
        """
        Get the authenticated student's cart items
        """
        return Cart.objects.select_related('course').filter(student=self.request.user, course__status = Course.CourseStatus.PUBLISHED)
    

    def perform_create(self, serializer):
        """
        Add a course to the student's cart
        """
        serializer.save(student=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """
        Hard delete a course from the cart
        """
        try:
            cart_item = self.get_object()
            cart_item.delete()
            return Response({"message": "Course removed from cart."}, status=status.HTTP_204_NO_CONTENT)
        except Cart.DoesNotExist:
            return Response({"error": "Course not found in your cart."}, status=status.HTTP_404_NOT_FOUND)
    

    @action(detail=False, methods=['delete'], url_path="clear")
    def clear_cart(self, request):
        """
        Clear all courses from the students cart
        """

        if not Cart.objects.filter(student=request.user).exists():
            return Response({"message": "Your cart is already empty."}, status=status.HTTP_404_NOT_FOUND)
    
        Cart.objects.filter(student=request.user).delete()
        return Response({"message": "Cart cleared successfully."}, status=status.HTTP_204_NO_CONTENT)