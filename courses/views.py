from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from .models import Course, Enrollment, Material
from .serializers import (
    CourseSerializer, CourseCreateSerializer,
    MaterialSerializer, MaterialUploadSerializer,
    EnrollmentSerializer,
)


class IsAuthenticatedFaculty(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "faculty"


class CourseListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role == "faculty":
            courses = Course.objects.filter(instructor=user)
        elif user.role == "student":
            enrolled_ids = Enrollment.objects.filter(
                student=user, status="active"
            ).values_list("course_id", flat=True)
            courses = Course.objects.filter(id__in=enrolled_ids)
        else:
            # admin sees all
            courses = Course.objects.all()

        serializer = CourseSerializer(courses, many=True, context={"request": request})
        return Response(serializer.data)

    def post(self, request):
        if request.user.role != "faculty":
            return Response({"error": "Only faculty can create courses."}, status=403)

        serializer = CourseCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        course = serializer.save(instructor=request.user)
        return Response(
            CourseSerializer(course, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class CourseDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        course = get_object_or_404(Course, pk=pk)
        return Response(CourseSerializer(course, context={"request": request}).data)

    def patch(self, request, pk):
        course = get_object_or_404(Course, pk=pk)
        if request.user.role != "faculty" or course.instructor != request.user:
            return Response({"error": "Forbidden."}, status=403)
        serializer = CourseCreateSerializer(course, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(CourseSerializer(course, context={"request": request}).data)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        course = get_object_or_404(Course, pk=pk)
        if request.user.role != "faculty" or course.instructor != request.user:
            return Response({"error": "Forbidden."}, status=403)
        course.status = "archived"
        course.save(update_fields=["status"])
        return Response({"message": "Course archived."})


class MaterialUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        course    = get_object_or_404(Course, pk=pk)
        materials = course.materials.all()
        return Response(MaterialSerializer(materials, many=True, context={"request": request}).data)

    def post(self, request, pk):
        if request.user.role != "faculty":
            return Response({"error": "Only faculty can upload materials."}, status=403)

        course = get_object_or_404(Course, pk=pk)
        if course.instructor != request.user:
            return Response({"error": "You do not own this course."}, status=403)

        serializer = MaterialUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        material = serializer.save(course=course, uploaded_by=request.user)
        return Response(
            MaterialSerializer(material, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class EnrollView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        if request.user.role != "student":
            return Response({"error": "Only students can enroll."}, status=403)

        course = get_object_or_404(Course, pk=pk)
        if course.status != "active":
            return Response({"error": "Course is not open for enrollment."}, status=400)

        enrollment, created = Enrollment.objects.get_or_create(
            student=request.user,
            course=course,
            defaults={"status": "active"},
        )
        if not created and enrollment.status == "dropped":
            enrollment.status = "active"
            enrollment.save(update_fields=["status"])

        return Response(
            {"message": f"Successfully enrolled in {course.title}."},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def delete(self, request, pk):
        if request.user.role != "student":
            return Response({"error": "Only students can unenroll."}, status=403)

        course     = get_object_or_404(Course, pk=pk)
        enrollment = get_object_or_404(Enrollment, student=request.user, course=course)
        enrollment.status = "dropped"
        enrollment.save(update_fields=["status"])
        return Response({"message": "Unenrolled successfully."})


class AllCoursesView(APIView):
    """Public-ish catalog — any authenticated user can browse all active courses."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        courses = Course.objects.filter(status="active")
        return Response(CourseSerializer(courses, many=True, context={"request": request}).data)
