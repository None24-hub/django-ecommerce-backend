from django.urls import re_path

from orders.views import OrderDetailAPIView, OrdersAPIView

urlpatterns = [
    re_path(r"^orders/?$", OrdersAPIView.as_view(), name="orders"),
    re_path(r"^orders/(?P<order_id>\d+)/?$", OrderDetailAPIView.as_view(), name="orders-detail"),
    # Совместимость с текущим фронтовым JS, который вызывает /api/order/{id}
    re_path(r"^order/(?P<order_id>\d+)/?$", OrderDetailAPIView.as_view(), name="order-detail"),
]
