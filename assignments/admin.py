from django.contrib import admin
from .models import Assignment, Submission


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display  = ["title", "course", "deadline", "max_marks", "submission_count", "is_past_deadline", "created_at"]
    list_filter   = ["course"]
    search_fields = ["title", "course__code"]
    ordering      = ["deadline"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display  = ["student", "assignment", "file_type", "file_size", "status", "is_late", "timestamp"]
    list_filter   = ["status", "is_late", "file_type"]
    search_fields = ["student__email", "assignment__title"]
    readonly_fields = ["timestamp", "updated_at", "file_size", "file_name", "file_type"]
