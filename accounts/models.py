from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        CUSTOMER = 'customer', 'Customer'
        ENTREPRENEUR = 'entrepreneur', 'Entrepreneur'
        ADMIN = 'admin', 'Admin'

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER)
    phone = models.CharField(max_length=15, blank=True)

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = self.Role.ADMIN
        super().save(*args, **kwargs)

    @property
    def is_customer(self):
        return self.role == self.Role.CUSTOMER and not self.is_staff

    @property
    def is_entrepreneur(self):
        return self.role == self.Role.ENTREPRENEUR

    @property
    def is_platform_admin(self):
        return self.is_staff or self.role == self.Role.ADMIN
