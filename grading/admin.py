from django.contrib import admin
from .models import Rubric, RubricCriterion, Grade, RubricScore


class RubricCriterionInline(admin.TabularInline):
    model  = RubricCriterion
    extra  = 0
    fields = ["criterion", "description", "max_points", "order"]


@admin.register(Rubric)
class RubricAdmin(admin.ModelAdmin):
    list_display  = ["name", "assignment", "total_points", "created_by", "created_at"]
    search_fields = ["name", "assignment__title"]
    readonly_fields = ["created_at"]
    inlines       = [RubricCriterionInline]


class RubricScoreInline(admin.TabularInline):
    model  = RubricScore
    extra  = 0
    fields = ["criterion", "score"]


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display   = ["submission", "numerical_grade", "is_published", "published_at", "grader", "updated_at"]
    list_filter    = ["is_published"]
    search_fields  = ["submission__student__email", "submission__assignment__title"]
    readonly_fields = ["created_at", "updated_at", "published_at"]
    inlines        = [RubricScoreInline]

    fieldsets = (
        ("Grade",     {"fields": ("submission", "grader", "numerical_grade", "written_feedback")}),
        ("Status",    {"fields": ("is_published", "published_at")}),
        ("Timestamps",{"fields": ("created_at", "updated_at")}),
    )
