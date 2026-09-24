from django.contrib.auth.models import AbstractUser
from django.db import models

class Role(models.TextChoices):
    SUPER_ADMIN = 'SUPER_ADMIN','super_admin'
    ADMIN = 'ADMIN','Admin',
    TEACHER = 'TEACHER','Teacher'
    STUDENT = 'STUDENT','Student'



class User(AbstractUser):
    role = models.CharField(
        choices=Role.choices,
        default=Role.STUDENT
    )