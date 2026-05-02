from rest_framework import serializers
from django.utils import timezone
from .models import Assignment, Submission, ALLOWED_SUBMISSION_EXTENSIONS, MAX_SUBMISSION_SIZE_MB


class AssignmentSerializer(serializers.ModelSerializer):
    course_code       = serializers.CharField(source="course.code", read_only=True)
    course_title      = serializers.CharField(source="course.title", read_only=True)
    is_past_deadline  = serializers.BooleanField(read_only=True)
    submission_count  = serializers.IntegerField(read_only=True)
    student_status    = serializers.SerializerMethodField()

    class Meta:
        model  = Assignment
        fields = [
            "id", "course", "course_code", "course_title",
            "title", "description", "deadline", "max_marks",
            "submission_type", "is_past_deadline", "submission_count",
            "student_status", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_student_status(self, obj):
        request = self.context.get("request")
        if not request or request.user.role != "student":
            return None
        sub = obj.submissions.filter(student=request.user).first()
        if not sub:
            return "overdue" if obj.is_past_deadline else "upcoming"
        return sub.status


class AssignmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Assignment
        fields = ["course", "title", "description", "deadline", "max_marks", "submission_type"]

    def validate_deadline(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("Deadline must be in the future.")
        return value

    def validate_course(self, course):
        request = self.context.get("request")
        if course.instructor != request.user:
            raise serializers.ValidationError("You do not own this course.")
        return course


class SubmissionSerializer(serializers.ModelSerializer):
    student_name    = serializers.CharField(source="student.name", read_only=True)
    student_email   = serializers.CharField(source="student.email", read_only=True)
    assignment_title = serializers.CharField(source="assignment.title", read_only=True)
    file_url        = serializers.SerializerMethodField()
    file_size_mb    = serializers.SerializerMethodField()
    grade           = serializers.SerializerMethodField()

    class Meta:
        model  = Submission
        fields = [
            "id", "assignment", "assignment_title",
            "student", "student_name", "student_email",
            "file_url", "file_name", "file_type", "file_size", "file_size_mb",
            "status", "is_late", "timestamp", "grade",
        ]
        read_only_fields = ["id", "timestamp", "status", "is_late"]

    def get_file_url(self, obj):
        request = self.context.get("request")
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None

    def get_file_size_mb(self, obj):
        return round(obj.file_size / (1024 * 1024), 2)

    def get_grade(self, obj):
        grade = getattr(obj, "grade", None)
        if grade:
            return {
                "numerical_grade": grade.numerical_grade,
                "written_feedback": grade.written_feedback,
                "is_published": grade.is_published,
            }
        return None


class SubmissionCreateSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, file):
        ext     = file.name.rsplit(".", 1)[-1].lower()
        size_mb = file.size / (1024 * 1024)

        if ext not in ALLOWED_SUBMISSION_EXTENSIONS:
            raise serializers.ValidationError(
                "Unsupported file format. Please upload a PDF, DOCX, or ZIP file."
            )
        if size_mb > MAX_SUBMISSION_SIZE_MB:
            raise serializers.ValidationError(
                f"File size exceeds the {MAX_SUBMISSION_SIZE_MB} MB limit. "
                f"Your file is {size_mb:.1f} MB."
            )
        return file

    def save(self, assignment, student):
        file = self.validated_data["file"]
        ext  = file.name.rsplit(".", 1)[-1].lower()

        # Update existing or create new
        submission, _ = Submission.objects.update_or_create(
            assignment=assignment,
            student=student,
            defaults={
                "file":      file,
                "file_name": file.name,
                "file_type": ext.upper(),
                "file_size": file.size,
                "status":    Submission.Status.SUBMITTED,
                "is_late":   assignment.is_past_deadline,
            },
        )
        return submission
