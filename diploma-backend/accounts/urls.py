from django.urls import re_path

from accounts.views import (
    ProfileAPIView,
    ProfileAvatarAPIView,
    ProfilePasswordAPIView,
    SignInAPIView,
    SignOutAPIView,
    SignUpAPIView,
)

urlpatterns = [
    re_path(r"^sign-in/?$", SignInAPIView.as_view(), name="sign-in"),
    re_path(r"^sign-up/?$", SignUpAPIView.as_view(), name="sign-up"),
    re_path(r"^sign-out/?$", SignOutAPIView.as_view(), name="sign-out"),
    re_path(r"^profile/?$", ProfileAPIView.as_view(), name="profile"),
    re_path(r"^profile/password/?$", ProfilePasswordAPIView.as_view(), name="profile-password"),
    re_path(r"^profile/avatar/?$", ProfileAvatarAPIView.as_view(), name="profile-avatar"),
]
