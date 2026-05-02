from django.contrib import admin
from .models import Course, Enrollment, Material


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display  = ["code", "title", "instructor", "status", "enrolled_count", "credit_hours", "created_at"]
    list_filter   = ["status", "credit_hours"]
    search_fields = ["code", "title", "instructor__name"]
    ordering      = ["-created_at"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        ("Course Info",  {"fields": ("code", "title", "description", "schedule", "credit_hours")}),
        ("Management",   {"fields": ("instructor", "status")}),
        ("Timestamps",   {"fields": ("created_at", "updated_at")}),
    )


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display  = ["student", "course", "status", "enrolled_at"]
    list_filter   = ["status"]
    search_fields = ["student__email", "course__code"]
    readonly_fields = ["enrolled_at"]


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display  = ["title", "course", "file_type", "file_size", "uploaded_by", "created_at"]
    list_filter   = ["file_type"]
    search_fields = ["title", "course__code"]
    readonly_fields = ["created_at", "file_size"]
