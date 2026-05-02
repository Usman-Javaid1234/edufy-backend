from django.db import models
from django.conf import settings


class Course(models.Model):
    class Status(models.TextChoices):
        DRAFT    = "draft",    "Draft"
        ACTIVE   = "active",   "Active"
        ARCHIVED = "archived", "Archived"

    code         = models.CharField(max_length=20, unique=True)
    title        = models.CharField(max_length=200)
    description  = models.TextField(blank=True)
    schedule     = models.CharField(max_length=200, blank=True)
    credit_hours = models.PositiveSmallIntegerField(default=3)
    status       = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    instructor   = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="courses_taught",
        limit_choices_to={"role": "faculty"},
    )
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.code} — {self.title}"

    @property
    def enrolled_count(self):
        return self.enrollments.filter(status="active").count()


class Enrollment(models.Model):
    class Status(models.TextChoices):
        ACTIVE  = "active",  "Active"
        DROPPED = "dropped", "Dropped"

    student    = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="enrollments",
        limit_choices_to={"role": "student"},
    )
    course     = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    status     = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "course")
        ordering        = ["-enrolled_at"]

    def __str__(self):
        return f"{self.student.email} → {self.course.code}"


ALLOWED_MATERIAL_EXTENSIONS = {"pdf", "docx", "pptx", "mp4", "zip"}
MAX_MATERIAL_SIZE_MB = 50


def material_upload_path(instance, filename):
    return f"materials/course_{instance.course.id}/{filename}"


class Material(models.Model):
    class FileType(models.TextChoices):
        PDF   = "pdf",   "PDF"
        DOCX  = "docx",  "DOCX"
        PPTX  = "pptx",  "PPTX"
        VIDEO = "video", "Video"
        ZIP   = "zip",   "ZIP"
        OTHER = "other", "Other"

    course      = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="materials")
    title       = models.CharField(max_length=200)
    file        = models.FileField(upload_to=material_upload_path)
    file_type   = models.CharField(max_length=10, choices=FileType.choices, default=FileType.OTHER)
    file_size   = models.PositiveIntegerField(default=0, help_text="Size in bytes")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="uploaded_materials",
    )
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.course.code})"
