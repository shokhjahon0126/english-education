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
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
    )

    phone = PhoneNumberField(unique=True)

    @property
    def is_super_admin(self):
        return self.role == Role.SUPER_ADMIN or (self.is_superuser and self.role != Role.ADMIN)

    @property
    def is_admin_user(self):
        return self.role in [Role.ADMIN, Role.SUPER_ADMIN] or self.is_superuser

    @property
    def is_teacher(self):
        return self.role == Role.TEACHER

    @property
    def is_student(self):
        return self.role == Role.STUDENT