from rest_framework import serializers
from .models import Course, Enrollment, Material, ALLOWED_MATERIAL_EXTENSIONS, MAX_MATERIAL_SIZE_MB
from accounts.serializers import UserSerializer


class MaterialSerializer(serializers.ModelSerializer):
    file_url  = serializers.SerializerMethodField()
    file_size_mb = serializers.SerializerMethodField()

    class Meta:
        model  = Material
        fields = ["id", "title", "file_url", "file_type", "file_size", "file_size_mb", "created_at"]

    def get_file_url(self, obj):
        request = self.context.get("request")
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None

    def get_file_size_mb(self, obj):
        return round(obj.file_size / (1024 * 1024), 2)


class MaterialUploadSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    file  = serializers.FileField()

    def validate_file(self, file):
        ext = file.name.rsplit(".", 1)[-1].lower()
        size_mb = file.size / (1024 * 1024)

        if ext not in ALLOWED_MATERIAL_EXTENSIONS:
            raise serializers.ValidationError(
                f"Unsupported file format. Allowed: {', '.join(ALLOWED_MATERIAL_EXTENSIONS).upper()}."
            )
        if size_mb > MAX_MATERIAL_SIZE_MB:
            raise serializers.ValidationError(
                f"File size exceeds the {MAX_MATERIAL_SIZE_MB} MB limit. "
                f"Your file is {size_mb:.1f} MB."
            )
        return file

    def save(self, course, uploaded_by):
        file     = self.validated_data["file"]
        title    = self.validated_data["title"]
        ext      = file.name.rsplit(".", 1)[-1].lower()
        material = Material.objects.create(
            course      = course,
            title       = title,
            file        = file,
            file_type   = ext if ext in {"pdf", "docx", "pptx", "zip"} else "other",
            file_size   = file.size,
            uploaded_by = uploaded_by,
        )
        return material


class EnrollmentSerializer(serializers.ModelSerializer):
    student = UserSerializer(read_only=True)

    class Meta:
        model  = Enrollment
        fields = ["id", "student", "status", "enrolled_at"]


class CourseSerializer(serializers.ModelSerializer):
    instructor_name  = serializers.CharField(source="instructor.name", read_only=True)
    enrolled_count   = serializers.IntegerField(read_only=True)
    materials        = MaterialSerializer(many=True, read_only=True)
    is_enrolled      = serializers.SerializerMethodField()

    class Meta:
        model  = Course
        fields = [
            "id", "code", "title", "description", "schedule",
            "credit_hours", "status", "instructor", "instructor_name",
            "enrolled_count", "materials", "is_enrolled",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "enrolled_count"]

    def get_is_enrolled(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.enrollments.filter(student=request.user, status="active").exists()


class CourseCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Course
        fields = ["code", "title", "description", "schedule", "credit_hours", "status"]

    def validate_code(self, value):
        if Course.objects.filter(code__iexact=value).exists():
            raise serializers.ValidationError(f"A course with code '{value}' already exists.")
        return value.upper()
