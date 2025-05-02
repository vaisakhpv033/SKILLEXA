from django.contrib import admin

from .models import Order, OrderItem, Payments

# Register your models here.
class CustomOrderItemAdmin(admin.ModelAdmin):
    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()

    list_display = (
        "order",
        "instructor",
        "price",
        "instructor_earning",
        "admin_earning",
        "is_unlocked",
        "is_refunded",
        "locked_until",
    )
    ordering = ("-created_at",)

admin.site.register(Payments)
admin.site.register(Order)
admin.site.register(OrderItem, CustomOrderItemAdmin)
