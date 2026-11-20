from django.db import models

# Create your models here.

from django.conf import settings
from pathlib import Path
from uuid import uuid4


def avatar_upload_to(instance, filename):
    extension = Path(filename).suffix.lower()
    return f"avatars/{uuid4().hex}{extension}"



class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="пользователь",
    )
    avatar = models.ImageField(
    "аватар", upload_to=avatar_upload_to, blank=True,
    )

    nick = models.CharField(
        "ник", max_length=50, unique=True, blank=True, null=True,
    )


    class Meta:
        verbose_name = "профиль"
        verbose_name_plural = "профили"

    def __str__(self):
        return self.user.get_username()
