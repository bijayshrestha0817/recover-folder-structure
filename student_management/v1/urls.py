from django.urls import path

from student_management.v1.views.course_view import CourseDetails, CourseView, CourseViewList
from student_management.v1.views.student_view import StudentDetails, StudentView, StudentViewList

urlpatterns = [
    path("student-list/", StudentViewList.as_view()),
    path("students/", StudentView.as_view()),
    path("students/<int:pk>/", StudentDetails.as_view()),
    path("course-list/", CourseViewList.as_view()),
    path("courses/", CourseView.as_view()),
    path("courses/<int:pk>/", CourseDetails.as_view()),
]
