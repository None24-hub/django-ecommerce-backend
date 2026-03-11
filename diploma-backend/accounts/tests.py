import json
import os
import shutil
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase

from accounts.services import get_or_create_profile

User = get_user_model()
TEST_MEDIA_ROOT = Path(__file__).resolve().parent / "test_media"
TEST_MEDIA_ROOT.mkdir(exist_ok=True)


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class AccountsApiTests(APITestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)

    def test_sign_up_and_sign_out(self):
        response = self.client.post(
            "/api/sign-up",
            data=json.dumps(
                {"name": "Test User", "username": "test_user", "password": "12345678"}
            ),
            content_type="text/plain",
        )
        self.assertEqual(response.status_code, 200)

        profile_response = self.client.get("/api/profile")
        self.assertEqual(profile_response.status_code, 200)
        self.assertEqual(profile_response.data["fullName"], "Test User")

        sign_out_response = self.client.post("/api/sign-out")
        self.assertEqual(sign_out_response.status_code, 200)
        self.assertEqual(self.client.get("/api/profile").status_code, 403)

    def test_sign_in_with_raw_body_json_string(self):
        User.objects.create_user(username="login_user", password="12345678")
        response = self.client.post(
            "/api/sign-in",
            data=json.dumps({"username": "login_user", "password": "12345678"}),
            content_type="text/plain",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get("/api/profile").status_code, 200)

    def test_profile_update_and_password_change(self):
        user = User.objects.create_user(
            username="profile_user",
            password="old_pass_123",
            email="old@example.com",
        )
        profile = get_or_create_profile(user)
        profile.full_name = "Old Name"
        profile.phone = "+70000000000"
        profile.save(update_fields=["full_name", "phone"])
        self.client.login(username="profile_user", password="old_pass_123")

        response = self.client.post(
            "/api/profile",
            data={
                "fullName": "New Name",
                "email": "new@example.com",
                "phone": "+79998887766",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["fullName"], "New Name")
        self.assertEqual(response.data["email"], "new@example.com")
        self.assertEqual(response.data["phone"], "+79998887766")

        password_response = self.client.post(
            "/api/profile/password",
            data={
                "currentPassword": "old_pass_123",
                "newPassword": "new_pass_456",
            },
            format="json",
        )
        self.assertEqual(password_response.status_code, 200)

        self.client.post("/api/sign-out")
        sign_in_response = self.client.post(
            "/api/sign-in",
            data=json.dumps({"username": "profile_user", "password": "new_pass_456"}),
            content_type="text/plain",
        )
        self.assertEqual(sign_in_response.status_code, 200)

    def test_avatar_upload_and_size_limit(self):
        user = User.objects.create_user(username="avatar_user", password="12345678")
        profile = get_or_create_profile(user)
        self.client.login(username="avatar_user", password="12345678")

        first_avatar = SimpleUploadedFile(
            "avatar.png",
            b"\x89PNG\r\n\x1a\nsmall-image",
            content_type="image/png",
        )
        response = self.client.post("/api/profile/avatar", data={"avatar": first_avatar})
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.data["avatar"])
        self.assertTrue(response.data["avatar"]["src"].startswith("/media/avatars/"))
        profile.refresh_from_db()
        old_file_path = profile.avatar.path
        self.assertTrue(os.path.exists(old_file_path))

        second_avatar = SimpleUploadedFile(
            "avatar-new.png",
            b"\x89PNG\r\n\x1a\nanother-small-image",
            content_type="image/png",
        )
        with self.captureOnCommitCallbacks(execute=True):
            second_response = self.client.post(
                "/api/profile/avatar",
                data={"avatar": second_avatar},
            )
        self.assertEqual(second_response.status_code, 200)

        profile.refresh_from_db()
        self.assertTrue(profile.avatar.name.endswith("avatar-new.png"))
        self.assertNotEqual(profile.avatar.path, old_file_path)
        self.assertFalse(os.path.exists(old_file_path))
        self.assertTrue(os.path.exists(profile.avatar.path))

        large_avatar = SimpleUploadedFile(
            "large.png",
            b"a" * (2 * 1024 * 1024 + 1),
            content_type="image/png",
        )
        large_response = self.client.post(
            "/api/profile/avatar",
            data={"avatar": large_avatar},
        )
        self.assertEqual(large_response.status_code, 400)
