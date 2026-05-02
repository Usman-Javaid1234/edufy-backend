from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Assignment, Submission
from .serializers import (
    AssignmentSerializer, AssignmentCreateSerializer,
    SubmissionSerializer, SubmissionCreateSerializer,
)
from courses.models import Course, Enrollment


class AssignmentListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.role == "faculty":
            # Faculty sees assignments for their courses
            assignments = Assignment.objects.filter(
                course__instructor=user
            ).select_related("course")

        elif user.role == "student":
            # Student sees assignments for enrolled courses only
            enrolled_course_ids = Enrollment.objects.filter(
                student=user, status="active"
            ).values_list("course_id", flat=True)
            assignments = Assignment.objects.filter(
                course_id__in=enrolled_course_ids
            ).select_related("course").prefetch_related("submissions")

        else:
            assignments = Assignment.objects.all().select_related("course")

        serializer = AssignmentSerializer(
            assignments, many=True, context={"request": request}
        )
        return Response(serializer.data)

    def post(self, request):
        if request.user.role != "faculty":
            return Response({"error": "Only faculty can create assignments."}, status=403)

        serializer = AssignmentCreateSerializer(
            data=request.data, context={"request": request}
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        assignment = serializer.save(created_by=request.user)
        return Response(
            AssignmentSerializer(assignment, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class AssignmentDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        assignment = get_object_or_404(Assignment, pk=pk)
        return Response(
            AssignmentSerializer(assignment, context={"request": request}).data
        )


class SubmitAssignmentView(APIView):
    """TC-05 (valid), TC-06 (past deadline), TC-07 (bad format) all handled here."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        if request.user.role != "student":
            return Response({"error": "Only students can submit assignments."}, status=403)

        assignment = get_object_or_404(Assignment, pk=pk)

        # TC-06 — Deadline passed
        if assignment.is_past_deadline:
            return Response(
                {
                    "error": "Deadline has passed. Late submissions are not accepted.",
                    "deadline": assignment.deadline,
                    "submitted_at": timezone.now(),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check enrollment
        enrolled = Enrollment.objects.filter(
            student=request.user,
            course=assignment.course,
            status="active",
        ).exists()
        if not enrolled:
            return Response(
                {"error": "You are not enrolled in this course."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # TC-07 — File format + size validation
        serializer = SubmissionCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # TC-05 — Save submission
        submission = serializer.save(assignment=assignment, student=request.user)
        return Response(
            {
                "message": "Assignment submitted successfully.",
                "submission": SubmissionSerializer(
                    submission, context={"request": request}
                ).data,
            },
            status=status.HTTP_201_CREATED,
        )


class SubmissionListView(APIView):
    """Faculty views all submissions for an assignment."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        assignment = get_object_or_404(Assignment, pk=pk)

        if request.user.role == "faculty":
            if assignment.course.instructor != request.user:
                return Response({"error": "Forbidden."}, status=403)
            submissions = assignment.submissions.select_related("student").prefetch_related("grade")

        elif request.user.role == "student":
            submissions = assignment.submissions.filter(student=request.user)

        else:
            submissions = assignment.submissions.all()

        return Response(
            SubmissionSerializer(submissions, many=True, context={"request": request}).data
        )


class SubmissionDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        submission = get_object_or_404(Submission, pk=pk)

        # Students can only see their own
        if request.user.role == "student" and submission.student != request.user:
            return Response({"error": "Forbidden."}, status=403)

        return Response(
            SubmissionSerializer(submission, context={"request": request}).data
        )
