from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", "admin")
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        STUDENT = "student", "Student"
        FACULTY = "faculty", "Faculty"
        ADMIN   = "admin",   "Admin"

    email      = models.EmailField(unique=True)
    name       = models.CharField(max_length=150)
    role       = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT)
    department = models.CharField(max_length=100, blank=True)
    is_active  = models.BooleanField(default=True)
    is_staff   = models.BooleanField(default=False)

    failed_attempts = models.PositiveSmallIntegerField(default=0)
    locked_until    = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD  = "email"
    REQUIRED_FIELDS = ["name"]

    objects = UserManager()

    class Meta:
        verbose_name        = "User"
        verbose_name_plural = "Users"
        ordering            = ["-created_at"]

    def __str__(self):
        return f"{self.name} <{self.email}> [{self.role}]"

    def is_locked(self):
        return bool(self.locked_until and timezone.now() < self.locked_until)

    def record_failed_login(self):
        self.failed_attempts += 1
        if self.failed_attempts >= 3:
            self.locked_until = timezone.now() + timezone.timedelta(minutes=15)
            self.failed_attempts = 0
        self.save(update_fields=["failed_attempts", "locked_until"])

    def reset_login_attempts(self):
        self.failed_attempts = 0
        self.locked_until    = None
        self.save(update_fields=["failed_attempts", "locked_until"])
