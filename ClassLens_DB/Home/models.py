from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from pgvector.django import VectorField

class Department(models.Model):
    name = models.TextField(unique=True, null=False)
    def __str__(self):
        return self.name

class Teacher(models.Model):
    name = models.TextField(null=False)
    email = models.EmailField(unique=True, null=False)
    password_hash = models.TextField(null=True)
    department = models.ForeignKey(
        Department, 
        on_delete=models.CASCADE, 
    )
    date_joined=models.DateField(null=True,auto_now_add=True)
    def __str__(self):
        return self.name
    
class Student(models.Model):
    prn = models.BigIntegerField(unique=True, null=False)
    name = models.TextField(null=False)
    email = models.EmailField(unique=True, null=False)
    password_hash = models.TextField(null=True,blank=True)
    year = models.IntegerField(null=False)
    department = models.ForeignKey(
        Department, 
        on_delete=models.CASCADE, 
    )
    division = models.ForeignKey(
        'Division',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    face_embedding = VectorField(dimensions=512, null=True, blank=True)
    notification_token = models.TextField(null=True, blank=True)
    def __str__(self):
        return f"{self.name} ({self.prn})"
    
class Subject(models.Model):
    code = models.TextField(unique=True, null=False,default="")
    name = models.TextField(null=False)
    
    def __str__(self):
        return f"{self.name}"

class SubjectFromDept(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    year = models.IntegerField(null=False)
    subject = models.ManyToManyField(Subject)
    semester=models.IntegerField(null=False)    
    
    class Meta:
        unique_together = ('department', 'year','semester')

    def __str__(self):
        return f"{self.department} - {self.year}"


class Division(models.Model):
    """
    Local teaching division metadata, e.g. BE CSE 4th year Sem 8 Division A.
    """
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    year = models.IntegerField(null=False)
    name = models.CharField(max_length=20, null=False)

    class Meta:
        unique_together = ("department", "year", "name")

    def __str__(self):
        return (
            f"{self.year}th year Division {self.name}"
        )
    
class StudentEnrollment(models.Model):
    student_prn = models.BigIntegerField(null=False)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('student_prn', 'subject')

    def __str__(self):
        return f"{self.student_prn} enrolled in {self.subject}"
    
class TeacherSubject(models.Model):
    teacher_id = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    division = models.ForeignKey(Division, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ('teacher_id', 'subject', 'division')

    def __str__(self):
        division_name = self.division.name if self.division else 'All Divisions'
        return f"{self.teacher_id.name} teaches {self.subject.name} ({division_name})"
    
class ClassSession(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    year = models.IntegerField(null=False)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    class_datetime = models.DateTimeField(null=False)

    def __str__(self):
        return f"Class for {self.subject.name} at {self.class_datetime}"

class AttendancePhotos(models.Model):
    class_session = models.ForeignKey(ClassSession, on_delete=models.CASCADE,related_name='photos')
    photo = models.ImageField(upload_to='attendance_photos/')
    detected_photo = models.ImageField(upload_to='detected_photos/', null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

class AttendanceRecord(models.Model):
    class_session = models.ForeignKey(ClassSession, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    status = models.BooleanField()
    marked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('class_session', 'student')

    def __str__(self):
        return f"{self.student.name} - {self.status} for class {self.class_session.id}"
    
class StudentAttendancePercentage(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject=models.ForeignKey(Subject,on_delete=models.CASCADE)
    present_count=models.IntegerField(null=False,default=0)
    attendancePercentage = models.FloatField(null=False,default=0.0)

class AdminUser(models.Model):
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)  
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_anonymous(self):
        return False
    
    
    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.username


class Holiday(models.Model):
    date = models.DateField(unique=True, help_text="The date of the holiday.")
    name = models.CharField(max_length=255, help_text="e.g., Diwali, Independence Day, Heavy Rain")
    is_working_day = models.BooleanField(default=False, help_text="Check if attendance is still required despite being a 'holiday'.")

    def __str__(self):
        return f"{self.date} - {self.name}"


class TimetableTemplate(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    day_of_week = models.IntegerField(help_text="0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 4=Friday, 5=Saturday, 6=Sunday")
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, blank=True)
    program = models.CharField(max_length=100, null=True, blank=True)
    division = models.ForeignKey(Division, on_delete=models.CASCADE)
    year = models.IntegerField(null=True, blank=True)
    semester = models.IntegerField(null=True, blank=True)
    default_teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.subject.name} - Day {self.day_of_week} ({self.division.name})"


class DailySession(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    date = models.DateField()
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, blank=True)
    program = models.CharField(max_length=100, null=True, blank=True)
    division = models.ForeignKey(Division, on_delete=models.CASCADE)
    year = models.IntegerField(null=True, blank=True)
    semester = models.IntegerField(null=True, blank=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    is_cancelled = models.BooleanField(default=False)
    proxy_teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name='proxy_daily_sessions')

    def __str__(self):
        return f"{self.date} - {self.subject.name} ({self.division.name})"