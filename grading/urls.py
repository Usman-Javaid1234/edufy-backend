from django.urls import path
from .views import (
    RubricView, GradeView,
    PublishGradeView, MyGradesView, CourseGradesView,
)

urlpatterns = [
    path("my-grades/",                              MyGradesView.as_view(),       name="my_grades"),
    path("course/<int:course_pk>/",                 CourseGradesView.as_view(),   name="course_grades"),
    path("assignment/<int:assignment_pk>/rubric/",  RubricView.as_view(),         name="rubric"),
    path("submission/<int:submission_pk>/",         GradeView.as_view(),          name="grade"),
    path("submission/<int:submission_pk>/publish/", PublishGradeView.as_view(),   name="publish_grade"),
]
