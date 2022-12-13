from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    location = models.CharField(max_length=255, blank=True)
    bio = models.TextField(
        blank=True,
        help_text="Brief description for your profile. URLs are hyperlinked.",
    )

    personal_website = models.URLField(
        blank=True, help_text="Your home page, blog or company site."
    )
