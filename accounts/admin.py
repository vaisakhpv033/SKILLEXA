from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import OtpVerification, SocialProfile, User, FCMToken, Notification

# Register your models here.


class CustomUserAdmin(UserAdmin):
    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()

    list_display = (
        "email",
        "first_name",
        "last_name",
        "role",
        "is_active",
        "is_superuser",
    )
    ordering = ("-date_joined",)


admin.site.register(User, CustomUserAdmin)
admin.site.register(SocialProfile)
admin.site.register(OtpVerification)
admin.site.register(FCMToken)
admin.site.register(Notification)
