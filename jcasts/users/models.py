import hashlib

from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserQuerySet(models.QuerySet):
    def for_email(self, email):
        """Returns users matching this email address, including both
        primary and secondary email addresses
        """
        return self.filter(
            models.Q(emailaddress__email__iexact=email) | models.Q(email__iexact=email)
        )

    def matches_usernames(self, names):
        """Returns users matching the (case insensitive) username."""
        if not names:
            return self.none()
        return self.filter(username__iregex=r"^(%s)+" % "|".join(names))


class UserManager(BaseUserManager.from_queryset(UserQuerySet)):
    def create_user(self, username, email, password=None, **kwargs):
        user = self.model(
            username=username, email=self.normalize_email(email), **kwargs
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password, **kwargs):
        return self.create_user(
            username,
            email,
            password,
            is_staff=True,
            is_superuser=True,
            **kwargs,
        )


class User(AbstractUser):
    send_recommendations_email = models.BooleanField(default=True)
    autoplay = models.BooleanField(default=True)

    objects = UserManager()

    def get_email_addresses(self):
        """Get set of emails belonging to user.

        Returns:
            set: set of email addresses
        """
        return {self.email} | set(self.emailaddress_set.values_list("email", flat=True))

    def get_gravatar_url(
        self,
        size=settings.GRAVATAR_DEFAULT_SIZE,
        default=settings.GRAVATAR_DEFAULT_IMAGE,
        rating=settings.GRAVATAR_DEFAULT_RATING,
    ):
        digest = hashlib.md5(self.email.encode("utf-8")).hexdigest()
        qs = urlencode(
            {
                "s": str(size),
                "d": default,
                "r": rating,
            }
        )
        return f"https://www.gravatar.com/avatar/{digest}?{qs}"
