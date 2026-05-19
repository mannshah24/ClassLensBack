from django.db import models


class APIEnrollment(models.Model):
	"""Staging table for enrollment data - matches New_schema exactly."""
	prn = models.BigIntegerField()
	subject_code = models.CharField(max_length=100)
	division = models.CharField(max_length=20)
	year = models.IntegerField()
	
	class Meta:
		unique_together = ('prn', 'subject_code', 'division', 'year')
	
	def __str__(self):
		return f"PRN {self.prn} - {self.subject_code} Div {self.division}"


class APIPaper(models.Model):
	"""Staging table for paper data - mirrors MSUIS API payloads. Matches New_schema exactly."""
	msuis_id = models.BigIntegerField(primary_key=True)
	paper_name = models.CharField(max_length=500)
	paper_code = models.CharField(max_length=100)
	raw_payload = models.JSONField()

	def __str__(self):
		return f"{self.paper_code} - {self.paper_name}"


class APIStudent(models.Model):
	"""Staging table for student data - mirrors MSUIS API payloads. Matches New_schema exactly."""
	prn = models.BigIntegerField(primary_key=True)
	email_id = models.CharField(max_length=255, null=True, blank=True)
	raw_payload = models.JSONField()
	full_name = models.CharField(max_length=255, null=True, blank=True)

	def __str__(self):
		return str(self.prn)
