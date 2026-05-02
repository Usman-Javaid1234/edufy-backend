from django.urls import path
from .views import (
    CourseListView, CourseDetailView,
    MaterialUploadView, EnrollView, AllCoursesView,
)

urlpatterns = [
    path("",                         CourseListView.as_view(),    name="course_list"),
    path("catalog/",                 AllCoursesView.as_view(),    name="course_catalog"),
    path("<int:pk>/",                CourseDetailView.as_view(),  name="course_detail"),
    path("<int:pk>/materials/",      MaterialUploadView.as_view(), name="course_materials"),
    path("<int:pk>/enroll/",         EnrollView.as_view(),        name="course_enroll"),
]
