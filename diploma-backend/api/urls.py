from django.urls import include, path

from api.views import HealthCheckAPIView

urlpatterns = [
    path("health/", HealthCheckAPIView.as_view(), name="health"),
    path("", include("accounts.urls")),
    path("", include("catalog.urls")),
]
