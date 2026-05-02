from django.core.management.base import BaseCommand
from accounts.models import User


USERS = [
    {"email": "student@nust.edu.pk",  "name": "Alex Rivera",        "role": "student", "department": "CS",  "password": "Test@1234"},
    {"email": "faculty@nust.edu.pk",  "name": "Dr. Sarah Jenkins",  "role": "faculty", "department": "CS",  "password": "Test@1234"},
    {"email": "admin@nust.edu.pk",    "name": "Admin User",         "role": "admin",   "department": "IT",  "password": "Test@1234", "is_staff": True, "is_superuser": True},
    {"email": "maria@nust.edu.pk",    "name": "Maria Hassan",       "role": "student", "department": "CS",  "password": "Test@1234"},
    {"email": "bilal@nust.edu.pk",    "name": "Bilal Ahmed",        "role": "student", "department": "SE",  "password": "Test@1234"},
    {"email": "omar@nust.edu.pk",     "name": "Dr. Omar Sheikh",    "role": "faculty", "department": "EE",  "password": "Test@1234"},
    {"email": "zara@nust.edu.pk",     "name": "Zara Malik",         "role": "student", "department": "CS",  "password": "Test@1234", "is_active": False},
]


class Command(BaseCommand):
    help = "Seed initial users for Edufy LMS"

    def handle(self, *args, **kwargs):
        created = 0
        skipped = 0
        for u in USERS:
            password   = u.pop("password")
            is_staff   = u.pop("is_staff", False)
            is_super   = u.pop("is_superuser", False)
            is_active  = u.pop("is_active", True)

            if User.objects.filter(email=u["email"]).exists():
                skipped += 1
                self.stdout.write(f"  Skipped (exists): {u['email']}")
                continue

            user = User.objects.create_user(
                password=password,
                is_staff=is_staff,
                is_superuser=is_super,
                is_active=is_active,
                **u,
            )
            created += 1
            self.stdout.write(self.style.SUCCESS(f"  Created: {user.email} [{user.role}]"))

        self.stdout.write(self.style.SUCCESS(f"\nDone. Created: {created}  Skipped: {skipped}"))
