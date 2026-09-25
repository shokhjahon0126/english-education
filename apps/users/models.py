from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class Role(models.TextChoices):
    SUPER_ADMIN = 'SUPER_ADMIN','Super Admin'
    ADMIN = 'ADMIN','Admin',
    TEACHER = 'TEACHER','Teacher'
    STUDENT = 'STUDENT','Student'



class User(AbstractUser):
    role = models.CharField(
        choices=Role.choices,
        default=Role.STUDENT
    )

    phone = PhoneNumberField(unique=True)