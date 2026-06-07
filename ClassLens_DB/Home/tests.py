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
	Holiday,
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


class HolidayAPIEndpointTests(TestCase):
	def setUp(self):
		self.client = APIClient()

	def test_get_daily_schedule_no_holiday(self):
		# With no holiday on the date, should return is_holiday: False
		response = self.client.get(
			reverse("get_daily_schedule"),
			{"date": "2026-06-07"},
		)
		self.assertEqual(response.status_code, 200)
		self.assertFalse(response.data["is_holiday"])
		self.assertEqual(len(response.data["sessions"]), 0)

	def test_get_daily_schedule_alias_works(self):
		# Verify that the schedule/daily route functions identically
		response = self.client.get(
			reverse("get_daily_schedule_alias"),
			{"date": "2026-06-07"},
		)
		self.assertEqual(response.status_code, 200)
		self.assertFalse(response.data["is_holiday"])
		self.assertEqual(len(response.data["sessions"]), 0)

	def test_get_daily_schedule_with_holiday(self):
		# Create a non-working holiday
		Holiday.objects.create(
			date="2026-06-07",
			name="Test Holiday",
			is_working_day=False,
		)
		response = self.client.get(
			reverse("get_daily_schedule"),
			{"date": "2026-06-07"},
		)
		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.data["is_holiday"])
		self.assertEqual(response.data["holiday_name"], "Test Holiday")
		self.assertEqual(len(response.data["sessions"]), 0)

	def test_get_daily_schedule_with_working_holiday(self):
		# Create a working holiday
		Holiday.objects.create(
			date="2026-06-07",
			name="Working Holiday",
			is_working_day=True,
		)
		response = self.client.get(
			reverse("get_daily_schedule"),
			{"date": "2026-06-07"},
		)
		self.assertEqual(response.status_code, 200)
		self.assertFalse(response.data["is_holiday"])

	def test_list_holidays(self):
		Holiday.objects.create(date="2026-06-07", name="Holiday A", is_working_day=False)
		Holiday.objects.create(date="2026-06-08", name="Holiday B", is_working_day=True)
		
		response = self.client.get(reverse("list_holidays"))
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data), 2)
		self.assertEqual(response.data[0]["name"], "Holiday A")
		self.assertEqual(response.data[1]["name"], "Holiday B")

	def test_declare_holiday_success(self):
		payload = {
			"date": "2026-06-09",
			"name": "New Emergency Holiday",
			"is_working_day": False
		}
		response = self.client.post(reverse("declare_holiday"), payload, format="json")
		self.assertEqual(response.status_code, 201)
		self.assertEqual(response.data["name"], "New Emergency Holiday")
		self.assertTrue(Holiday.objects.filter(date="2026-06-09").exists())

	def test_declare_holiday_duplicate(self):
		Holiday.objects.create(date="2026-06-09", name="Existing Holiday")
		payload = {
			"date": "2026-06-09",
			"name": "Duplicate Holiday",
			"is_working_day": False
		}
		response = self.client.post(reverse("declare_holiday"), payload, format="json")
		self.assertEqual(response.status_code, 400)
		self.assertIn("error", response.data)

	def test_declare_holiday_invalid_date(self):
		payload = {
			"date": "invalid-date",
			"name": "Invalid Date Holiday",
			"is_working_day": False
		}
		response = self.client.post(reverse("declare_holiday"), payload, format="json")
		self.assertEqual(response.status_code, 400)

	def test_delete_holiday(self):
		h = Holiday.objects.create(date="2026-06-10", name="Temp Holiday")
		response = self.client.delete(reverse("delete_holiday", kwargs={"pk": h.pk}))
		self.assertEqual(response.status_code, 200)
		self.assertFalse(Holiday.objects.filter(pk=h.pk).exists())

