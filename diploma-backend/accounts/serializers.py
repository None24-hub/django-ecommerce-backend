from rest_framework import serializers

from accounts.models import UserProfile


class ProfileSerializer(serializers.ModelSerializer):
    fullName = serializers.CharField(source="full_name")
    avatar = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ("fullName", "email", "phone", "avatar")

    def get_avatar(self, obj):
        if not obj.avatar:
            return None
        return {
            "src": obj.avatar.url,
            "alt": obj.avatar.name.split("/")[-1],
        }

    def get_email(self, obj):
        return obj.user.email


class ProfileUpdateSerializer(serializers.Serializer):
    fullName = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=32)


class PasswordUpdateSerializer(serializers.Serializer):
    currentPassword = serializers.CharField()
    newPassword = serializers.CharField(min_length=6)
