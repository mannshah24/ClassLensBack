from io import BytesIO

from django.test import TestCase
from django.urls import reverse
from PIL import Image
from rest_framework.test import APIClient
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from Home.models import Department, Student
from .serializers import StudentSerializer

# Create your tests here.


class StudentFaceUpdateTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.department = Department.objects.create(name="Computer Science")
		self.student = Student.objects.create(
			prn=1001,
			name="Student One",
			email="student.one@example.com",
			year=2,
			department=self.department,
		)

	def _make_image_file(self, name="face.jpg", color=(255, 0, 0)):
		image = Image.new("RGB", (8, 8), color)
		buffer = BytesIO()
		image.save(buffer, format="JPEG")
		buffer.seek(0)
		return SimpleUploadedFile(name, buffer.read(), content_type="image/jpeg")

	@patch("Home.views.extract_face_embedding", return_value=[0.1] * 512)
	def test_register_student_accepts_photo_only_update(self, _mock_embedding):
		response = self.client.post(
			reverse("register_student"),
			{"prn": self.student.prn, "photo": self._make_image_file()},
			format="multipart",
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["message"], "Student face updated successfully")
		self.student.refresh_from_db()
		self.assertEqual(len(self.student.face_embedding), 512)
		self.assertAlmostEqual(self.student.face_embedding[0], 0.1)

	@patch("DatabaseAdminApp.serializers.extract_face_embedding", return_value=[0.2] * 512)
	def test_student_serializer_updates_face_from_photo(self, _mock_embedding):
		serializer = StudentSerializer(
			instance=self.student,
			data={"photo": self._make_image_file()},
			partial=True,
		)

		self.assertTrue(serializer.is_valid(), serializer.errors)
		updated_student = serializer.save()
		self.assertEqual(len(updated_student.face_embedding), 512)
		self.assertAlmostEqual(updated_student.face_embedding[0], 0.2)


from .models import APIEnrollment, APIStudent

class StagingToCoreSyncTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.department = Department.objects.create(name="Computer Science")

	def test_sync_staging_to_core_with_enrollment_succeeds(self):
		# Create staging APIStudent and APIEnrollment
		APIStudent.objects.create(
			prn=1001,
			full_name="Student One",
			email_id="student.one@example.com",
			raw_payload={"email": "student.one@example.com", "department_name": "Computer Science"}
		)
		APIEnrollment.objects.create(
			prn=1001,
			subject_code="CS101",
			division="A",
			year=2,
		)

		# Make request to sync endpoint
		response = self.client.post(reverse("sync-staging-to-core"))
		self.assertEqual(response.status_code, 200)
		self.assertIn("message", response.data)
		self.assertEqual(response.data["counts"]["core_students_upserted"], 1)
		self.assertEqual(response.data["counts"]["core_enrollments_upserted"], 1)

