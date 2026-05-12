#!/usr/bin/env python
"""Test the sync_msuis_payload endpoint via Django shell."""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ClassLens_DB.settings')
sys.path.insert(0, 'ClassLens_DB')
django.setup()

from django.test import RequestFactory
import json
from Home.models import AdminUser, Department, Student, Subject
from DatabaseAdminApp.views import sync_msuis_payload

# Use existing admin or create one
admin = AdminUser.objects.first()
if not admin:
    admin = AdminUser(username='admin', is_active=True)
    admin.set_password('admin')
    admin.save()

print(f"Using admin: {admin.username} (id={admin.id})")
print(f"Departments before sync: {Department.objects.count()}")
print(f"Students before sync: {Student.objects.count()}")

# Build mock request with payload
rf = RequestFactory()
payload = {
    'faculties': [{'Id': 100, 'FacultyName': 'Test Faculty', 'IsActive': 1}],
    'students': [{'PRN': 2025001, 'FirstName': 'John', 'MiddleName': '', 'LastName': 'Doe', 'EmailId': 'john@example.com', 'FacultyId': 100, 'Year': 2}],
    'papers': [{'Id': 500, 'PaperCode': 'TEST101', 'PaperName': 'Test Subject', 'SubjectId': 500}],
    'student_academic_information': [],
    'student_part_term_paper_maps': [{'Id': 1000, 'PRN': 2025001, 'PaperId': 500, 'Division': 'A', 'Semester': 3}],
    'apply_to_core': True
}

req = rf.post('/api/admin/sync/msuis/', data=json.dumps(payload), content_type='application/json')
req.user = admin

# Call the view
resp = sync_msuis_payload(req)
print(f"\nResponse status: {resp.status_code}")
print(f"Response data: {json.dumps(resp.data, indent=2)}")

print(f"\nDepartments after sync: {Department.objects.count()}")
print(f"Students after sync: {Student.objects.count()}")
print(f"Subjects after sync: {Subject.objects.count()}")
print("\n✓ Sync endpoint test completed successfully!")
