from django.urls import path

from student_management.v1.views.admin_view import AdminDetails, AdminView, AdminViewList
from student_management.v1.views.course_view import (
    CourseDetails,
    CourseDropdownAPIView,
    CourseView,
    CourseViewList,
)
from student_management.v1.views.student_view import StudentDetails, StudentView, StudentViewList

urlpatterns = [
    path("student-list/", StudentViewList.as_view()),
    path("students/", StudentView.as_view()),
    path("students/<int:pk>/", StudentDetails.as_view()),
    path("course-list/", CourseViewList.as_view()),
    path("courses/", CourseView.as_view()),
    path("courses/<int:pk>/", CourseDetails.as_view()),
    path("admin-list/", AdminViewList.as_view()),
    path("auth/users/", AdminView.as_view()),
    path("admin/<int:pk>/", AdminDetails.as_view()),
    path("courses/all/", CourseDropdownAPIView.as_view()),
]
