from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from assignments.models import Assignment, Submission


class Rubric(models.Model):
    assignment  = models.OneToOneField(Assignment, on_delete=models.CASCADE, related_name="rubric")
    name        = models.CharField(max_length=200)
    created_by  = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="rubrics_created",
    )
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rubric: {self.name} ({self.assignment.title})"

    @property
    def total_points(self):
        return self.criteria.aggregate(
            total=models.Sum("max_points")
        )["total"] or 0


class RubricCriterion(models.Model):
    rubric      = models.ForeignKey(Rubric, on_delete=models.CASCADE, related_name="criteria")
    criterion   = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    max_points  = models.PositiveIntegerField()
    order       = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.criterion} ({self.max_points} pts)"


class Grade(models.Model):
    submission      = models.OneToOneField(Submission, on_delete=models.CASCADE, related_name="grade")
    grader          = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="grades_given",
    )
    numerical_grade  = models.FloatField(
        validators=[MinValueValidator(0)],
        null=True, blank=True,
    )
    written_feedback = models.TextField(blank=True)
    is_published     = models.BooleanField(default=False)
    published_at     = models.DateTimeField(null=True, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    def __str__(self):
        status = "Published" if self.is_published else "Draft"
        return f"{self.submission.student.name} — {self.numerical_grade} [{status}]"


class RubricScore(models.Model):
    grade     = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name="rubric_scores")
    criterion = models.ForeignKey(RubricCriterion, on_delete=models.CASCADE)
    score     = models.FloatField(validators=[MinValueValidator(0)])

    class Meta:
        unique_together = ("grade", "criterion")

    def __str__(self):
        return f"{self.criterion.criterion}: {self.score}/{self.criterion.max_points}"
