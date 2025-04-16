from rest_framework.permissions import IsAuthenticated
from instructor.permissions import IsInstructor
from rest_framework.exceptions import PermissionDenied


class InstructorOwnedContentMixin:
    permission_classes = [IsAuthenticated, IsInstructor]

    def get_queryset(self):
        user = self.request.user 

        if hasattr(self.queryset.model, "filter_by_instructor"):
            return self.queryset.model.filter_by_instructor(user)
        raise NotImplementedError("Model does not implement filter_by_instructor method.")
    

    def perform_create(self, serializer):
        model_class = serializer.Meta.model
        instance = model_class(**serializer.validated_data)
        course = instance.get_course()

        if course.instructor != self.request.user:
            raise PermissionDenied("You can only create items for your own courses.")

        serializer.save()
    
    def perform_update(self, serializer):
        instance = serializer.instance  # get the instance being updated

        for attr, value in serializer.validated_data.items():
            setattr(instance, attr, value)

        course = instance.get_course()

        if course.instructor != self.request.user:
            raise PermissionDenied("You can only update items for your own courses.")
        
        serializer.save()

    def perform_destroy(self, instance):
        course = instance.get_course()
        if course.instructor != self.request.user:
            raise PermissionDenied("You can only delete items for your own courses.")
        instance.delete()

    