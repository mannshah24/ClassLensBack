from django.db import models


class APIEnrollment(models.Model):
	"""Simplified mirror of enrollment data from MSUIS API - attendance-only focus."""
	prn = models.BigIntegerField(db_index=True)
	subject_code = models.CharField(max_length=100)
	department_name = models.CharField(max_length=200)
	program_name = models.CharField(max_length=200)
	year = models.IntegerField()
	semester = models.IntegerField()
	division = models.CharField(max_length=20)  # A, B, C, etc.
	raw_payload = models.JSONField(default=dict)
	synced_at = models.DateTimeField(auto_now=True)
	
	class Meta:
		unique_together = ('prn', 'subject_code', 'division', 'semester')
	
	def __str__(self):
		return f"PRN {self.prn} - {self.subject_code} Div {self.division}"


class APIFaculty(models.Model):
	"""Mirror of faculty data received from MSUIS API."""
	msuis_id = models.BigIntegerField(primary_key=True)
	name = models.TextField(null=True, blank=True)
	is_active = models.BooleanField(null=True, blank=True)
	is_deleted = models.BooleanField(null=True, blank=True)
	raw_payload = models.JSONField(default=dict)
	synced_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"{self.msuis_id} - {self.name or 'Faculty'}"


class APIStudent(models.Model):
	"""Mirror of MstStudent API payloads."""
	prn = models.BigIntegerField(primary_key=True)
	first_name = models.CharField(max_length=100, null=True, blank=True)
	middle_name = models.CharField(max_length=100, null=True, blank=True)
	last_name = models.CharField(max_length=100, null=True, blank=True)
	email_id = models.CharField(max_length=150, null=True, blank=True)
	mobile_no = models.CharField(max_length=50, null=True, blank=True)
	faculty_id = models.BigIntegerField(null=True, blank=True)
	programme_name = models.CharField(max_length=200, null=True, blank=True)
	admission_year = models.IntegerField(null=True, blank=True)
	passing_year = models.IntegerField(null=True, blank=True)
	raw_payload = models.JSONField(default=dict)
	synced_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return str(self.prn)


class APIPaper(models.Model):
	"""Mirror of MstPaper API payloads."""
	msuis_id = models.BigIntegerField(primary_key=True)
	subject_id = models.BigIntegerField(null=True, blank=True)
	paper_name = models.CharField(max_length=1000)
	paper_code = models.CharField(max_length=100)
	is_credit = models.BooleanField(null=True, blank=True)
	max_marks = models.IntegerField(null=True, blank=True)
	min_marks = models.IntegerField(null=True, blank=True)
	credits = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
	is_active = models.BooleanField(null=True, blank=True)
	is_deleted = models.BooleanField(null=True, blank=True)
	raw_payload = models.JSONField(default=dict)
	synced_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"{self.paper_code} - {self.paper_name}"


class APIStudentAcademicInformation(models.Model):
	"""Mirror of IncStudentAcademicInformation API payloads."""
	msuis_id = models.BigIntegerField(primary_key=True)
	prn = models.BigIntegerField(db_index=True)
	student_admission_id = models.BigIntegerField(null=True, blank=True)
	programme_instance_part_term_id = models.BigIntegerField(null=True, blank=True)
	programme_id = models.BigIntegerField(null=True, blank=True)
	specialisation_id = models.BigIntegerField(null=True, blank=True)
	academic_year_id = models.BigIntegerField(null=True, blank=True)
	institute_id = models.BigIntegerField(null=True, blank=True)
	faculty_id = models.BigIntegerField(null=True, blank=True)
	part_term_status = models.CharField(max_length=100, null=True, blank=True)
	raw_payload = models.JSONField(default=dict)
	synced_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"{self.msuis_id} - {self.prn}"


class APIStudentPartTermPaperMap(models.Model):
	"""Mirror of IncStudentPartTermPaperMap API payloads. (Legacy - use APIEnrollment instead)"""
	msuis_id = models.BigIntegerField(primary_key=True)
	prn = models.BigIntegerField(null=True, blank=True, db_index=True)
	student_academic_information_id = models.BigIntegerField(null=True, blank=True)
	programme_instance_part_term_id = models.BigIntegerField(null=True, blank=True)
	paper_id = models.BigIntegerField(null=True, blank=True)
	mst_paper_id = models.BigIntegerField(null=True, blank=True)
	obtained_marks = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
	obtained_grade = models.CharField(max_length=10, null=True, blank=True)
	paper_status = models.CharField(max_length=100, null=True, blank=True)
	part_term_status = models.CharField(max_length=100, null=True, blank=True)
	division = models.CharField(max_length=20, null=True, blank=True)
	raw_payload = models.JSONField(default=dict)
	synced_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"{self.msuis_id} - {self.prn}"
