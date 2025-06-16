
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

class EstudianteManager(BaseUserManager):
    def create_superuser(self, dni, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if not dni:
            raise ValueError('El DNI debe estar definido')
        user = self.model(dni=dni, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

class Estudiante(AbstractUser):
    FORMATO_CHOICES = [
        ('general', 'Formato general'),
        ('kinder', 'Formato Kinder'),
        ('first', 'Formato First'),
    ]

    dni = models.IntegerField(unique=True)
    boletin_data = models.JSONField(default=dict)
    formato_boletin = models.CharField(max_length=10, choices=FORMATO_CHOICES, default='general')

    USERNAME_FIELD = 'dni'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', 'email']

    objects = EstudianteManager()

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.dni})"


""" from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

class EstudianteManager(BaseUserManager):
    def create_superuser(self, dni, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if not dni:
            raise ValueError('The given dni must be set')
        user = self.model(dni=dni, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

class Estudiante(AbstractUser):
    dni = models.IntegerField(unique=True)
    boletin_data = models.JSONField(default=dict)

    USERNAME_FIELD = 'dni'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', 'email']

    objects = EstudianteManager()

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.dni})"
 """