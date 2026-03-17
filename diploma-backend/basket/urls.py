from django.urls import re_path

from basket.views import BasketAPIView

urlpatterns = [
    re_path(r"^basket/?$", BasketAPIView.as_view(), name="basket"),
]
