from django.urls import re_path

from payments.views import PaymentProcessAPIView

urlpatterns = [
    re_path(
        r"^payment/(?P<order_id>\d+)/?$",
        PaymentProcessAPIView.as_view(),
        name="payment-process",
    ),
]
