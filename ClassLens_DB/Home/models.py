from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from pgvector.django import HnswIndex, VectorField

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
    face_embedding = VectorField(dimensions=512, null=True, blank=True)
    notification_token = models.TextField(null=True, blank=True)
    class Meta:
        indexes = [
           HnswIndex(
                name='student_face_embedding_idx',
                fields=['face_embedding'],
                m=16,                 
                ef_construction=200,  
                opclasses=['vector_cosine_ops']
            ),
        ]
    def __str__(self):
        return f"{self.name} ({self.prn})"
    
class Subject(models.Model):
    code = models.TextField(unique=True, null=False,default="")
    name = models.TextField(null=False)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    
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
    program_name = models.TextField(null=False, default="")
    year = models.IntegerField(null=False)
    semester = models.IntegerField(null=False)
    name = models.CharField(max_length=20, null=False)

    class Meta:
        unique_together = ("department", "program_name", "year", "semester", "name")

    def __str__(self):
        return (
            f"{self.program_name} {self.year}th year {self.semester}th Sem "
            f"Division {self.name}"
        )
    
class StudentEnrollment(models.Model):
    student_prn = models.BigIntegerField(null=False)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    division = models.ForeignKey(Division, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ('student_prn', 'subject', 'division')

    def __str__(self):
        return f"{self.student_prn} enrolled in {self.subject} Division {self.division.name if self.division else 'N/A'}"
    
class TeacherSubject(models.Model):
    teacher_id = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('teacher_id', 'subject')

    def __str__(self):
        return f"{self.teacher_id.name} teaches {self.subject.name}"
    
class ClassSession(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    year = models.IntegerField(null=False)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    division = models.ForeignKey(Division, on_delete=models.SET_NULL, null=True, blank=True)
    class_datetime = models.DateTimeField(null=False)

    def __str__(self):
        return f"Class for {self.subject.name} at {self.class_datetime}"

class AttendancePhotos(models.Model):
    class_session = models.ForeignKey(ClassSession, on_delete=models.CASCADE,related_name='photos')
    photo = models.ImageField(upload_to='attendance_photos/')
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