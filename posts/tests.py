from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.images import ImageFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class PostsAppTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="Testuser")
        self.client = Client()
        self.group = Group.objects.create(
            title="testgroup", slug="tst", description="group for test"
        )
        self.login_client = Client()
        self.login_client.force_login(self.user)

    def tearDown(self):
        Post.objects.all().delete()

    def content_check(self, testpost):
        places = [
            reverse("profile", args=[self.user.username]),
            reverse("index", args=[]),
            reverse("group_posts", args=[self.group.slug]),
            reverse("post_view", args=[self.user.username, testpost.id]),
        ]
        for url in places:
            cache.clear()
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
            self.assertIn("<img", page.decode("utf-8"))

    def test_new_post(self):
        with open("media/posts/testpic.jpg", "rb") as img:
            response = self.login_client.post(
                reverse("new_post"),
                {"text": "test post", "group": self.group.id, "image": img,},
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
        testpost.save()
        url = reverse("post_edit", args=[self.user.username, testpost.id])
        response = self.login_client.post(
            url, {"text": "edit test"}, follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.get(id=1).text, "edit test")

    def test_new_post_in_place(self):
        with open("media/posts/testpic.jpg", "rb") as img:
            testpost = Post.objects.create(
                text="test text",
                author=self.user,
                group=self.group,
                image=ImageFile(img),
            )
            testpost.save()
        self.content_check(testpost)

    def test_edit_post_in_place(self):
        with open("media/posts/testpic.jpg", "rb") as img:
            testpost = Post.objects.create(
                text="test text",
                author=self.user,
                group=self.group,
                image=ImageFile(img),
            )
            testpost.save()
        url = reverse("post_edit", args=[self.user.username, testpost.id])
        edited_text = "editet test text"
        response = self.login_client.post(
            url, {"text": edited_text, "group": self.group.id}, follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.get(id=testpost.id).text, edited_text)

        testpost = Post.objects.get(id=testpost.id)
        self.content_check(testpost)

    def test_page_not_found(self):
        response = self.client.get("404")
        self.assertEqual(response.status_code, 404)

    def test_image_format_check(self):
        with open("media/posts/fail.txt", "rb") as img:
            response = self.login_client.post(
                reverse("new_post"),
                {
                    "text": "test post",
                    "group": self.group.id,
                    "image": ImageFile(img),
                },
                follow=True,
            )
            self.assertFormError(
                response,
                "form",
                "image",
                "Загрузите правильное изображение. Файл, который вы загрузили, поврежден или не является изображением.",
            )

    def test_cached_index_page(self):
        testpost1 = Post.objects.create(
        text="test text", author=self.user, group=self.group
        )
        testpost1.save()
        first_request = self.login_client.get(reverse("index"))

        testpost2 = Post.objects.create(
        text="cache test", author=self.user, group=self.group
        )
        testpost2.save()
        
        second_request = self.login_client.get(reverse("index"))
        self.assertNotIn("cache test", second_request.content.decode("utf-8"))
        
        cache.clear()
        third_request = self.login_client.get(reverse("index"))
        self.assertIn("cache test", third_request.content.decode("utf-8"))


# Создать 1й пост
# Сделать первый запрос (Страница покажет 1 пост)
#  Создать 2й пост
# Сделать второй запрос (Страница покажет все еще 1 пост)
# 5. Очистить кэш (кстати, а как это правильно сделать, так пойдет?)
#  from django.core.cache import cache
#  cache.clear()
# 6. Сделать опять запрос (Страница на этот раз выведет 2 поста)