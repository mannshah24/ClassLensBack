from io import BytesIO

from django.test import TestCase
from django.urls import reverse
from PIL import Image
from rest_framework.test import APIClient
from unittest.mock import patch

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
		buffer.name = name
		return buffer

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
