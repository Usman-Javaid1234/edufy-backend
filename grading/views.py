from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from django.utils import timezone
from assignments.models import Submission, Assignment
from .models import Rubric, Grade
from .serializers import (
    RubricSerializer, RubricCreateSerializer,
    GradeSerializer, GradeCreateSerializer,
)


class IsFaculty(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "faculty"


class RubricView(APIView):
    """GET or POST rubric for an assignment."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, assignment_pk):
        assignment = get_object_or_404(Assignment, pk=assignment_pk)
        if not hasattr(assignment, "rubric"):
            return Response({"detail": "No rubric found for this assignment."}, status=404)
        return Response(RubricSerializer(assignment.rubric).data)

    def post(self, request, assignment_pk):
        if request.user.role != "faculty":
            return Response({"error": "Only faculty can create rubrics."}, status=403)

        assignment = get_object_or_404(Assignment, pk=assignment_pk)
        data = {**request.data, "assignment": assignment.pk}
        serializer = RubricCreateSerializer(data=data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        rubric = serializer.save()
        return Response(RubricSerializer(rubric).data, status=status.HTTP_201_CREATED)


class GradeView(APIView):
    """
    GET  — retrieve grade for a submission
    POST — create or update grade (TC-08: draft save + publish)
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, submission_pk):
        submission = get_object_or_404(Submission, pk=submission_pk)

        # Students only see published grades
        if request.user.role == "student":
            if submission.student != request.user:
                return Response({"error": "Forbidden."}, status=403)
            if not hasattr(submission, "grade") or not submission.grade.is_published:
                return Response({"detail": "Grade not yet released."}, status=404)

        elif request.user.role == "faculty":
            if submission.assignment.course.instructor != request.user:
                return Response({"error": "Forbidden."}, status=403)

        if not hasattr(submission, "grade"):
            return Response({"detail": "No grade found."}, status=404)

        return Response(GradeSerializer(submission.grade).data)

    def post(self, request, submission_pk):
        if request.user.role != "faculty":
            return Response({"error": "Only faculty can grade submissions."}, status=403)

        submission = get_object_or_404(Submission, pk=submission_pk)

        if submission.assignment.course.instructor != request.user:
            return Response({"error": "You do not own this course."}, status=403)

        serializer = GradeCreateSerializer(
            data=request.data,
            context={"request": request, "submission": submission},
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        grade = serializer.save(submission=submission, grader=request.user)

        action = "published" if grade.is_published else "saved as draft"
        return Response(
            {
                "message": f"Grade {action} successfully.",
                "grade": GradeSerializer(grade).data,
            },
            status=status.HTTP_201_CREATED,
        )


class PublishGradeView(APIView):
    """Publish a draft grade — separate endpoint for explicit publish action."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, submission_pk):
        if request.user.role != "faculty":
            return Response({"error": "Only faculty can publish grades."}, status=403)

        submission = get_object_or_404(Submission, pk=submission_pk)

        if submission.assignment.course.instructor != request.user:
            return Response({"error": "Forbidden."}, status=403)

        if not hasattr(submission, "grade"):
            return Response({"error": "No grade exists. Save a grade first."}, status=400)

        grade = submission.grade
        if grade.is_published:
            return Response({"message": "Grade is already published."}, status=200)

        grade.is_published = True
        grade.published_at = timezone.now()
        grade.save(update_fields=["is_published", "published_at"])

        submission.status = "graded"
        submission.save(update_fields=["status"])

        return Response(
            {
                "message": "Grade published. Student has been notified.",
                "grade": GradeSerializer(grade).data,
            }
        )


class MyGradesView(APIView):
    """Student views all their published grades."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role != "student":
            return Response({"error": "Only students can access this endpoint."}, status=403)

        grades = Grade.objects.filter(
            submission__student=request.user,
            is_published=True,
        ).select_related(
            "submission__assignment__course",
            "grader",
        ).prefetch_related("rubric_scores__criterion")

        return Response(GradeSerializer(grades, many=True).data)


class CourseGradesView(APIView):
    """Faculty views all grades for a course."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, course_pk):
        if request.user.role != "faculty":
            return Response({"error": "Forbidden."}, status=403)

        from courses.models import Course
        course = get_object_or_404(Course, pk=course_pk)

        if course.instructor != request.user:
            return Response({"error": "You do not own this course."}, status=403)

        grades = Grade.objects.filter(
            submission__assignment__course=course
        ).select_related(
            "submission__student",
            "submission__assignment",
        )

        return Response(GradeSerializer(grades, many=True).data)
