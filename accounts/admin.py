from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display    = ["email", "name", "role", "department", "is_active", "failed_attempts", "locked_until", "created_at"]
    list_filter     = ["role", "is_active", "department"]
    search_fields   = ["email", "name"]
    ordering        = ["-created_at"]
    readonly_fields = ["created_at", "updated_at", "failed_attempts", "locked_until"]

    fieldsets = (
        ("Account",     {"fields": ("email", "password")}),
        ("Profile",     {"fields": ("name", "role", "department")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Security",    {"fields": ("failed_attempts", "locked_until")}),
        ("Timestamps",  {"fields": ("created_at", "updated_at")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields":  ("email", "name", "role", "department", "password1", "password2", "is_active", "is_staff"),
        }),
    )
