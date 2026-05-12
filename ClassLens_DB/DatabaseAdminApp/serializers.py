# serializers.py

from rest_framework import serializers
from Home.models import (
    Department, Teacher, Student, Subject, SubjectFromDept,
    StudentEnrollment, TeacherSubject, AdminUser
)
from .models import (
    APIFaculty,
    APIStudent,
    APIPaper,
    APIStudentAcademicInformation,
    APIStudentPartTermPaperMap,
)

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'

class TeacherSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    
    class Meta:
        model = Teacher
        fields = ['id', 'name', 'email', 'password_hash', 'department', 'department_name', 'date_joined']
        extra_kwargs = {'password_hash': {'write_only': True}}

class StudentSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    
    class Meta:
        model = Student
        fields = ['id', 'prn', 'name', 'email', 'password_hash', 'year', 'department', 
                  'department_name', 'face_embedding', 'notification_token']
        extra_kwargs = {'password_hash': {'write_only': True}, 'face_embedding': {'write_only': True}}

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = '__all__'

class SubjectFromDeptSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    subject_details = SubjectSerializer(source='subject', many=True, read_only=True)
    subject_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Subject.objects.all(), source='subject', write_only=True
    )
    
    class Meta:
        model = SubjectFromDept
        fields = ['id', 'department', 'department_name', 'year', 'semester', 
                  'subject_details', 'subject_ids']

class StudentEnrollmentSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    subject_code = serializers.CharField(source='subject.code', read_only=True)
    
    class Meta:
        model = StudentEnrollment
        fields = ['id', 'student_prn', 'subject', 'subject_name', 'subject_code']

class TeacherSubjectSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher_id.name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    
    class Meta:
        model = TeacherSubject
        fields = ['id', 'teacher_id', 'teacher_name', 'subject', 'subject_name']

# class AdminUserSerializer(serializers.ModelSerializer):
#     password = serializers.CharField(write_only=True)
    
#     class Meta:
#         model = AdminUser
#         fields = ['id', 'username', 'password', 'created_at', 'is_active']
#         extra_kwargs = {'password': {'write_only': True}}
    
#     def create(self, validated_data):
#         password = validated_data.pop('password')
#         admin = AdminUser(**validated_data)
#         admin.set_password(password)
#         admin.save()
#         return admin



class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminUser
        fields = ['id', 'username', 'password', 'is_active']
        extra_kwargs = {
            'password': {'write_only': True} # Never send the password back in the response
        }

    def create(self, validated_data):
        user = AdminUser(
            username=validated_data['username'],
            is_active=validated_data.get('is_active', True)
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class APIFacultySerializer(serializers.ModelSerializer):
    class Meta:
        model = APIFaculty
        fields = "__all__"


class APIStudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = APIStudent
        fields = "__all__"


class APIPaperSerializer(serializers.ModelSerializer):
    class Meta:
        model = APIPaper
        fields = "__all__"


class APIStudentAcademicInformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = APIStudentAcademicInformation
        fields = "__all__"


class APIStudentPartTermPaperMapSerializer(serializers.ModelSerializer):
    class Meta:
        model = APIStudentPartTermPaperMap
        fields = "__all__"


class DivisionSerializer(serializers.ModelSerializer):
    class Meta:
        from Home.models import Division
        model = Division
        fields = ['id', 'department', 'program_name', 'year', 'semester', 'name']