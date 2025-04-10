from django.contrib import admin

from .models import Order, OrderItem, Payments

# Register your models here.


admin.site.register(Payments)
admin.site.register(Order)
admin.site.register(OrderItem)
