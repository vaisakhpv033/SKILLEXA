from rest_framework import serializers
from .models import Course, CourseDetail, Topics, PriceLevel

class CourseDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for course requirements, outcomes, and target audiences.
    """

    class Meta:
        model = CourseDetail
        fields = ["id", "detail_type", "description"]
        read_only_fields = ["id"]

class CourseSerializer(serializers.ModelSerializer):
    """
    Serializer for Course model.
    """
    
    details = CourseDetailSerializer(many=True, required=False)
    topic_name = serializers.CharField(source="topic.name", read_only=True)
    price_id = serializers.PrimaryKeyRelatedField(
        queryset=PriceLevel.objects.filter(deleted_at__isnull=True),
        write_only=True,
        required=True
    )

    class Meta:
        model = Course
        fields = [
            "id", "title", "subtitle", "description", "thumbnail", "trailer",
            "language", "level", "price", "price_id", "status", "topic", "topic_name",
            "created_at", "updated_at", "details"
        ]
        read_only_fields = ["id", "created_at", "updated_at", "instructor", "price"]

    def create(self, validated_data):
        """
        Custom create method to assign instructor and handle nested details.
        """
        request = self.context["request"]
        instructor = request.user  # Get the authenticated instructor

        price_instance = validated_data.pop("price_id")
        validated_data["price"] = price_instance.amount
        validated_data["instructor"] = instructor  # Assign the instructor

        details_data = validated_data.pop("details", [])

        course = Course.objects.create(**validated_data)

        # Handle nested CourseDetail creation
        for detail_data in details_data:
            CourseDetail.objects.create(course=course, **detail_data)

        return course

    def update(self, instance, validated_data):
        """
        Update method for editing course details.
        """
        price_instance = validated_data.pop("price_id", None)
        if price_instance:
            instance.price = price_instance.amount

        details_data = validated_data.pop("details", [])

        # Update basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update CourseDetails
        if details_data:
            instance.details.all().delete()  # Remove old details
            for detail_data in details_data:
                CourseDetail.objects.create(course=instance, **detail_data)

        return instance


class TopicsSerializer(serializers.ModelSerializer):
    """
    Serializer for Topics model.
    - Shows nested subcategories.
    - Admins can create/update categories.
    """

    subcategories = serializers.SerializerMethodField()

    class Meta:
        model = Topics
        fields = ["id", "name", "parent", "score", "created_at", "updated_at", "subcategories"]
        read_only_fields = ["id", "created_at", "updated_at", "subcategories"]

    def get_subcategories(self, obj):
        """Recursively fetch all subcategories for a given topic."""
        subcategories = obj.subcategories.all()
        return TopicsSerializer(subcategories, many=True).data

    def validate_name(self, value):
        """Ensure unique category names (case insensitive)."""
        if Topics.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("A topic with this name already exists.")
        return value
    
    def validate_parent(self, value):
        """Ensure a topic is not assigned as its own parent."""
        if self.instance and self.instance.id == value.id:
            raise serializers.ValidationError("A category cannot be its own parent.")
        return value

