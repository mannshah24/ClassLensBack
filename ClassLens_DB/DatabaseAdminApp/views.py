from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import make_password
from django.http import HttpResponse
try:
    import pandas as pd
except Exception:
    pd = None
import io
from .pagination import StudentPagination
from Home.models import (
    Department, Teacher, Student, Subject, SubjectFromDept,
    StudentEnrollment, TeacherSubject, AdminUser, StudentAttendancePercentage, Division
)
from .models import (
    APIFaculty,
    APIStudent,
    APIPaper,
    APIStudentAcademicInformation,
    APIStudentPartTermPaperMap,
)
from .serializers import (
    DepartmentSerializer, TeacherSerializer, StudentSerializer,
    SubjectSerializer, SubjectFromDeptSerializer, StudentEnrollmentSerializer,
    TeacherSubjectSerializer, AdminUserSerializer,
    APIFacultySerializer, APIStudentSerializer, APIPaperSerializer,
    APIStudentAcademicInformationSerializer, APIStudentPartTermPaperMapSerializer,
    DivisionSerializer,
)
from django.db import transaction

from rest_framework.permissions import BasePermission

class IsSuperUser(BasePermission):
    """
    Allow access only to superusers.
    """

    def has_permission(self, request, view):
      return bool(
          request.user
          and request.user.is_authenticated
          and getattr(request.user, "is_superuser", False)
      )

@api_view(['POST'])
@permission_classes([AllowAny])
def admin_login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    
    try:
        admin = AdminUser.objects.get(username=username, is_active=True)
        if admin.check_password(password):
            refresh = RefreshToken.for_user(admin)
            refresh['username'] = admin.username
            refresh['user_id'] = admin.id 
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'username': admin.username
            })
        else:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    except AdminUser.DoesNotExist:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

