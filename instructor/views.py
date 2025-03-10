from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .permissions import IsInstructor
from .serializers import InstructorResetPasswordSerializer


class InstructorResetPasswordView(generics.GenericAPIView):
    """Reset Password API view for authenticated Instructors"""

    permission_classes = [IsAuthenticated, IsInstructor]
    serializer_class = InstructorResetPasswordSerializer

    def post(self, request):
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Password Reset Successfully"}, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
