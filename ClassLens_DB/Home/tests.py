from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from .models import (
	AttendanceRecord,
	ClassSession,
	Department,
	Division,
	Student,
	StudentEnrollment,
	Subject,
	Teacher,
	TeacherSubject,
)


class TeacherClassSessionsEndpointTests(TestCase):
	def setUp(self):
		self.client = APIClient()

		self.department = Department.objects.create(name="Computer Science")
		self.teacher = Teacher.objects.create(
			name="Teacher One",
			email="teacher.one@example.com",
			department=self.department,
		)
		self.subject = Subject.objects.create(
			code="CS101",
			name="Object Oriented Programming with Java-CSE",
			department=self.department,
		)
		self.division = Division.objects.create(
			department=self.department,
			year=2,
			name="SFI",
		)
		self.teacher_subject = TeacherSubject.objects.create(
			teacher_id=self.teacher,
			subject=self.subject,
			division=self.division,
		)

		self.student_one = Student.objects.create(
			prn=1001,
			name="Student One",
			email="student.one@example.com",
			year=2,
			department=self.department,
			division=self.division,
		)
		self.student_two = Student.objects.create(
			prn=1002,
			name="Student Two",
			email="student.two@example.com",
			year=2,
			department=self.department,
			division=self.division,
		)

		StudentEnrollment.objects.create(student_prn=self.student_one.prn, subject=self.subject)
		StudentEnrollment.objects.create(student_prn=self.student_two.prn, subject=self.subject)

		self.class_session = ClassSession.objects.create(
			department=self.department,
			year=2,
			subject=self.subject,
			teacher=self.teacher,
			class_datetime=timezone.now(),
		)

		AttendanceRecord.objects.create(
			class_session=self.class_session,
			student=self.student_one,
			status=True,
		)
		AttendanceRecord.objects.create(
			class_session=self.class_session,
			student=self.student_two,
			status=False,
		)

	def test_get_teacher_class_sessions_returns_expected_payload(self):
		response = self.client.get(
			reverse("teacher_class_sessions"),
			{"teacher_id": self.teacher.id, "limit": 5},
		)

		self.assertEqual(response.status_code, 200)
		self.assertIn("class_sessions", response.data)
		self.assertEqual(len(response.data["class_sessions"]), 1)

		session_data = response.data["class_sessions"][0]
		self.assertEqual(session_data["class_session_id"], self.class_session.id)
		self.assertEqual(session_data["subject_name"], self.subject.name)
		self.assertEqual(session_data["division_name"], self.division.name)
		self.assertEqual(session_data["present_count"], 1)
		self.assertEqual(session_data["absent_count"], 1)
		self.assertEqual(session_data["total_count"], 2)

	def test_post_teacher_class_sessions_fallback_works(self):
		response = self.client.post(
			reverse("get_teacher_class_sessions"),
			{"teacher_id": self.teacher.id, "limit": 5},
			format="json",
		)

		self.assertEqual(response.status_code, 200)
		self.assertIn("class_sessions", response.data)
