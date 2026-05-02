from django.core.management.base import BaseCommand
from accounts.models import User
from courses.models import Course, Enrollment

COURSES = [
    {
        "code": "CS-401",
        "title": "Advanced Algorithm Design",
        "description": "Graph theory, dynamic programming, NP-completeness and approximation algorithms.",
        "schedule": "Mon/Wed 10:00–11:30",
        "credit_hours": 3,
        "status": "active",
        "faculty_email": "faculty@nust.edu.pk",
    },
    {
        "code": "PSY-210",
        "title": "Cognitive Psychology",
        "description": "Study of mental processes including perception, memory, and reasoning.",
        "schedule": "Tue/Thu 14:00–15:30",
        "credit_hours": 3,
        "status": "active",
        "faculty_email": "faculty@nust.edu.pk",
    },
    {
        "code": "LIT-405",
        "title": "Comparative Literature Seminar",
        "description": "Modernist poetry and the urban landscape across cultural contexts.",
        "schedule": "Fri 09:00–12:00",
        "credit_hours": 3,
        "status": "active",
        "faculty_email": "faculty@nust.edu.pk",
    },
    {
        "code": "CS-305",
        "title": "Database Systems",
        "description": "Relational models, SQL, normalisation, transactions, and NoSQL overview.",
        "schedule": "Mon/Wed/Fri 11:00–12:00",
        "credit_hours": 3,
        "status": "active",
        "faculty_email": "faculty@nust.edu.pk",
    },
]

ENROLL_EMAILS = [
    "student@nust.edu.pk",
    "maria@nust.edu.pk",
    "bilal@nust.edu.pk",
]


class Command(BaseCommand):
    help = "Seed courses and enrolments for Edufy LMS"

    def handle(self, *args, **kwargs):
        created_c = 0
        for c in COURSES:
            faculty_email = c.pop("faculty_email")
            try:
                instructor = User.objects.get(email=faculty_email)
            except User.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"  Faculty not found: {faculty_email} — run seed_users first"))
                continue

            course, created = Course.objects.get_or_create(
                code=c["code"],
                defaults={**c, "instructor": instructor},
            )
            if created:
                created_c += 1
                self.stdout.write(self.style.SUCCESS(f"  Created course: {course.code}"))
            else:
                self.stdout.write(f"  Skipped (exists): {course.code}")

            # Enrol students
            for email in ENROLL_EMAILS:
                try:
                    student = User.objects.get(email=email)
                    enr, enr_created = Enrollment.objects.get_or_create(
                        student=student, course=course,
                        defaults={"status": "active"},
                    )
                    if enr_created:
                        self.stdout.write(f"    Enrolled {student.email} in {course.code}")
                except User.DoesNotExist:
                    pass

        self.stdout.write(self.style.SUCCESS(f"\nDone. Courses created: {created_c}"))
