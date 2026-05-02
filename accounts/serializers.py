from rest_framework import serializers
from django.utils import timezone
from .models import User


class LoginSerializer(serializers.Serializer):
    email    = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email    = data.get("email")
        password = data.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"non_field_errors": "Invalid credentials. Please try again."}
            )

        if not user.is_active:
            raise serializers.ValidationError(
                {"non_field_errors": "Your account has been deactivated. Contact admin."}
            )

        if user.is_locked():
            mins = max(1, int((user.locked_until - timezone.now()).total_seconds() // 60))
            raise serializers.ValidationError(
                {"non_field_errors": f"Account locked. Please try again in {mins} minute(s).",
                 "locked": True}
            )

        if not user.check_password(password):
            user.record_failed_login()
            if user.is_locked():
                raise serializers.ValidationError(
                    {"non_field_errors": "Account locked. Please try again in 15 minutes.",
                     "locked": True}
                )
            remaining = 3 - user.failed_attempts
            raise serializers.ValidationError(
                {"non_field_errors": f"Invalid credentials. {remaining} attempt(s) remaining."}
            )

        user.reset_login_attempts()
        data["user"] = user
        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ["id", "email", "name", "role", "department", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model  = User
        fields = ["email", "name", "role", "department", "password"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