class AdminUserViewSet(viewsets.ModelViewSet):
  
    queryset = AdminUser.objects.all().order_by("id")
    serializer_class = AdminUserSerializer
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.id == request.user.id:
            return Response(
                {"detail": "You cannot delete your own admin account."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_dashboard_stats(request):
    print(f"Stats Request User: {request.user}") 
    print(f"Is Authenticated: {request.user.is_authenticated}")
    
    try:
        stats = {
            "teachers_count": Teacher.objects.count(),
            "students_count": Student.objects.count(),
            "subjects_count": Subject.objects.count(),
        }
        return Response(stats, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"error": "Failed to fetch stats", "details": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]

class TeacherViewSet(viewsets.ModelViewSet):
    queryset = Teacher.objects.all().select_related('department')
    serializer_class = TeacherSerializer
   
    
    @action(detail=False, methods=['get'])
    def download_template(self, request):
        """Download Excel template for bulk teacher upload"""
        data = {
            'name': ['John Doe', 'Jane Smith'],
            'email': ['john@example.com', 'jane@example.com'],
            'department_name': ['Computer Science', 'Electronics']
        }
        df = pd.DataFrame(data)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Teachers')
        output.seek(0)
        
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=teachers_template.xlsx'
        return response
    
    @action(detail=False, methods=['post'])
    def bulk_upload(self, request):
        """
        Bulk upload teachers from CSV/Excel
        Expected columns: name, email, password, department_name
        """
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.name.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file)
            else:
                return Response({'error': 'Invalid file format. Use CSV or Excel'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            created_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    department = Department.objects.get(name=row['department_name'])
                    teacher_data = {
                        'name': row['name'],
                        'email': row['email'],
                        'password_hash': make_password(row.get('password', 'default123')),
                        'department': department
                    }
                    Teacher.objects.create(**teacher_data)
                    created_count += 1
                except Exception as e:
                    errors.append(f"Row {index + 1}: {str(e)}")
            
            return Response({
                'message': f'Successfully created {created_count} teachers',
                'errors': errors
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all().select_related('department')
    serializer_class = StudentSerializer
    pagination_class = StudentPagination 
    
    @action(detail=False, methods=['get'])
    def download_template(self, request):
        """Download Excel template for bulk student upload"""
        data = {
            'prn': [2021001, 2021002],
            'name': ['Alice Johnson', 'Bob Williams'],
            'email': ['alice@example.com', 'bob@example.com'],
            'year': [2, 3],
            'department_name': ['Computer Science', 'Electronics']
        }
        df = pd.DataFrame(data)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Students')
        output.seek(0)
        
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=students_template.xlsx'
        return response
    
    @action(detail=False, methods=['post'])
    def bulk_upload(self, request):
        """
        Bulk upload students from CSV/Excel
        Expected columns: prn, name, email, password, year, department_name
        """
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.name.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file)
            else:
                return Response({'error': 'Invalid file format'}, status=status.HTTP_400_BAD_REQUEST)
            
            created_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    department = Department.objects.get(name=row['department_name'])
                    student_data = {
                        'prn': int(row['prn']),
                        'name': row['name'],
                        'email': row['email'],
                        'password_hash': make_password(row.get('password', 'student123')),
                        'year': int(row['year']),
                        'department': department
                    }
                    Student.objects.create(**student_data)
                    created_count += 1
                except Exception as e:
                    errors.append(f"Row {index + 1}: {str(e)}")
            
            return Response({
                'message': f'Successfully created {created_count} students',
                'errors': errors
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    
    @action(detail=False, methods=['get'])
    def download_template(self, request):
        """Download Excel template for bulk subject upload"""
        data = {
            'code': ['CS101', 'CS102', 'EE201'],
            'name': ['Data Structures', 'Algorithms', 'Digital Electronics']
        }
        df = pd.DataFrame(data)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Subjects')
        output.seek(0)
        
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=subjects_template.xlsx'
        return response
    
    @action(detail=False, methods=['post'])
    def bulk_upload(self, request):
        """
        Bulk upload subjects from CSV/Excel
        Expected columns: code, name
        """
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.name.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file)
            else:
                return Response({'error': 'Invalid file format'}, status=status.HTTP_400_BAD_REQUEST)
            
            created_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    Subject.objects.create(
                        code=row['code'],
                        name=row['name']
                    )
                    created_count += 1
                except Exception as e:
                    errors.append(f"Row {index + 1}: {str(e)}")
            
            return Response({
                'message': f'Successfully created {created_count} subjects',
                'errors': errors
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class SubjectFromDeptViewSet(viewsets.ModelViewSet):
    queryset = SubjectFromDept.objects.all().select_related('department').prefetch_related('subject')
    serializer_class = SubjectFromDeptSerializer
    
    @action(detail=False, methods=['get'])
    def download_template(self, request):
        """Download Excel template for bulk subject-dept mapping upload"""
        data = {
            'department_name': ['Computer Science', 'Electronics'],
            'year': [2, 2],
            'semester': [3, 4],
            'subject_codes': ['CS101,CS102,CS103', 'EE201,EE202']
        }
        df = pd.DataFrame(data)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='SubjectFromDept')
            # Add instructions sheet
            instructions = pd.DataFrame({
                'Instructions': [
                    '1. department_name must match existing department',
                    '2. year should be 1, 2, 3, or 4',
                    '3. semester should be 1-8',
                    '4. subject_codes should be comma-separated (e.g., CS101,CS102)',
                    '5. All subject codes must exist in database'
                ]
            })
            instructions.to_excel(writer, index=False, sheet_name='Instructions')
        output.seek(0)
        
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=subject_dept_template.xlsx'
        return response
    
    @action(detail=False, methods=['post'])
    def bulk_upload(self, request):
        """
        Bulk upload subject-dept mappings from CSV/Excel
        Expected columns: department_name, year, semester, subject_codes (comma-separated)
        """
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.name.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file)
            else:
                return Response({'error': 'Invalid file format'}, status=status.HTTP_400_BAD_REQUEST)
            
            created_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    department = Department.objects.get(name=row['department_name'])
                    subject_codes = [code.strip() for code in str(row['subject_codes']).split(',')]
                    subjects = Subject.objects.filter(code__in=subject_codes)
                    
                    subject_dept, created = SubjectFromDept.objects.get_or_create(
                        department=department,
                        year=int(row['year']),
                        semester=int(row['semester'])
                    )
                    subject_dept.subject.set(subjects)
                    created_count += 1
                except Exception as e:
                    errors.append(f"Row {index + 1}: {str(e)}")
            
            return Response({
                'message': f'Successfully processed {created_count} records',
                'errors': errors
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class StudentEnrollmentViewSet(viewsets.ModelViewSet):
    queryset = StudentEnrollment.objects.all().select_related('subject')
    serializer_class = StudentEnrollmentSerializer
    
    @action(detail=False, methods=['get'])
    def download_template(self, request):
        """Download Excel template for bulk student enrollment upload"""
        data = {
            'student_prn': [2021001, 2021001, 2021002],
            'subject_code': ['CS101', 'CS102', 'EE201']
        }
        df = pd.DataFrame(data)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Enrollments')
            # Add instructions
            instructions = pd.DataFrame({
                'Instructions': [
                    '1. student_prn must exist in students table',
                    '2. subject_code must exist in subjects table',
                    '3. Each student-subject combination must be unique',
                    '4. One student can enroll in multiple subjects'
                ]
            })
            instructions.to_excel(writer, index=False, sheet_name='Instructions')
        output.seek(0)
        
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=enrollments_template.xlsx'
        return response
    
    @action(detail=False, methods=['post'])
    def bulk_upload(self, request):
        """
        Bulk upload student enrollments from CSV/Excel
        Expected columns: student_prn, subject_code
        """
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.name.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file)
            else:
                return Response({'error': 'Invalid file format'}, status=status.HTTP_400_BAD_REQUEST)
            
            created_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    subject = Subject.objects.get(code=row['subject_code'])
                    StudentEnrollment.objects.create(
                        student_prn=int(row['student_prn']),
                        subject=subject
                    )
                    StudentAttendancePercentage.objects.create(
                        student=Student.objects.get(prn=int(row['student_prn'])),
                        subject=subject,
                        present_count=0,
                        attendancePercentage=0.0
                    )
                    created_count += 1
                except Exception as e:
                    errors.append(f"Row {index + 1}: {str(e)}")
            
            return Response({
                'message': f'Successfully created {created_count} enrollments',
                'errors': errors
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class APIFacultyViewSet(viewsets.ModelViewSet):
    queryset = APIFaculty.objects.all().order_by("msuis_id")
    serializer_class = APIFacultySerializer
    permission_classes = [IsAuthenticated]


class APIStudentViewSet(viewsets.ModelViewSet):
    queryset = APIStudent.objects.all().order_by("prn")
    serializer_class = APIStudentSerializer
    permission_classes = [IsAuthenticated]


class APIPaperViewSet(viewsets.ModelViewSet):
    queryset = APIPaper.objects.all().order_by("msuis_id")
    serializer_class = APIPaperSerializer
    permission_classes = [IsAuthenticated]


class APIStudentAcademicInformationViewSet(viewsets.ModelViewSet):
    queryset = APIStudentAcademicInformation.objects.all().order_by("msuis_id")
    serializer_class = APIStudentAcademicInformationSerializer
    permission_classes = [IsAuthenticated]


class APIStudentPartTermPaperMapViewSet(viewsets.ModelViewSet):
    queryset = APIStudentPartTermPaperMap.objects.all().order_by("msuis_id")
    serializer_class = APIStudentPartTermPaperMapSerializer
    permission_classes = [IsAuthenticated]


class DivisionViewSet(viewsets.ModelViewSet):
    queryset = Division.objects.all().select_related('department')
    serializer_class = DivisionSerializer
    permission_classes = [IsAuthenticated]


def _full_name(student_record):
    name_parts = [
        student_record.get("FirstName"),
        student_record.get("MiddleName"),
        student_record.get("LastName"),
    ]
    merged = " ".join([part.strip() for part in name_parts if isinstance(part, str) and part.strip()])
    return merged or student_record.get("NameAsPerMarksheet") or "Unknown"


def _to_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return None


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def sync_msuis_payload(request):
    """
    Single entrypoint for API-sourced data ingestion through admin app.
    This keeps external-source writes centralized for future DB merge workflows.
    """
    payload = request.data or {}
    apply_to_core = bool(payload.get("apply_to_core", True))

    faculties = payload.get("faculties", [])
    students = payload.get("students", [])
    papers = payload.get("papers", [])
    academic_records = payload.get("student_academic_information", [])
    part_term_maps = payload.get("student_part_term_paper_maps", [])

    counters = {
        "faculties_synced": 0,
        "students_synced": 0,
        "papers_synced": 0,
        "academic_records_synced": 0,
        "part_term_maps_synced": 0,
        "core_departments_upserted": 0,
        "core_students_upserted": 0,
        "core_subjects_upserted": 0,
        "core_enrollments_upserted": 0,
        "core_divisions_upserted": 0,
    }

    # Use the latest academic snapshot to derive student year/faculty defaults.
    latest_academic_by_prn = {}

    with transaction.atomic():
        for row in faculties:
            msuis_id = row.get("Id") or row.get("id")
            if msuis_id is None:
                continue

            name = row.get("FacultyName") or row.get("Name") or row.get("name")
            APIFaculty.objects.update_or_create(
                msuis_id=msuis_id,
                defaults={
                    "name": name,
                    "is_active": _to_bool(row.get("IsActive")),
                    "is_deleted": _to_bool(row.get("IsDeleted")),
                    "raw_payload": row,
                },
            )
            counters["faculties_synced"] += 1

            if apply_to_core and name:
                Department.objects.update_or_create(
                    id=msuis_id,
                    defaults={"name": name},
                )
                counters["core_departments_upserted"] += 1

        for row in academic_records:
            msuis_id = row.get("Id") or row.get("id")
            if msuis_id is None:
                continue

            prn = row.get("PRN") or row.get("Prn") or row.get("prn")
            APIStudentAcademicInformation.objects.update_or_create(
                msuis_id=msuis_id,
                defaults={
                    "prn": prn,
                    "student_admission_id": row.get("StudentAdmissionId"),
                    "programme_instance_part_term_id": row.get("ProgrammeInstancePartTermId"),
                    "programme_id": row.get("ProgrammeId"),
                    "specialisation_id": row.get("SpecialisationId"),
                    "academic_year_id": row.get("AcademicYearId"),
                    "institute_id": row.get("InstituteId"),
                    "faculty_id": row.get("FacultyId"),
                    "part_term_status": row.get("PartTermStatus"),
                    "raw_payload": row,
                },
            )
            counters["academic_records_synced"] += 1

            if prn is not None:
                latest_academic_by_prn[prn] = row

        for row in students:
            prn = row.get("PRN") or row.get("Prn") or row.get("prn")
            if prn is None:
                continue

            APIStudent.objects.update_or_create(
                prn=prn,
                defaults={
                    "first_name": row.get("FirstName"),
                    "middle_name": row.get("MiddleName"),
                    "last_name": row.get("LastName"),
                    "email_id": row.get("EmailId"),
                    "mobile_no": row.get("MobileNo"),
                    "faculty_id": row.get("FacultyId"),
                    "programme_name": row.get("ProgrammeName"),
                    "admission_year": row.get("AdmissionYear"),
                    "passing_year": row.get("PassingYear"),
                    "raw_payload": row,
                },
            )
            counters["students_synced"] += 1

            if apply_to_core:
                academic = latest_academic_by_prn.get(prn, {})
                faculty_id = row.get("FacultyId") or academic.get("FacultyId")
                if not faculty_id:
                    continue

                dept = Department.objects.filter(id=faculty_id).first()
                if dept is None:
                    dept = Department.objects.create(
                        id=faculty_id,
                        name=f"Faculty-{faculty_id}",
                    )
                    counters["core_departments_upserted"] += 1

                # When exact year is unavailable from API, keep a stable fallback.
                year = row.get("Year") or 1

                Student.objects.update_or_create(
                    prn=prn,
                    defaults={
                        "name": _full_name(row),
                        "email": row.get("EmailId") or f"{prn}@classlens.local",
                        "year": year,
                        "department": dept,
                    },
                )
                counters["core_students_upserted"] += 1

        for row in papers:
            msuis_id = row.get("Id") or row.get("id")
            if msuis_id is None:
                continue

            paper_code = row.get("PaperCode") or row.get("Code") or f"PAPER-{msuis_id}"
            paper_name = row.get("PaperName") or row.get("Name") or paper_code

            APIPaper.objects.update_or_create(
                msuis_id=msuis_id,
                defaults={
                    "subject_id": row.get("SubjectId"),
                    "paper_name": paper_name,
                    "paper_code": paper_code,
                    "is_credit": _to_bool(row.get("IsCredit")),
                    "max_marks": row.get("MaxMarks"),
                    "min_marks": row.get("MinMarks"),
                    "credits": row.get("Credits"),
                    "is_active": _to_bool(row.get("IsActive")),
                    "is_deleted": _to_bool(row.get("IsDeleted")),
                    "raw_payload": row,
                },
            )
            counters["papers_synced"] += 1

            if apply_to_core:
                Subject.objects.update_or_create(
                    id=msuis_id,
                    defaults={"code": paper_code, "name": paper_name},
                )
                counters["core_subjects_upserted"] += 1

        for row in part_term_maps:
            msuis_id = row.get("Id") or row.get("id")
            if msuis_id is None:
                continue

            prn = row.get("PRN") or row.get("Prn")
            paper_id = row.get("MstPaperId") or row.get("PaperId")

            APIStudentPartTermPaperMap.objects.update_or_create(
                msuis_id=msuis_id,
                defaults={
                    "prn": prn,
                    "student_academic_information_id": row.get("StudentAcademicInformationId"),
                    "programme_instance_part_term_id": row.get("ProgrammeInstancePartTermId"),
                    "paper_id": row.get("PaperId"),
                    "mst_paper_id": row.get("MstPaperId"),
                    "obtained_marks": row.get("ObtainedMarks"),
                    "obtained_grade": row.get("ObtainedGrade"),
                    "paper_status": row.get("PaperStatus"),
                    "part_term_status": row.get("PartTermStatus"),
                    "division": row.get("Division"),
                    "raw_payload": row,
                },
            )
            counters["part_term_maps_synced"] += 1

            if apply_to_core and prn and paper_id:
                student = Student.objects.filter(prn=prn).first()
                subject = Subject.objects.filter(id=paper_id).first()
                if student and subject:
                    StudentEnrollment.objects.update_or_create(
                        student_prn=student.prn,
                        subject=subject,
                    )
                    StudentAttendancePercentage.objects.get_or_create(
                        student=student,
                        subject=subject,
                        defaults={"present_count": 0, "attendancePercentage": 0.0},
                    )
                    counters["core_enrollments_upserted"] += 1

                    division_name = row.get("Division")
                    semester = row.get("Semester")
                    if division_name and semester:
                        division_obj, _ = Division.objects.get_or_create(
                            department=student.department,
                            program_name=(row.get("ProgrammeName") or "Program"),
                            year=student.year,
                            semester=int(semester),
                            name=str(division_name),
                        )
                        counters["core_divisions_upserted"] += 1

    return Response(
        {
            "message": "MSUIS payload synced via admin app",
            "apply_to_core": apply_to_core,
            "counts": counters,
        },
        status=status.HTTP_200_OK,
    )
 
