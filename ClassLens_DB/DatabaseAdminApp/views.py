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
    APIStudent,
    APIPaper,
    APIEnrollment,
)
from .serializers import (
    DepartmentSerializer, TeacherSerializer, StudentSerializer,
    SubjectSerializer, SubjectFromDeptSerializer, StudentEnrollmentSerializer,
    TeacherSubjectSerializer, AdminUserSerializer,
    APIStudentSerializer, APIPaperSerializer,
    DivisionSerializer,
)
from django.db import transaction
from django.db.models import Max

from rest_framework.permissions import BasePermission
import re

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


def _normalize_department_label(value):
    if value is None:
        return ""
    normalized = str(value).strip().lower()
    normalized = normalized.replace("&", "and")
    normalized = re.sub(r"[().,/_-]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def _resolve_department(department_name):
    normalized_name = _normalize_department_label(department_name)
    if not normalized_name:
        return None

    exact_match = Department.objects.filter(name__iexact=str(department_name).strip()).first()
    if exact_match is not None:
        return exact_match

    alias_map = {
        "computer science and engineering": [
            "Bachelor in Computer Science and Engineering (B.E)",
            "Computer Science and Engineering",
            "CSE",
        ],
        "cse": [
            "Bachelor in Computer Science and Engineering (B.E)",
            "Computer Science and Engineering",
            "CSE",
        ],
    }

    for alias in alias_map.get(normalized_name, []):
        department = Department.objects.filter(name__iexact=alias).first()
        if department is not None:
            return department

    candidate = Department.objects.all()
    for department in candidate:
        department_label = _normalize_department_label(department.name)
        if normalized_name == department_label:
            return department
        if normalized_name in department_label or department_label in normalized_name:
            return department

    tokens = [token for token in normalized_name.split(" ") if len(token) > 2]
    if tokens:
        query = candidate
        for token in tokens:
            query = query.filter(name__icontains=token)
        department = query.first()
        if department is not None:
            return department

    return None


def _normalize_password_value(value, fallback):
    if value is None:
        return fallback
    if pd is not None:
        try:
            if pd.isna(value):
                return fallback
        except Exception:
            pass
    if isinstance(value, str):
        password = value.strip()
        return password or fallback
    return str(value)

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
                        'name': name,
                        'email': email,
                        'password_hash': make_password(_normalize_password_value(row.get('password'), 'default123')),
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

            df.columns = [str(column).strip() for column in df.columns]

            required_columns = {'prn', 'name', 'email', 'year', 'department_name'}
            missing_columns = required_columns.difference(df.columns)
            if missing_columns:
                return Response(
                    {'error': f"Missing required columns: {', '.join(sorted(missing_columns))}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            created_count = 0
            updated_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    prn = int(row['prn'])
                    full_name = str(row['name']).strip()
                    email = str(row['email']).strip()
                    year = int(row['year'])
                    department_name = str(row['department_name']).strip()
                    if not department_name:
                        raise ValueError('department_name is required')

                    department = _resolve_department(department_name)

                    staging_defaults = {
                        'full_name': full_name,
                        'email_id': email,
                        'raw_payload': {
                            'department_name': department_name,
                            'year': year,
                            'name': full_name,
                        },
                    }

                    _, created = APIStudent.objects.update_or_create(
                        prn=prn,
                        defaults=staging_defaults,
                    )
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                except Exception as e:
                    errors.append(f"Row {index + 1}: {str(e)}")
            
            return Response({
                'message': f'Successfully processed {created_count + updated_count} staging students',
                'created_count': created_count,
                'updated_count': updated_count,
                'skipped_count': len(errors),
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
            updated_count = 0
            errors = []

            current_max = APIPaper.objects.aggregate(max_id=Max("msuis_id")).get("max_id") or 0
            next_id = int(current_max) + 1

            for index, row in df.iterrows():
                try:
                    paper_code = str(row['code']).strip()
                    paper_name = str(row['name']).strip()
                    if not paper_code:
                        raise ValueError("code is required")

                    existing = APIPaper.objects.filter(paper_code=paper_code).first()
                    if existing:
                        existing.paper_name = paper_name or existing.paper_name
                        existing.raw_payload = {
                            "code": paper_code,
                            "name": paper_name,
                        }
                        existing.save(update_fields=["paper_name", "raw_payload"])
                        updated_count += 1
                    else:
                        APIPaper.objects.create(
                            msuis_id=next_id,
                            subject_id=None,
                            paper_name=paper_name or paper_code,
                            paper_code=paper_code,
                            raw_payload={"code": paper_code, "name": paper_name},
                        )
                        next_id += 1
                        created_count += 1
                except Exception as e:
                    errors.append(f"Row {index + 1}: {str(e)}")
            
            return Response({
                'message': f'Successfully processed {created_count + updated_count} staging subjects',
                'created_count': created_count,
                'updated_count': updated_count,
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
            'subject_code': ['CS101', 'CS102', 'EE201'],
            'year': [2, 2, 3],
            'division': ['A', 'A', 'B'],
        }
        df = pd.DataFrame(data)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Enrollments')
            # Add instructions
            instructions = pd.DataFrame({
                'Instructions': [
                    '1. student_prn must match staging students PRN',
                    '2. subject_code must match staging subjects code',
                    '3. year and division are required',
                    '4. Each student-subject-division-year combination must be unique',
                    '5. One student can enroll in multiple subjects'
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
        Expected columns: student_prn, subject_code, year, division
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
            
            df.columns = [str(column).strip() for column in df.columns]

            required_columns = {
                'student_prn',
                'subject_code',
                'year',
                'division',
            }
            missing_columns = required_columns.difference(df.columns)
            if missing_columns:
                return Response(
                    {'error': f"Missing required columns: {', '.join(sorted(missing_columns))}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            created_count = 0
            updated_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    prn = int(row['student_prn'])
                    subject_code = str(row['subject_code']).strip()
                    year = int(row['year'])
                    division = str(row['division']).strip()

                    if not subject_code:
                        raise ValueError('subject_code is required')
                    if not division:
                        raise ValueError('division is required')

                    _, created = APIEnrollment.objects.update_or_create(
                        prn=prn,
                        subject_code=subject_code,
                        division=division,
                        year=year,
                        defaults={},
                    )
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                except Exception as e:
                    errors.append(f"Row {index + 1}: {str(e)}")
            
            return Response({
                'message': f'Successfully processed {created_count + updated_count} staging enrollments',
                'created_count': created_count,
                'updated_count': updated_count,
                'errors': errors
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class APIStudentViewSet(viewsets.ModelViewSet):
    queryset = APIStudent.objects.all().order_by("prn")
    serializer_class = APIStudentSerializer
    permission_classes = [IsAuthenticated]


class APIPaperViewSet(viewsets.ModelViewSet):
    queryset = APIPaper.objects.all().order_by("msuis_id")
    serializer_class = APIPaperSerializer
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
@permission_classes([AllowAny])
def sync_msuis_payload(request):
    """
    Sync student and paper data to staging tables for later promotion to core.
    """
    payload = request.data or {}

    students = payload.get("students", [])
    papers = payload.get("papers", [])

    counters = {
        "students_synced": 0,
        "papers_synced": 0,
    }

    with transaction.atomic():
        for row in students:
            prn = row.get("PRN") or row.get("Prn") or row.get("prn")
            if prn is None:
                continue

            # Build full_name from first/middle/last name components
            first_name = row.get("FirstName") or ""
            middle_name = row.get("MiddleName") or ""
            last_name = row.get("LastName") or ""
            full_name = " ".join([n.strip() for n in [first_name, middle_name, last_name] if n.strip()])
            if not full_name:
                full_name = row.get("NameAsPerMarksheet") or f"PRN {prn}"

            APIStudent.objects.update_or_create(
                prn=prn,
                defaults={
                    "full_name": full_name,
                    "email_id": row.get("EmailId"),
                    "raw_payload": row,
                },
            )
            counters["students_synced"] += 1

        for row in papers:
            msuis_id = row.get("Id") or row.get("id")
            if msuis_id is None:
                continue

            paper_code = row.get("PaperCode") or row.get("Code") or f"PAPER-{msuis_id}"
            paper_name = row.get("PaperName") or row.get("Name") or paper_code

            APIPaper.objects.update_or_create(
                msuis_id=msuis_id,
                defaults={
                    "paper_name": paper_name,
                    "paper_code": paper_code,
                    "raw_payload": row,
                },
            )
            counters["papers_synced"] += 1

    return Response(
        {
            "message": "MSUIS payload synced to staging tables",
            "counts": counters,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def sync_staging_to_core(request):
    """
    Process staging data into live Home_* tables.
    Reads DatabaseAdminApp_* tables and writes to Home_* only.
    """
    counters = {
        "core_students_upserted": 0,
        "core_subjects_upserted": 0,
        "core_enrollments_upserted": 0,
        "core_divisions_upserted": 0,
        "students_skipped": 0,
        "enrollments_skipped": 0,
    }

    def _department_from_payload(raw_payload):
        if not raw_payload:
            return None
        for key in ("department_name", "Department", "department", "FacultyName"):
            value = raw_payload.get(key)
            if value:
                return str(value).strip()
        return None

    def _year_from_payload(raw_payload):
        if not raw_payload:
            return None
        for key in ("year", "Year", "YearOfStudy"):
            value = raw_payload.get(key)
            if value is None:
                continue
            try:
                return int(value)
            except Exception:
                return None
        return None

    def _student_display_name(api_student):
        # APIStudent now stores `full_name` per new_schema
        if getattr(api_student, 'full_name', None):
            return api_student.full_name
        raw_payload = api_student.raw_payload or {}
        return raw_payload.get("name") or raw_payload.get("NameAsPerMarksheet") or f"PRN {api_student.prn}"

    api_students = list(APIStudent.objects.all())
    api_papers = list(APIPaper.objects.all())
    api_enrollments = list(APIEnrollment.objects.all())

    year_by_prn = {}
    for enrollment in api_enrollments:
        if enrollment.prn is None:
            continue
        try:
            year_value = int(enrollment.year)
        except Exception:
            continue
        current = year_by_prn.get(enrollment.prn)
        if current is None or year_value > current:
            year_by_prn[enrollment.prn] = year_value

    with transaction.atomic():
        for paper in api_papers:
            paper_code = (paper.paper_code or "").strip()
            if not paper_code:
                continue
            paper_name = (paper.paper_name or paper_code).strip()
            Subject.objects.update_or_create(
                code=paper_code,
                defaults={"name": paper_name},
            )
            counters["core_subjects_upserted"] += 1

        for api_student in api_students:
            prn = api_student.prn
            if prn is None:
                counters["students_skipped"] += 1
                continue

            raw_payload = api_student.raw_payload or {}
            department_name = _department_from_payload(raw_payload)
            department = None
            if department_name:
                department = _resolve_department(department_name)
                if department is None:
                    department, _ = Department.objects.get_or_create(name=department_name)

            if department is None and getattr(api_student, 'faculty_id', None):
                department = Department.objects.filter(id=api_student.faculty_id).first()

            if department is None:
                counters["students_skipped"] += 1
                continue

            year_value = (
                year_by_prn.get(prn)
                or _year_from_payload(raw_payload)
            )
            if year_value is None:
                year_value = 1

            Student.objects.update_or_create(
                prn=prn,
                defaults={
                    "name": _student_display_name(api_student),
                    "email": api_student.email_id or raw_payload.get("email") or f"{prn}@classlens.local",
                    "year": int(year_value),
                    "department": department,
                },
            )
            counters["core_students_upserted"] += 1

        for enrollment in api_enrollments:
            if enrollment.prn is None or not enrollment.subject_code:
                counters["enrollments_skipped"] += 1
                continue

            student = Student.objects.filter(prn=enrollment.prn).first()
            if student is None:
                counters["enrollments_skipped"] += 1
                continue

            subject_code = enrollment.subject_code.strip()
            subject, created = Subject.objects.get_or_create(
                code=subject_code,
                defaults={"name": subject_code}
            )
            if created:
                counters["core_subjects_upserted"] += 1

            department = None
            if enrollment.department_name:
                department = _resolve_department(enrollment.department_name)
                if department is None:
                    department, _ = Department.objects.get_or_create(name=enrollment.department_name)
            if department is None:
                department = student.department

            division_obj = None
            if (
                department
                and enrollment.division
                and enrollment.year is not None
            ):
                division_obj, created = Division.objects.get_or_create(
                    department=department,
                    year=int(enrollment.year),
                    name=str(enrollment.division).strip(),
                )
                if created:
                    counters["core_divisions_upserted"] += 1

            if division_obj is not None and student.division_id != division_obj.id:
                student.division = division_obj
                student.save(update_fields=["division"])

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

    return Response(
        {
            "message": "Staging data processed into core tables",
            "counts": counters,
        },
        status=status.HTTP_200_OK,
    )
 
