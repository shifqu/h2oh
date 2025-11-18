"""Users models."""

from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Extend the default user model."""
