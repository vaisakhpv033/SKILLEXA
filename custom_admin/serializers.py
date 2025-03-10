from rest_framework import serializers

from accounts.models import User


class AdminUserSerializer(serializers.ModelSerializer):
    """Serializer for listing users in the admin dashboard"""

    # to get the human readable role name
    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "role",
            "role_display",
            "first_name",
            "last_name",
            "phone_number",
            "is_active",
            "is_blocked",
            "date_joined",
            "is_superuser",
        ]
        read_only_fields = [
            "id",
            "username",
            "email",
            "role",
            "first_name",
            "last_nmae",
            "phone_number",
            "is_superuser",
            "date_joined",
        ]
