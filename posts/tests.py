import io

from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.images import ImageFile
from django.test import Client, TestCase
from django.urls import reverse
from PIL import Image

from posts.models import Comment, Follow, Group, Post

User = get_user_model()


class PostsAppTest(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username="Testuser")
        self.client = Client()
        self.group = Group.objects.create(
            title="testgroup", slug="tst", description="group for test"
        )
        self.login_client = Client()
        self.login_client.force_login(self.user)

    def tearDown(self):
        Post.objects.all().delete()

    @staticmethod
    def create_test_image():
        img = Image.new("RGB", (50, 50), "black")
        file_obj = io.BytesIO()
        img.save(file_obj, format="JPEG")
        file_obj.seek(0)
        return ImageFile(file_obj, name="testpic")

    def content_check(self, testpost):
        places = [
            reverse("index", args=[]),
            reverse("profile", args=[self.user.username]),
            reverse("group_posts", args=[self.group.slug]),
            reverse("post_view", args=[self.user.username, testpost.id]),
        ]
        for url in places:
            response = self.login_client.get(url)
            paginator = response.context.get("paginator")
            if paginator is not None:
                self.assertEqual(paginator.count, 1)
                post = response.context["page"][0]
            else:
                post = response.context["post"]
            page = response.content

            self.assertEqual(post.text, testpost.text)
            self.assertEqual(post.group, testpost.group)
            self.assertEqual(post.author, testpost.author)
            self.assertEqual(post.image, testpost.image)
            self.assertIn("<img", page.decode("utf-8"))

    def test_new_post(self):
        response = self.login_client.post(
            reverse("new_post"),
            {
                "text": "test post",
                "group": self.group.id,
                "image": Image.new("RGB", (50, 50), "black"),
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.count(), 1)

    def test_unauthorised_new_post(self):
        response = self.client.post(
            reverse("new_post"),
            {"text": "test post", "group": self.group.title},
        )
        with self.assertRaises(Post.DoesNotExist):
            Post.objects.get(text="test post")

        login_url = reverse("login")
        new_post_url = reverse("new_post")
        expected_url = f"{login_url}?next={new_post_url}"
        self.assertRedirects(response, expected_url)

    def test_post_edit(self):
        testpost = Post.objects.create(
            text="test text", author=self.user, group=self.group
        )
        url = reverse("post_edit", args=[self.user.username, testpost.id])
        response = self.login_client.post(
            url,
            {"text": "edit test"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.get(id=1).text, "edit test")

    def test_new_post_in_place(self):
        testpost = Post.objects.create(
            text="test text",
            author=self.user,
            group=self.group,
            image=self.create_test_image(),
        )
        self.content_check(testpost)

    def test_edit_post_in_place(self):
        testpost = Post.objects.create(
            text="test text",
            author=self.user,
            group=self.group,
            image=self.create_test_image(),
        )
        url = reverse("post_edit", args=[self.user.username, testpost.id])
        edited_text = "editet test text"
        response = self.login_client.post(
            url,
            {"text": edited_text, "group": self.group.id},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.get(id=testpost.id).text, edited_text)

        testpost = Post.objects.get(id=testpost.id)
        self.content_check(testpost)

    def test_page_not_found(self):
        response = self.client.get("404")
        self.assertEqual(response.status_code, 404)

    def test_image_format_check(self):
        response = self.login_client.post(
            reverse("new_post"),
            {
                "text": "test post",
                "group": self.group.id,
                "image": ImageFile(io.BytesIO(b"not-an-image")),
            },
            follow=True,
        )
        self.assertFormError(
            response,
            "form",
            "image",
            ("Загрузите правильное изображение. Файл, который вы загрузили, "
            "поврежден или не является изображением."),
        )

    def test_cached_index_page(self):
        testpost1 = Post.objects.create(
            text="test text",
            author=self.user,
            group=self.group,
            image=self.create_test_image(),
        )
        first_response = self.login_client.get(reverse("index"))
        cached_data = first_response.content

        testpost2 = Post.objects.create(
            text="cache test",
            author=self.user,
            group=self.group,
            image=self.create_test_image(),
        )

        second_response = self.login_client.get(reverse("index"))
        self.assertEqual(first_response.content, second_response.content)

        cache.clear()
        third_response = self.login_client.get(reverse("index"))
        self.assertNotEqual(first_response.content, third_response.content)


    def test_follow(self):
        testuser_to_follow = User.objects.create_user(username="Testuser2")
        nonfollower = User.objects.create_user(username="Testuser3")

        # Checking that Follow is created
        self.login_client.get(
            reverse("profile_follow", args=[testuser_to_follow.username])
        )
        self.assertEqual(Follow.objects.count(), 1)

        # Checking that new post appears in follow index if following
        testpost = Post.objects.create(
            text="test text", author=testuser_to_follow
        )
        response = self.login_client.get(reverse("follow_index"))
        self.assertEqual(response.context.get("paginator").count, 1)

        # Checking that new post doesn't appear in follow index if not following
        nonfollower_client = self.client
        nonfollower_client.force_login(nonfollower)
        response = nonfollower_client.get(reverse("follow_index"))
        self.assertEqual(response.context.get("paginator").count, 0)

        # Checking that Follow is deleted
        self.login_client.get(
            reverse("profile_unfollow", args=[testuser_to_follow.username])
        )
        self.assertEqual(Follow.objects.count(), 0)

    def test_commenting_authorized(self):
        testpost = Post.objects.create(text="test text", author=self.user)
        url = reverse("add_comment", args=[self.user.username, testpost.id])
        response = self.login_client.post(
            url,
            {"text": "test comment"},
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), 1)

    def test_commenting_unauthorized(self):
        testpost = Post.objects.create(text="test text", author=self.user)
        url = reverse("add_comment", args=[self.user.username, testpost.id])
        response = self.client.post(
            url,
            {"text": "test comment"},
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), 0)
