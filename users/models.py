from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    CUSTOMER = 'customer'
    SELLER = 'seller'

    ROLE_CHOICES = [
        (CUSTOMER, 'customer'),
        (SELLER, 'seller'),
    ]

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default=CUSTOMER,
    )

    def is_seller(self):
        return self.role == self.SELLER

    def is_customer(self):
        return self.role == self.CUSTOMER

    def __str__(self):
        return f"{self.username} ({self.role})"