"""N+1 regression guards.

The student list serializes ``course_name`` via ``source="course.name"``. The repository
must keep ``select_related("course")`` so the query count stays constant as rows grow.
If a future change drops the join (or adds an unprefetched related field), these fail.
"""

import pytest

from student_management.models import Course, Student
from student_management.repository.student_repository import StudentRepository
from student_management.v1.serializers.student_serializer import StudentSerializer

pytestmark = pytest.mark.django_db


def _serialize_all_students():
    return StudentSerializer(StudentRepository().all(), many=True).data


def _make_students(course, prefix, count):
    Student.objects.bulk_create(
        [
            Student(name=f"{prefix}{i}", age=20, email=f"{prefix}{i}@example.com", course=course)
            for i in range(count)
        ]
    )


def test_student_list_single_query(django_assert_num_queries):
    course = Course.objects.create(name="N+1")
    _make_students(course, "s", 10)

    # select_related("course") => exactly one SELECT regardless of row count.
    with django_assert_num_queries(1):
        data = _serialize_all_students()

    assert len(data) == 10
    assert data[0]["course_name"] == "N+1"


def test_student_list_query_count_is_constant(django_assert_num_queries):
    course = Course.objects.create(name="N+1")

    _make_students(course, "a", 3)
    with django_assert_num_queries(1):
        assert len(_serialize_all_students()) == 3

    _make_students(course, "b", 20)
    with django_assert_num_queries(1):
        assert len(_serialize_all_students()) == 23
