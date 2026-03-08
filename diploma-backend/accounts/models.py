from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    full_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    avatar = models.FileField(upload_to="avatars/", null=True, blank=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.full_name or self.user.username
