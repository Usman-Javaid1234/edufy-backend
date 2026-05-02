from rest_framework import serializers
from django.utils import timezone
from .models import Rubric, RubricCriterion, Grade, RubricScore


class RubricCriterionSerializer(serializers.ModelSerializer):
    class Meta:
        model  = RubricCriterion
        fields = ["id", "criterion", "description", "max_points", "order"]


class RubricSerializer(serializers.ModelSerializer):
    criteria    = RubricCriterionSerializer(many=True, read_only=True)
    total_points = serializers.IntegerField(read_only=True)

    class Meta:
        model  = Rubric
        fields = ["id", "assignment", "name", "criteria", "total_points", "created_at"]
        read_only_fields = ["id", "created_at"]


class RubricCreateSerializer(serializers.ModelSerializer):
    criteria = RubricCriterionSerializer(many=True)

    class Meta:
        model  = Rubric
        fields = ["assignment", "name", "criteria"]

    def validate_assignment(self, assignment):
        request = self.context.get("request")
        if assignment.course.instructor != request.user:
            raise serializers.ValidationError("You do not own this assignment's course.")
        if hasattr(assignment, "rubric"):
            raise serializers.ValidationError("A rubric already exists for this assignment.")
        return assignment

    def create(self, validated_data):
        criteria_data = validated_data.pop("criteria")
        rubric = Rubric.objects.create(**validated_data, created_by=self.context["request"].user)
        for i, c in enumerate(criteria_data):
            RubricCriterion.objects.create(rubric=rubric, order=i, **c)
        return rubric


class RubricScoreSerializer(serializers.ModelSerializer):
    criterion_name = serializers.CharField(source="criterion.criterion", read_only=True)
    max_points     = serializers.IntegerField(source="criterion.max_points", read_only=True)

    class Meta:
        model  = RubricScore
        fields = ["id", "criterion", "criterion_name", "max_points", "score"]


class GradeSerializer(serializers.ModelSerializer):
    rubric_scores   = RubricScoreSerializer(many=True, read_only=True)
    student_name    = serializers.CharField(source="submission.student.name", read_only=True)
    assignment_title = serializers.CharField(source="submission.assignment.title", read_only=True)
    max_marks       = serializers.IntegerField(source="submission.assignment.max_marks", read_only=True)
    percentage      = serializers.SerializerMethodField()

    class Meta:
        model  = Grade
        fields = [
            "id", "submission", "student_name", "assignment_title",
            "numerical_grade", "max_marks", "percentage",
            "written_feedback", "is_published", "published_at",
            "rubric_scores", "grader", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "published_at", "created_at", "updated_at"]

    def get_percentage(self, obj):
        if obj.numerical_grade is None:
            return None
        max_marks = obj.submission.assignment.max_marks
        if max_marks == 0:
            return 0
        return round((obj.numerical_grade / max_marks) * 100, 1)


class GradeCreateSerializer(serializers.Serializer):
    numerical_grade  = serializers.FloatField(min_value=0)
    written_feedback = serializers.CharField(allow_blank=False)
    publish          = serializers.BooleanField(default=False)
    rubric_scores    = serializers.ListField(
        child=serializers.DictField(), required=False, default=list
    )

    def validate(self, data):
        submission = self.context.get("submission")
        grade_val  = data["numerical_grade"]
        max_marks  = submission.assignment.max_marks

        if grade_val > max_marks:
            raise serializers.ValidationError(
                {"numerical_grade": f"Grade cannot exceed max marks ({max_marks})."}
            )
        return data

    def validate_written_feedback(self, value):
        if not value.strip():
            raise serializers.ValidationError("Written feedback is required before saving a grade.")
        return value

    def save(self, submission, grader):
        data    = self.validated_data
        publish = data["publish"]

        grade, _ = Grade.objects.update_or_create(
            submission=submission,
            defaults={
                "grader":           grader,
                "numerical_grade":  data["numerical_grade"],
                "written_feedback": data["written_feedback"],
                "is_published":     publish,
                "published_at":     timezone.now() if publish else None,
            },
        )

        # Save rubric scores if provided
        rubric_scores = data.get("rubric_scores", [])
        if rubric_scores:
            grade.rubric_scores.all().delete()
            for rs in rubric_scores:
                try:
                    criterion = RubricCriterion.objects.get(pk=rs["criterion_id"])
                    RubricScore.objects.create(
                        grade=grade,
                        criterion=criterion,
                        score=min(rs["score"], criterion.max_points),
                    )
                except (RubricCriterion.DoesNotExist, KeyError):
                    pass

        # Update submission status
        if publish:
            submission.status = "graded"
            submission.save(update_fields=["status"])

        return grade
