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


from django.core.cache import cache
from unittest.mock import patch

class PerformanceOptimizationTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.department = Department.objects.create(name="Electronics")
		self.teacher = Teacher.objects.create(
			name="Teacher E",
			email="teacher.e@example.com",
			department=self.department
		)
		self.subject = Subject.objects.create(
			code="EL101",
			name="Basic Electronics"
		)
		self.division = Division.objects.create(
			department=self.department,
			year=1,
			name="A"
		)
		self.teacher_subject = TeacherSubject.objects.create(
			teacher_id=self.teacher,
			subject=self.subject,
			division=self.division
		)
		self.student = Student.objects.create(
			prn=2001,
			name="Student E",
			email="student.e@example.com",
			year=1,
			department=self.department,
			division=self.division
		)
		StudentEnrollment.objects.create(student_prn=self.student.prn, subject=self.subject)

	def test_teacher_subjects_optimized(self):
		response = self.client.get(reverse("teacher_subjects"), {"teacher_id": self.teacher.id})
		self.assertEqual(response.status_code, 200)
		self.assertIn("subjects", response.data)
		self.assertEqual(len(response.data["subjects"]), 1)
		self.assertEqual(response.data["subjects"][0]["strength"], 1)

	def test_teacher_profile_optimized(self):
		response = self.client.get(reverse("teacher_profile", kwargs={"teacher_id": self.teacher.id}))
		self.assertEqual(response.status_code, 200)
		self.assertIn("teacher_profile", response.data)
		self.assertEqual(response.data["teacher_profile"]["total_subjects"], 1)
		self.assertEqual(response.data["teacher_profile"]["total_students"], 1)

	def test_get_student_dashboard_optimized(self):
		response = self.client.post(reverse("get_student_dashboard"), {"student_id": self.student.id}, format="json")
		self.assertEqual(response.status_code, 200)
		self.assertIn("subjects", response.data)
		self.assertEqual(len(response.data["subjects"]), 1)
		self.assertEqual(response.data["student_name"], "Student E")

	@patch("Home.views.send_otp_email_task.delay")
	def test_send_otp_cooldown_jitter(self, mock_send_email_delay):
		cache.clear()
		# First request should succeed
		response = self.client.post(reverse("send_otp"), {"email": self.student.email}, format="json")
		self.assertEqual(response.status_code, 200)
		
		# Second request should be rate-limited with 429
		response2 = self.client.post(reverse("send_otp"), {"email": self.student.email}, format="json")
		self.assertEqual(response2.status_code, 429)
		self.assertIn("cooldown_seconds", response2.data)
		self.assertTrue(60 <= response2.data["cooldown_seconds"] <= 180)

	@patch("Home.tasks.process_student_face_embedding.delay")
	def test_instant_registration(self, mock_delay):
		# We delete student password_hash to allow registration
		self.student.password_hash = None
		self.student.save()
		
		# Create a dummy image file
		import io
		from PIL import Image
		file = io.BytesIO()
		image = Image.new('RGB', (100, 100))
		image.save(file, 'jpeg')
		file.name = 'test.jpg'
		file.seek(0)
		
		response = self.client.post(
			reverse("register_student"),
			{"prn": self.student.prn, "password": "newpassword", "photo": file},
			format="multipart"
		)
		self.assertEqual(response.status_code, 200)
		self.assertIn("Registration successful", response.data["message"])
		
		# Verify password is saved synchronously
		self.student.refresh_from_db()
		self.assertIsNotNone(self.student.password_hash)


class ForgotPasswordTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.department = Department.objects.create(name="Computer Science & Engineering")
		
		# Create student with face embedding
		self.student = Student.objects.create(
			prn=1111222233,
			name="Reset Student",
			email="reset.student@example.com",
			year=3,
			department=self.department,
			password_hash="somehashvalue",
			face_embedding=[0.1] * 512
		)
		
		# Create teacher
		self.teacher = Teacher.objects.create(
			name="Reset Teacher",
			email="reset.teacher@msubaroda.ac.in",
			department=self.department,
			password_hash="teacherhash"
		)

	@patch("Home.views.send_otp_email_task.delay")
	def test_forgot_password_student_flow(self, mock_send_email_delay):
		cache.clear()
		
		# 1. Send OTP for student using PRN
		response = self.client.post(
			reverse("forgot_password_send_otp"),
			{"prn": self.student.prn},
			format="json"
		)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["email"], self.student.email)
		mock_send_email_delay.assert_called_once()
		
		# Retrieve the generated OTP from cache
		otp = cache.get(self.student.email)
		self.assertIsNotNone(otp)
		
		# 2. Verify OTP for student
		response = self.client.post(
			reverse("forgot_password_verify_otp"),
			{"prn": self.student.prn, "otp": otp},
			format="json"
		)
		self.assertEqual(response.status_code, 200)
		
		# Assert password_hash is cleared, but face embedding remains intact
		self.student.refresh_from_db()
		self.assertIsNone(self.student.password_hash)
		import numpy as np
		self.assertTrue(np.allclose(self.student.face_embedding, [0.1] * 512))

	@patch("Home.views.send_otp_email_task.delay")
	def test_forgot_password_teacher_flow(self, mock_send_email_delay):
		cache.clear()
		
		# 1. Send OTP for teacher using Email
		response = self.client.post(
			reverse("forgot_password_send_otp"),
			{"email": self.teacher.email},
			format="json"
		)
		self.assertEqual(response.status_code, 200)
		mock_send_email_delay.assert_called_once()
		
		otp = cache.get(self.teacher.email)
		self.assertIsNotNone(otp)
		
		# 2. Verify OTP with incorrect code (should fail)
		response = self.client.post(
			reverse("forgot_password_verify_otp"),
			{"email": self.teacher.email, "otp": 9999},
			format="json"
		)
		self.assertEqual(response.status_code, 400)
		self.assertIsNotNone(self.teacher.password_hash)
		
		# 3. Verify OTP with correct code (should succeed)
		response = self.client.post(
			reverse("forgot_password_verify_otp"),
			{"email": self.teacher.email, "otp": otp},
			format="json"
		)
		self.assertEqual(response.status_code, 200)
		
		# Assert password_hash is cleared
		self.teacher.refresh_from_db()
		self.assertIsNone(self.teacher.password_hash)

	def test_forgot_password_unregistered_rejection(self):
		# Set student's password_hash to None
		self.student.password_hash = None
		self.student.save()
		
		response = self.client.post(
			reverse("forgot_password_send_otp"),
			{"prn": self.student.prn},
			format="json"
		)
		self.assertEqual(response.status_code, 400)
		self.assertIn("Account is not registered", response.data["detail"])


