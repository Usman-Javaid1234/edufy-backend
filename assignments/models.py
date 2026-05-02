from django.db import models
from django.conf import settings
from django.utils import timezone
from courses.models import Course

ALLOWED_SUBMISSION_EXTENSIONS = {"pdf", "docx", "zip"}
MAX_SUBMISSION_SIZE_MB = 50


def submission_upload_path(instance, filename):
    return f"submissions/assignment_{instance.assignment.id}/student_{instance.student.id}/{filename}"


class Assignment(models.Model):
    course       = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="assignments")
    title        = models.CharField(max_length=200)
    description  = models.TextField(blank=True)
    deadline     = models.DateTimeField()
    max_marks    = models.PositiveIntegerField(default=100)
    submission_type = models.CharField(max_length=50, default="PDF/DOCX/ZIP")
    created_by   = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="assignments_created",
    )
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["deadline"]

    def __str__(self):
        return f"{self.title} ({self.course.code})"

    @property
    def is_past_deadline(self):
        return timezone.now() > self.deadline

    @property
    def submission_count(self):
        return self.submissions.count()


class Submission(models.Model):
    class Status(models.TextChoices):
        PENDING   = "pending",   "Pending"
        SUBMITTED = "submitted", "Submitted"
        LATE      = "late",      "Late"
        GRADED    = "graded",    "Graded"

    assignment  = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="submissions")
    student     = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="submissions",
        limit_choices_to={"role": "student"},
    )
    file        = models.FileField(upload_to=submission_upload_path)
    file_name   = models.CharField(max_length=255)
    file_type   = models.CharField(max_length=10)
    file_size   = models.PositiveIntegerField(default=0)
    status      = models.CharField(max_length=10, choices=Status.choices, default=Status.SUBMITTED)
    is_late     = models.BooleanField(default=False)
    timestamp   = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("assignment", "student")
        ordering        = ["-timestamp"]

    def __str__(self):
        return f"{self.student.name} → {self.assignment.title}"
