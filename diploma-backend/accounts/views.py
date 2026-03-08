import json

from django.contrib.auth import authenticate, get_user_model, login, logout, update_session_auth_hash
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.serializers import (
    PasswordUpdateSerializer,
    ProfileSerializer,
    ProfileUpdateSerializer,
)
from accounts.services import get_or_create_profile

User = get_user_model()


class SignUpAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            payload = json.loads(request.body or b"{}")
        except json.JSONDecodeError:
            return Response({"detail": "Invalid JSON payload"}, status=status.HTTP_400_BAD_REQUEST)

        username = str(payload.get("username", "")).strip()
        password = str(payload.get("password", "")).strip()
        name = str(payload.get("name", "")).strip()
        if not username or not password:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        if User.objects.filter(username=username).exists():
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        user = User.objects.create_user(username=username, password=password)
        profile = get_or_create_profile(user)
        profile.full_name = name
        profile.save(update_fields=["full_name"])
        login(request, user)
        return Response(status=status.HTTP_200_OK)


class SignInAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return Response({"detail": "Invalid JSON payload"}, status=status.HTTP_400_BAD_REQUEST)

        username = str(payload.get("username", "")).strip()
        password = str(payload.get("password", "")).strip()
        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        login(request, user)
        get_or_create_profile(user)
        return Response(status=status.HTTP_200_OK)


class SignOutAPIView(APIView):
    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_200_OK)


class ProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = get_or_create_profile(request.user)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)

    def post(self, request):
        serializer = ProfileUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = get_or_create_profile(request.user)

        profile.full_name = serializer.validated_data["fullName"]
        profile.phone = serializer.validated_data["phone"]
        request.user.email = serializer.validated_data["email"]

        request.user.save(update_fields=["email"])
        profile.save(update_fields=["full_name", "phone"])
        return Response(ProfileSerializer(profile).data)


class ProfilePasswordAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        current_password = serializer.validated_data["currentPassword"]
        new_password = serializer.validated_data["newPassword"]
        if not request.user.check_password(current_password):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        request.user.set_password(new_password)
        request.user.save(update_fields=["password"])
        update_session_auth_hash(request, request.user)
        return Response(status=status.HTTP_200_OK)


class ProfileAvatarAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    max_avatar_size = 2 * 1024 * 1024

    def post(self, request):
        avatar = request.FILES.get("avatar")
        if not avatar:
            return Response({"detail": "Avatar file is required"}, status=status.HTTP_400_BAD_REQUEST)
        if avatar.size > self.max_avatar_size:
            return Response({"detail": "Avatar is too large"}, status=status.HTTP_400_BAD_REQUEST)
        if not getattr(avatar, "content_type", "").startswith("image/"):
            return Response({"detail": "Avatar must be an image"}, status=status.HTTP_400_BAD_REQUEST)

        profile = get_or_create_profile(request.user)
        profile.avatar = avatar
        profile.save(update_fields=["avatar"])
        return Response(ProfileSerializer(profile).data, status=status.HTTP_200_OK)
