from datetime import datetime, timedelta
from typing import Dict, Optional, Union

from django.db.models import Count, Q, Sum, Avg
from django.db.models.functions import ExtractDay, ExtractYear, ExtractMonth
from django.utils import timezone

from orders.models import Order, OrderItem



def admin_revenue_stats():
    orders = OrderItem.objects.filter(order__status=Order.OrderStatus.COMPLETED, is_refunded=False)

    now = timezone.now()

    start_date = now - timedelta(days=29)
    last_30days = [(start_date + timedelta(days=i)).strftime("%d-%m") for i in range(30)]

    daily_revenue = (
        orders.filter(
            created_at__range = (start_date, now)
        ).annotate(day=ExtractDay('created_at'), month=ExtractMonth('created_at'), year=ExtractYear('created_at'))
        .values('day', 'month', 'year')
        .annotate(total_revenue = Sum('admin_earning'))
        .order_by('year', 'month', 'day')
    )

    last_12months = []
    for i in range(12):
        month = (now.month - i - 1) % 12 + 1
        year = now.year + ((now.month-i-1)//12)
        last_12months.insert(0,(month, year))

    
    query = Q()

    for month, year in last_12months:
        query |= Q(created_at__year=year, created_at__month=month)

    monthly_revenue = (
        orders.filter(query)
            .annotate(month=ExtractMonth('created_at'), year=ExtractYear('created_at'))
            .values('month', 'year')
            .annotate(total_revenue=Sum('admin_earning'))
            .order_by('month')
    )

    return list(daily_revenue), list(monthly_revenue), last_12months, last_30days