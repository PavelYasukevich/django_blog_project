from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Post

User = get_user_model()


class UsersAppTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="Testuser", password="testpass123"
        )
        self.client = Client()
        self.login_client = Client()
        self.login_client.force_login(self.user)

    def test_user_create(self):
        url = reverse("signup")
        response = self.client.post(
            url,
            {
                "first_name": "Test",
                "last_name": "User",
                "username": "Testuser1",
                "email": "testusr@test.com",
                "password1": "testpass123",
                "password2": "testpass123",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.get(email="testusr@test.com"))

    def test_user_login(self):
        url = reverse("login")
        response = self.client.post(
            url,
            {
                "username": "Testuser",
                "password": "testpass123",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

    def test_user_profile(self):
        url = reverse("profile", args=[self.user.username])
        response = self.login_client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
