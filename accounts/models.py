from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ROLE_ADMIN = 'admin'
    ROLE_USER = 'user'

    ROLE_CHOICES = (
        (ROLE_ADMIN, 'Admin'),
        (ROLE_USER, 'User'),
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_USER)

    def __str__(self):
        return f"{self.username} ({self.email})"

    def is_admin_role(self):
        return self.role == self.ROLE_ADMIN

    def is_user_role(self):
        return self.role == self.ROLE_USER
