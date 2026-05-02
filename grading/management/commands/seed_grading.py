from django.core.management.base import BaseCommand
from accounts.models import User
from assignments.models import Assignment, Submission
from grading.models import Rubric, RubricCriterion, Grade


class Command(BaseCommand):
    help = "Seed rubric and a sample grade for Edufy LMS"

    def handle(self, *args, **kwargs):
        try:
            faculty = User.objects.get(email="faculty@nust.edu.pk")
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR("Run seed_users first."))
            return

        try:
            lab01 = Assignment.objects.get(title="Lab Report 01 – Graph Traversal")
        except Assignment.DoesNotExist:
            self.stdout.write(self.style.ERROR("Run seed_assignments first."))
            return

        # Create rubric for Lab01
        rubric, created = Rubric.objects.get_or_create(
            assignment=lab01,
            defaults={"name": "Lab Report Rubric", "created_by": faculty},
        )
        if created:
            criteria = [
                ("Code Correctness",    40, "Does the implementation produce correct output for all test cases?"),
                ("Code Quality",        20, "Is the code clean, well-commented, and follows naming conventions?"),
                ("Time Complexity",     25, "Is the time complexity analysed correctly and is the solution optimal?"),
                ("Report Presentation", 15, "Is the PDF report well-structured with diagrams and clear explanations?"),
            ]
            for i, (name, pts, desc) in enumerate(criteria):
                RubricCriterion.objects.create(
                    rubric=rubric, criterion=name,
                    max_points=pts, description=desc, order=i,
                )
            self.stdout.write(self.style.SUCCESS(f"  Created rubric: {rubric.name}"))
        else:
            self.stdout.write(f"  Skipped rubric (exists): {rubric.name}")

        # Seed one published grade (ER Diagram — CS305) for student grades page
        try:
            student = User.objects.get(email="student@nust.edu.pk")
            er_assign = Assignment.objects.get(title="ER Diagram Assignment")
            sub, _ = Submission.objects.get_or_create(
                assignment=er_assign,
                student=student,
                defaults={
                    "file":      "submissions/placeholder/er_diagram.pdf",
                    "file_name": "er_diagram.pdf",
                    "file_type": "PDF",
                    "file_size": 204800,
                    "status":    "graded",
                    "is_late":   False,
                },
            )
            grade, g_created = Grade.objects.get_or_create(
                submission=sub,
                defaults={
                    "grader":           faculty,
                    "numerical_grade":  85,
                    "written_feedback": "Good effort, improve code comments.",
                    "is_published":     True,
                },
            )
            if g_created:
                self.stdout.write(self.style.SUCCESS(f"  Created published grade: 85/60 for {student.name}"))
            else:
                self.stdout.write(f"  Skipped grade (exists)")
        except (User.DoesNotExist, Assignment.DoesNotExist):
            pass

        self.stdout.write(self.style.SUCCESS("\nDone."))
