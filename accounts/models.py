from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user with role + contact fields for SmartKibadaski."""

    class Roles(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        CUSTOMER = 'customer', 'Customer'

    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.CUSTOMER,
        help_text='Determines dashboard access level.',
    )
    phone = models.CharField(max_length=20, blank=True, default='')
    workplace = models.CharField(max_length=255, blank=True, default='')

    @property
    def is_customer(self) -> bool:
        return self.role == self.Roles.CUSTOMER

    @property
    def is_admin_role(self) -> bool:
        return self.role == self.Roles.ADMIN
