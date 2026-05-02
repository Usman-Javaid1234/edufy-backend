from django.urls import path
from .views import (
    AssignmentListView, AssignmentDetailView,
    SubmitAssignmentView, SubmissionListView, SubmissionDetailView,
)

urlpatterns = [
    path("",                              AssignmentListView.as_view(),   name="assignment_list"),
    path("<int:pk>/",                     AssignmentDetailView.as_view(), name="assignment_detail"),
    path("<int:pk>/submit/",              SubmitAssignmentView.as_view(), name="assignment_submit"),
    path("<int:pk>/submissions/",         SubmissionListView.as_view(),   name="submission_list"),
    path("submissions/<int:pk>/",         SubmissionDetailView.as_view(), name="submission_detail"),
]
