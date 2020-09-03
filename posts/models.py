from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver

User = get_user_model()


class Post(models.Model):
    text = models.TextField("Текст публикации", help_text="Текст публикации")
    pub_date = models.DateTimeField(
        "Дата публикации", auto_now_add=True, help_text="Дата публикации"
    )
    edit_date = models.DateTimeField(
        "Дата последнего редактирования",
        auto_now=True,
        help_text="Дата последнего редактирования",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name="Автор",
        help_text="Автор публикации",
    )
    group = models.ForeignKey(
        "Group",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posts",
        verbose_name="Группа",
        help_text="Группа для публикации",
    )
    image = models.ImageField(upload_to="posts/", blank=True, null=True)

    class Meta:
        ordering = ["-pub_date"]

    def __str__(self):
        fragment = (
            self.text if len(self.text) <= 50 else self.text[:50] + "..."
        )
        date = self.pub_date.strftime("%d %m %Y")
        author = self.author
        return f"{author} - {date} - {fragment}"


@receiver(post_delete, sender=Post)
def submission_delete(sender, instance, **kwargs):
    instance.image.delete(False)


class Group(models.Model):
    title = models.CharField(unique=True, max_length=200)
    slug = models.SlugField(unique=True, max_length=20)
    description = models.TextField()

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Публикация",
        help_text="Прокомментированная публикация",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Автор",
        help_text="Автор публикации",
    )
    text = models.TextField("Текст комментария", help_text="Текст комментария")
    created = models.DateTimeField(
        "Дата комментирования",
        auto_now_add=True,
        help_text="Дата комментирования",
    )


class Follow(models.Model):
    user = models.ForeignKey(User, related_name="follower", on_delete=models.CASCADE)
    author = models.ForeignKey(User, related_name="following", on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f'{self.user.username} follows {self.author.username}'
