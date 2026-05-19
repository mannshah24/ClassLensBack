# Script to add teacher, subject and department data
# Run this with: python manage.py shell < add_teacher_data.py

from Home.models import Department, Teacher, Subject, TeacherSubject

# Create or get the Department
department, created = Department.objects.get_or_create(
    name="Computer Science and Engineering"
)
if created:
    print(f"✓ Created Department: {department.name}")
else:
    print(f"✓ Department already exists: {department.name}")

# Create or get the Subject
subject, created = Subject.objects.get_or_create(
    name="Design and Analysis of Algorithms-CSE",
    defaults={'code': 'DAA-CSE'}  # You can change this code if needed
)
if created:
    print(f"✓ Created Subject: {subject.name}")
else:
    print(f"✓ Subject already exists: {subject.name}")

# Create or get the Teacher
teacher, created = Teacher.objects.get_or_create(
    email="viral.kapadia-cse@msubaroda.ac.in",
    defaults={
        'name': "Viral Kapadia",
        'department': department
    }
)
if created:
    print(f"✓ Created Teacher: {teacher.name}")
else:
    print(f"✓ Teacher already exists: {teacher.name}")
    # Update department if teacher already exists
    if teacher.department != department:
        teacher.department = department
        teacher.save()
        print(f"  Updated teacher's department")

# Link Teacher to Subject
teacher_subject, created = TeacherSubject.objects.get_or_create(
    teacher_id=teacher,
    subject=subject
)
if created:
    print(f"✓ Created TeacherSubject link: {teacher.name} teaches {subject.name}")
else:
    print(f"✓ TeacherSubject link already exists")

print("\n✅ All data added successfully!")
