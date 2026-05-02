from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from accounts.models import User
from courses.models import Course
from assignments.models import Assignment, Submission


class Command(BaseCommand):
    help = "Seed assignments and submissions for Edufy LMS"

    def handle(self, *args, **kwargs):
        now = timezone.now()

        try:
            faculty  = User.objects.get(email="faculty@nust.edu.pk")
            student1 = User.objects.get(email="student@nust.edu.pk")
            student2 = User.objects.get(email="maria@nust.edu.pk")
            student3 = User.objects.get(email="bilal@nust.edu.pk")
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR("Run seed_users first."))
            return

        try:
            cs401 = Course.objects.get(code="CS-401")
            psy210 = Course.objects.get(code="PSY-210")
            lit405 = Course.objects.get(code="LIT-405")
            cs305  = Course.objects.get(code="CS-305")
        except Course.DoesNotExist:
            self.stdout.write(self.style.ERROR("Run seed_courses first."))
            return

        assignments_data = [
            {
                "course": cs401,
                "title": "Lab Report 01 – Graph Traversal",
                "description": "Implement BFS and DFS. Submit a PDF report with time complexity analysis.",
                "deadline": now + timedelta(hours=24),
                "max_marks": 100,
            },
            {
                "course": psy210,
                "title": "Case Study Analysis",
                "description": "Review chapters 4–6 and submit a 1500-word case study.",
                "deadline": now + timedelta(hours=48),
                "max_marks": 50,
            },
            {
                "course": lit405,
                "title": "Comparative Analysis Essay",
                "description": "Compare modernist poetry and the urban landscape. Minimum 2000 words.",
                "deadline": now - timedelta(hours=2),   # past deadline for TC-06
                "max_marks": 80,
            },
            {
                "course": cs401,
                "title": "Lab Report 00 – Complexity Analysis",
                "description": "Analyse time and space complexity of sorting algorithms.",
                "deadline": now - timedelta(hours=10),  # past deadline
                "max_marks": 100,
            },
            {
                "course": cs305,
                "title": "ER Diagram Assignment",
                "description": "Design an ER diagram for a hospital management system.",
                "deadline": now + timedelta(hours=72),
                "max_marks": 60,
            },
        ]

        created_a = 0
        assignments = []
        for a in assignments_data:
            obj, created = Assignment.objects.get_or_create(
                title=a["title"],
                course=a["course"],
                defaults={**a, "created_by": faculty},
            )
            assignments.append(obj)
            if created:
                created_a += 1
                self.stdout.write(self.style.SUCCESS(f"  Created assignment: {obj.title}"))
            else:
                self.stdout.write(f"  Skipped (exists): {obj.title}")

        # Seed some submissions on assignment 0 (Lab 01) for grading panel
        lab01 = assignments[0]
        created_s = 0
        for student, fname in [
            (student1, "lab01_alex.pdf"),
            (student2, "lab01_maria.pdf"),
            (student3, "lab01_bilal.pdf"),
        ]:
            _, created = Submission.objects.get_or_create(
                assignment=lab01,
                student=student,
                defaults={
                    "file":      f"submissions/placeholder/{fname}",
                    "file_name": fname,
                    "file_type": "PDF",
                    "file_size": 512000,
                    "status":    "submitted",
                    "is_late":   False,
                },
            )
            if created:
                created_s += 1
                self.stdout.write(self.style.SUCCESS(f"  Created submission: {student.name} → {lab01.title}"))

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. Assignments: {created_a}  Submissions: {created_s}"
        ))
