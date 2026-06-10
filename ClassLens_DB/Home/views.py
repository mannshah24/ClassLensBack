from rest_framework import status
import string
from django.db.models import F
from rest_framework.decorators import api_view, parser_classes,permission_classes
from rest_framework.response import Response
from .models import Department, Student, Teacher, SubjectFromDept, StudentAttendancePercentage,AttendanceRecord, StudentEnrollment,TeacherSubject, ClassSession, Subject,AttendancePhotos,AdminUser, Division, Holiday, TimetableTemplate, DailySession
from django.db.models import Count, Q
from .serializers import DepartmentSerializer,SubjectSerializer, DailySessionSerializer
from rest_framework.parsers import MultiPartParser
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken

from django.contrib.auth.hashers import make_password, check_password
from django.shortcuts import get_object_or_404
import traceback
import random
from datetime import datetime, date
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import environ
import os
from pathlib import Path
try:
    import cv2
except Exception:
    cv2 = None
try:
    import matplotlib.pyplot as plt
except Exception:
    plt = None

from .face_utils import extract_face_embedding
import uuid
from .tasks import evaluate_attendance, send_attendance_notifications
from .utils import sync_all_attendance_percentages, sync_student_subject_attendance
from django.core.files.storage import default_storage
from celery.result import AsyncResult
from pgvector.django import CosineDistance
from rest_framework.permissions import AllowAny, IsAuthenticated

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

@api_view(["GET"])
def getDepartments(request):
    if request.method == "GET":
        departments = Department.objects.all()
        serializer = DepartmentSerializer(departments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(
        {"detail": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED
    )

@api_view(["POST"])
def registerNewTeacher(request, *args, **kwargs):
    data = request.data

    required_fields = ["name", "email", "password", "departmentID"]
    if not all(field in data for field in required_fields):
        return Response(
            {"error": "Missing one or more required fields."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        if Teacher.objects.filter(email=data["email"]).exists():
            return Response(
                {"error": "Teacher with this email already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        department = get_object_or_404(Department, id=data["departmentID"])
        teacher = Teacher.objects.create(
            name=data["name"],
            email=data["email"],
            password_hash=make_password(data["password"]),
            department=department,
        )
        return Response(
            {"message": "Teacher registered successfully"},
            status=status.HTTP_201_CREATED,
        )
    except Exception as e:
        traceback.print_exc()
        return Response(
            {"detail": f"Error registering teacher: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(["POST"])
def validateStudent(request, *args, **kwargs):
    prn = request.data.get("prn")
    password = request.data.get("password")

    if prn is None or password is None:
        return Response(
            {"detail": "PRN and Password are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        student = Student.objects.get(prn=prn)
        
        # Check if password_hash exists before attempting to verify
        if student.password_hash is None:
            return Response(
                {"detail": "Student account not fully registered. Please set a password first."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        if not check_password(password, student.password_hash):
            return Response(
                {"detail": "Invalid password"}, status=status.HTTP_400_BAD_REQUEST
            )
        else:
            # Issue a simple JWT-like token so frontend can authenticate subsequent requests
            refresh = RefreshToken()
            refresh['student_id'] = student.id
            refresh['prn'] = student.prn

            return Response(
                {
                    "message": "Student validated successfully",
                    "student_id": student.id,
                    "student_name": student.name,
                    "prn": student.prn,
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
                status=status.HTTP_200_OK,
            )
    except Student.DoesNotExist:
        return Response(
            {"detail": "Invalid PRN or password"}, status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        traceback.print_exc()
        return Response(
            {"detail": f"Error validating student: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(["POST"])
def validateTeacher(request, *args, **kwargs):
    email = request.data.get("email")
    password = request.data.get("password")

    if email is None or password is None:
        return Response(
            {"detail": "Email and Password are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:

        teacher = Teacher.objects.get(email=email)
        if teacher.password_hash is None:
            return Response(
                {"detail": "User not registered"}, status=status.HTTP_400_BAD_REQUEST
            )
        if not check_password(password, teacher.password_hash):
            return Response(
                {"detail": "Invalid password"}, status=status.HTTP_400_BAD_REQUEST
            )
        else:
            return Response(
                {"message": "Teacher validated successfully", "teacher_id": teacher.id, 'teacher_name': teacher.name},
                status=status.HTTP_200_OK,
            )
    except Teacher.DoesNotExist:
        return Response(
            {"detail": "Invalid email or user not registered"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        traceback.print_exc()
        return Response(
            {"detail": f"Error validating teacher: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(["POST"])
def get_subject_details(request, *args, **kwargs):
    if request.method == "POST":
        department_name = request.data.get("department")
        year = request.data.get("year")
        semester = request.data.get("semester")
        try:
            department = get_object_or_404(Department, name=department_name)
            
            # Map absolute semester to relative semester if needed
            rel_semester = semester
            try:
                y_val = int(year)
                s_val = int(semester)
                if s_val > 2:
                    rel_semester = s_val - (y_val - 1) * 2
            except Exception:
                pass

            subject_from_dept = get_object_or_404(
                SubjectFromDept, department=department, year=year, semester=rel_semester
            )

            subjects = subject_from_dept.subject.all()
            subjects = SubjectSerializer(subjects, many=True).data
            divisions = Division.objects.filter(
                department=department,
                year=year,
            ).order_by("name")
            divisions_data = [
                {
                    "id": division.id,
                    "name": division.name,
                    "year": division.year,
                }
                for division in divisions
            ]
            return Response(
                {"subjects": subjects, "divisions": divisions_data, "message": "subject details"},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"detail": f"Error getting subject details: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

@api_view(["POST"])
def send_otp(request, *args, **kwargs):
    try:
        email = request.data.get("email")
        otp = random.randint(1000, 9999)

        if email is None:
            return Response(
                {"detail": "Email is required"}, status=status.HTTP_400_BAD_REQUEST
            )
        
        teacher = Teacher.objects.filter(email=email).first()
        student = None if teacher else Student.objects.filter(email=email).first()

        if not (teacher or student):
            return Response(
                {"detail": "No user found with this email"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if teacher is not None:
            if teacher.password_hash is not None:
                print("Password is not None")
                return Response(
                    {"detail": "Email is already registered"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        cache.set(email, otp, 600)

        print('OTP:', otp)

        display_name = teacher.name if teacher else student.name
            
        

        subject = "Your ClassLens OTP Verification Code"

        plain_message = f"""
        Hello,

        Your One Time Password for ClassLens is: {otp}

        This code is valid for 10 minutes. For your security, please do not share it with anyone.

        If you did not request this, you can safely ignore this email.

        Thank you,
        The ClassLens Team
        """
        
        html_message = f"""
        <p>Hello {display_name},</p>
        <p>Your One Time Password for ClassLens is: <strong>{otp}</strong></p>
        <p>This code is valid for <strong>10 minutes</strong>. For your security, please do not share it with anyone.</p>
        <p>If you did not request this, you can safely ignore this email.</p>
        <br>
        <p>Thank you,<br>
        <strong>The ClassLens Team</strong></p>
        """

        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False,
            )
            return Response({"message": "OTP sent successfully"}, status=200)
        except Exception as email_error:
            print(f"Email send error: {email_error}")
            return Response({"message": "Failed to send OTP"}, status=500)

    except Exception as e:
        traceback.print_exc()
        return Response(
            {"detail": "Method not allowed"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(["POST"])
def verify_email(request, *args, **kwargs):
    try:
        email = request.data.get("email")
        if email is None:
            return Response(
                {"detail": "Email is required"}, status=status.HTTP_400_BAD_REQUEST
            )
        if not (Teacher.objects.filter(email=email).exists() or Student.objects.filter(email=email).exists()):
            return Response(
                {"detail": "No user found with this email"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        teacher = Teacher.objects.filter(email=email).first()
        student = None if teacher else Student.objects.filter(email=email).first()

        if teacher is not None:
            if teacher.password_hash is not None:
                print("Password is not None")
                return Response(
                    {"detail": "Email is already registered! Try login instead"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                return Response({"message": "Email verified successfully"}, status=200)
        else:
            if student.password_hash is not None:
                print("Password is not None")
                return Response(
                    {"detail": "Email is already registered"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                 return Response({"message": "Email verified successfully"}, status=200)

    except Exception as e:
        traceback.print_exc()
        return Response(
            {"detail": "Method not allowed"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(["POST"])
def verify_prn(request, *args, **kwargs):
    try:
        prn = request.data.get("prn")
        if prn is None:
            return Response(
                {"detail": "PRN is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        student = Student.objects.filter(prn=prn).first()
        if not student:
            return Response(
                {"detail": "No user found with this PRN"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if student.password_hash is not None:
            print("Password is not None")
            return Response(
                {"detail": "PRN is already registered! Try login instead"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            return Response({
                "message": "PRN verified successfully",
                "email": student.email
            }, status=200)
    except Exception as e:
        traceback.print_exc()
        return Response(
            {"detail": "Method not allowed"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(["POST"])
def verify_otp(request, *args, **kwargs):
    try:
        email = request.data.get("email")
        otp = request.data.get("otp")
        if email is None or otp is None:
            return Response(
                {"detail": "Email and OTP are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cached_otp = cache.get(email)

        if cached_otp is None or cached_otp != int(otp):
            return Response(
                {"detail": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST
            )
        cache.delete(email)
        return Response({"message": "OTP verified successfully"}, status=200)

    except Exception as e:
        traceback.print_exc()
        return Response(
            {"detail": "Method not allowed"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

def _update_student_password(prn, password, photo):
    if prn is None or password is None:
        return Response(
            {"detail": "PRN and Password are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    student = Student.objects.filter(prn=prn).first()
    if not student:
        return Response(
            {"detail": "No Student found with this prn"},
            status=status.HTTP_404_NOT_FOUND,
        )

    student.password_hash = make_password(password)

    if photo is not None:
        try:
            embedding = extract_face_embedding(photo)
            student.face_embedding = [float(value) for value in embedding]
        except ValueError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    student.save()
    print(f"✓ Student password set successfully for PRN {prn}")
    print(f"  Hash (first 20 chars): {student.password_hash[:20]}...")

    verify = Student.objects.get(prn=prn)
    if verify.password_hash:
        print(f"✓ Verified: Password hash persisted in database for PRN {prn}")
        return Response({"message": "Student password set successfully"}, status=200)

    print(f"✗ ERROR: Password hash is None after save for PRN {prn}!")
    return Response({"detail": "Failed to persist password"}, status=500)

@api_view(["POST"])
def set_password(request, *args, **kwargs):
    try:
        password = request.data.get("password")
        if request.data.get("email"):
            email=request.data.get("email")
            if email is None or password is None:
                return Response(
                    {"detail": "Email and Password are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            teacher = Teacher.objects.filter(email=email).first()
            if teacher : 
                teacher.password_hash = make_password(password)
                teacher.save()
                print(f"✓ Teacher password set successfully for {email}")
                print(f"  Hash (first 20 chars): {teacher.password_hash[:20]}...")
                
                # Verify it was saved to DB
                verify = Teacher.objects.get(email=email)
                if verify.password_hash:
                    print(f"✓ Verified: Password hash persisted in database")
                    return Response({"message": "Teacher password set successfully"}, status=200)
                else:
                    print(f"✗ ERROR: Password hash is None after save!")
                    return Response({"detail": "Failed to persist password"}, status=500)
            else : 
                return Response({"detail": "No Teacher found with this email"}, status=status.HTTP_404_NOT_FOUND)
        
        elif request.data.get("prn"):
            prn = request.data.get("prn")
            photo = request.FILES.get("photo")
            return _update_student_password(prn, password, photo)

    except Exception as e:
        traceback.print_exc()
        print(f"✗ Exception in set_password: {str(e)}")
        return Response(
            {"detail": f"An error occurred while updating the password: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(["POST"])
def register_student(request, *args, **kwargs):
    prn = request.data.get("prn")
    password = request.data.get("password")
    photo = request.FILES.get("photo")

    if password is None and photo is not None:
        student = Student.objects.filter(prn=prn).first()
        if not student:
            return Response(
                {"detail": "No Student found with this prn"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            embedding = extract_face_embedding(photo)
            student.face_embedding = [float(value) for value in embedding]
            student.save(update_fields=["face_embedding"])
            return Response({"message": "Student face updated successfully"}, status=200)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    return _update_student_password(prn, password, photo)
    
def registerNewStudent(photo):
    return extract_face_embedding(photo)


@api_view(["POST"])
def update_face(request, *args, **kwargs):
    """POST /api/updateFace/ - multipart/form-data: prn, photo

    Updates only the student's `face_embedding` without changing password or other fields.
    """
    try:
        # Prefer authenticated student identity if provided via Bearer token
        prn = None
        auth_header = request.META.get('HTTP_AUTHORIZATION') or request.headers.get('Authorization')
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
                try:
                    payload = AccessToken(token)
                    prn = payload.get('prn') or payload.get('student_prn') or payload.get('student_id')
                    # If student_id found, map to prn
                    if isinstance(prn, int) and not payload.get('prn'):
                        # prn may be student id - fetch actual prn
                        student_obj = Student.objects.filter(id=prn).first()
                        if student_obj:
                            prn = student_obj.prn
                except Exception:
                    prn = None

        if prn is None:
            prn = request.POST.get("prn") or request.data.get("prn")
        photo = request.FILES.get("photo")

        if prn is None:
            return Response({"detail": "prn is required"}, status=status.HTTP_400_BAD_REQUEST)

        if photo is None:
            return Response({"detail": "photo file is required"}, status=status.HTTP_400_BAD_REQUEST)

        student = Student.objects.filter(prn=prn).first()
        if not student:
            return Response({"detail": "No Student found with this prn"}, status=status.HTTP_404_NOT_FOUND)

        try:
            embedding = extract_face_embedding(photo)
            student.face_embedding = [float(value) for value in embedding]
            student.save(update_fields=["face_embedding"])
            return Response({"message": "Student face updated successfully"}, status=200)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        traceback.print_exc()
        return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["POST"])
def get_student_attendance(request, *args, **kwargs):
    try:
        subject_id = request.data.get("subject_id")
        division_id = request.data.get("division_id")

        if subject_id is None:
            return Response(
                {"detail": "subject_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Fetch enrolled student PRNs from StudentEnrollment
        enrolled_prns = StudentEnrollment.objects.filter(subject_id=subject_id).values_list('student_prn', flat=True)

        # Get Student records and annotate them with real total and attended counts from AttendanceRecord
        students = Student.objects.filter(prn__in=enrolled_prns).annotate(
            real_total_classes=Count(
                'attendancerecord',
                filter=Q(attendancerecord__class_session__subject_id=subject_id)
            ),
            real_attended_classes=Count(
                'attendancerecord',
                filter=Q(attendancerecord__class_session__subject_id=subject_id, attendancerecord__status=True)
            )
        )
        if division_id:
            students = students.filter(division_id=division_id)

        result = []
        for student in students:
            total = student.real_total_classes
            attended = student.real_attended_classes
            
            percentage = 0.0
            if total > 0:
                percentage = (attended * 100.0) / total
                if percentage > 100.0:
                    percentage = 100.0
            
            result.append({
                "student_id": student.id,
                "student_name": student.name,
                "total_classes": total,
                "attended_classes": attended,
                "attendance_percentage": percentage
            })

        return Response(
            {"attendance": result},
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        traceback.print_exc()
        return Response(
            {"detail": "Something went wrong"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(["GET"])
def get_student_subject_attendance(request, subject_id, *args, **kwargs):
    try:
        division_id = request.query_params.get("division_id")
        year = request.query_params.get("year")
        semester = request.query_params.get("semester")

        records = AttendanceRecord.objects.filter(
            class_session__subject_id=subject_id
        ).select_related(
            "student",
            "student__division",
            "class_session",
        )

        if division_id:
            records = records.filter(student__division_id=division_id)
        if year:
            records = records.filter(class_session__year=year)
        # Division no longer stores semester; skip filtering by division.semester

        results = []
        for record in records:
            results.append(
                {
                    "class_session_id": record.class_session_id,
                    "student_id": record.student_id,
                    "student_name": record.student.name,
                    "student_prn": record.student.prn,
                    "status": record.status,
                    "marked_at": record.marked_at.isoformat(),
                    "class_datetime": record.class_session.class_datetime.isoformat(),
                    "division_id": record.student.division_id,
                }
            )

        return Response(
            {"attendance_records": results},
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        traceback.print_exc()
        return Response(
            {"detail": "Something went wrong"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(["POST"])
@parser_classes([MultiPartParser])
def mark_attendance(request, *args, **kwargs):
    """
    API endpoint to start an attendance session.
    Expects form-data with: photo, subject_id, teacher_id, department_id, year
    """
    photos = request.FILES.getlist("photo")
    subject_id = request.data.get("subjectID")
    teacher_id = request.data.get("teacherID")
    departmentName = request.data.get("departmentName")
    year = request.data.get("year")
    division_id = request.data.get("divisionID")

    # Debug log to see exactly what is received
    print("=" * 60)
    print("MARK ATTENDANCE REQUEST RECEIVED")
    print(f"  photos      : {photos}")
    print(f"  subject_id  : {subject_id!r}")
    print(f"  teacher_id  : {teacher_id!r}")
    print(f"  department  : {departmentName!r}")
    print(f"  year        : {year!r}")
    print(f"  division_id : {division_id!r}")
    print("=" * 60)

    missing = []
    if not photos:         missing.append("photo")
    if not subject_id:     missing.append("subjectID")
    if not teacher_id:     missing.append("teacherID")
    if not departmentName: missing.append("departmentName")
    if not year:           missing.append("year")

    if missing:
        return Response({"error": f"Missing required fields: {', '.join(missing)}"}, status=400)

    if int(teacher_id) == 0:
        return Response({"error": "Invalid teacher ID (0). Please log in again."}, status=400)

    try:
        teacher_subject_qs = TeacherSubject.objects.filter(
            teacher_id=teacher_id,
            subject_id=subject_id,
        )

        if division_id:
            teacher_subject_qs = teacher_subject_qs.filter(division_id=division_id)

        resolved_division_id = int(division_id) if division_id else None
        if resolved_division_id is None and teacher_subject_qs.exists():
            resolved_division_id = teacher_subject_qs.first().division_id

        # Update DailySession today if it exists for this subject/division to track proxy teacher
        from datetime import date
        today = date.today()
        daily_session_qs = DailySession.objects.filter(
            subject_id=subject_id,
            date=today
        )
        if resolved_division_id:
            daily_session_qs = daily_session_qs.filter(division_id=resolved_division_id)
        
        daily_session = daily_session_qs.first()
        if daily_session:
            if daily_session.teacher_id != int(teacher_id):
                daily_session.proxy_teacher_id = int(teacher_id)
                daily_session.save(update_fields=['proxy_teacher'])


        class_session = ClassSession.objects.create(
            department = get_object_or_404(Department, name=departmentName),
            year = year,
            subject = get_object_or_404(Subject, id=subject_id),
            teacher = get_object_or_404(Teacher, id=teacher_id),
            class_datetime = timezone.now(),
        )

        total_sessions=ClassSession.objects.filter(
            subject=class_session.subject
        ).count()

        for photo in photos:
            AttendancePhotos.objects.create(
                class_session=class_session,
                photo=photo
            )

        task = evaluate_attendance.delay(
            total_sessions,
            class_session.id,
            request.scheme,
            request.get_host(),
            resolved_division_id,
        )

        return Response({
            "message": "Attendance processing started. You will be notified once it's done.",
            "task_id": task.id
        }, status=202)
    
    except Exception as e:
        traceback.print_exc()
        return Response({"error": "Failed to start attendance session."}, status=500)

    # file_bytes = np.asarray(bytearray(photo.read()), dtype=np.uint8)
    # image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    # task = evaluate_attendance.delay(absolute_file_path, request.scheme, request.get_host())
    # print(task.id)
    # return Response({
    #     "message": "Attendance processing started. You will be notified once it's done.",
    #     "task_id": task.id
    # }, status=202)

@api_view(["GET", "POST"])
def teacher_subjects(request, *args, **kwargs):
    teacher_id = (
        request.query_params.get("teacher_id")
        if request.method == "GET"
        else request.data.get("teacher_id")
    )
    if not teacher_id:
        return Response({"error": "Teacher ID is required"}, status=400)
    try:
        teacher = Teacher.objects.select_related('department').get(id=teacher_id)
        subjects = TeacherSubject.objects.filter(teacher_id=teacher_id).select_related(
            "subject",
            "division",
        )

        clean_subjects = []
        existing_keys = set()

        for row in subjects:
            dept_name = None
            year = None
            semester = None

            # 1. Try to get department and year from division if set
            if row.division:
                dept_name = row.division.department.name
                year = row.division.year
                
                # Try to resolve semester from SubjectFromDept with matching department and year
                sfd = SubjectFromDept.objects.filter(
                    subject=row.subject_id, 
                    department=row.division.department, 
                    year=row.division.year
                ).first()
                if sfd:
                    semester = sfd.semester
            
            # 2. If division was not set or semester/dept/year not found, fallback to SubjectFromDept mapping
            if not dept_name or not year or not semester:
                sfd_qs = SubjectFromDept.objects.filter(subject=row.subject_id)
                sfd = sfd_qs.first()
                
                if sfd:
                    if not dept_name:
                        dept_name = sfd.department.name
                    if not year:
                        year = sfd.year
                    if not semester:
                        semester = sfd.semester

            # 3. Last fallbacks
            if not dept_name:
                dept_name = row.teacher_id.department.name if row.teacher_id.department else "General"
            if not year:
                year = 1
            if not semester:
                semester = 1

            strength = StudentEnrollment.objects.filter(
                subject_id=row.subject_id,
                student_prn__in=Student.objects.filter(division_id=row.division_id).values_list("prn", flat=True),
            ).count() if row.division_id else StudentEnrollment.objects.filter(subject_id=row.subject_id).count()

            clean_subjects.append({
                "id": row.subject_id,
                "code": row.subject.code,
                "name": row.subject.name,
                "division_id": row.division_id,
                "division_name": row.division.name if row.division else None,
                "department_name": dept_name,
                "year": year,
                "semester": semester,
                "strength": strength,
                "is_mapped": True,
            })
            existing_keys.add((row.subject_id, row.division_id))

        return Response({"subjects": clean_subjects}, status=200)
    except Exception as e:
        traceback.print_exc()
        return Response(
            {"detail": "Something went wrong"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )



@api_view(["GET", "POST"])
def teacher_class_sessions(request, *args, **kwargs):
    teacher_id = (
        request.query_params.get("teacher_id")
        if request.method == "GET"
        else request.data.get("teacher_id")
    )
    limit = (
        request.query_params.get("limit")
        if request.method == "GET"
        else request.data.get("limit")
    )

    if not teacher_id:
        return Response({"error": "Teacher ID is required"}, status=400)

    try:
        teacher = get_object_or_404(Teacher, id=teacher_id)

        limit_value = 10
        if limit not in (None, ""):
            limit_value = int(limit)
            if limit_value <= 0:
                limit_value = 10

        sessions_qs = (
            ClassSession.objects.filter(teacher=teacher)
            .select_related("subject", "teacher", "department")
            .prefetch_related("attendancerecord_set__student__division")
            .order_by("-class_datetime")
        )

        if limit_value:
            sessions_qs = sessions_qs[:limit_value]

        class_sessions = []
        for session in sessions_qs:
            attendance_records = list(session.attendancerecord_set.all())
            present_count = sum(1 for record in attendance_records if record.status)
            total_count = len(attendance_records)
            absent_count = total_count - present_count

            division_names = sorted(
                {
                    record.student.division.name
                    for record in attendance_records
                    if record.student and record.student.division_id
                }
            )

            division_name = division_names[0] if len(division_names) == 1 else None
            if division_name is None:
                teacher_subject = (
                    TeacherSubject.objects.filter(
                        teacher_id=teacher,
                        subject_id=session.subject_id,
                    )
                    .select_related("division")
                    .order_by("id")
                    .first()
                )
                division_name = (
                    teacher_subject.division.name
                    if teacher_subject and teacher_subject.division
                    else None
                )

            class_sessions.append(
                {
                    "class_session_id": session.id,
                    "subject_name": session.subject.name,
                    "division_name": division_name or "All Divisions",
                    "class_datetime": session.class_datetime.isoformat(),
                    "present_count": present_count,
                    "absent_count": absent_count,
                    "total_count": total_count,
                }
            )

        return Response({"class_sessions": class_sessions}, status=status.HTTP_200_OK)

    except ValueError:
        return Response({"error": "limit must be an integer"}, status=400)
    except Exception:
        traceback.print_exc()
        return Response(
            {"detail": "Something went wrong"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(["POST"])
def get_present_absent_list(request, *args, **kwargs):
    class_session_id = request.data.get("class_session_id")
    isPresent = request.data.get("isPresent")
    
    if isinstance(isPresent, str):
        isPresent = isPresent.lower() == "true"
    if not class_session_id:
        return Response({"error": "Class Session ID is required"}, status=400)
    
    absentees_students=AttendanceRecord.objects.filter(class_session_id=class_session_id, status=isPresent).annotate(student_name=F('student__name'),student_prn=F('student__prn')).values('student_id', 'student_name', 'student_prn')

    return Response({"students": absentees_students}, status=status.HTTP_200_OK)

@api_view(["POST"])
def change_attendance(request, *args, **kwargs):
    class_session_id = request.data.get("class_session_id")
    student_list=request.data.get("student_list")

    class_session = ClassSession.objects.get(id=class_session_id)
    total_sessions=ClassSession.objects.filter(
        subject=class_session.subject
    ).count()

    notification_list = []

    for student_id in student_list:
        attendance_record = AttendanceRecord.objects.filter(class_session_id=class_session_id, student_id=student_id).first()
        if attendance_record:
            attendance_record.status = not attendance_record.status
            attendance_record.save()
            
            sync_student_subject_attendance(
                attendance_record.student,
                attendance_record.class_session.subject
            )
            
            # Add to notification list
            notification_list.append((attendance_record.student, attendance_record.status))
    
    # Send notifications to students whose attendance was changed
    if notification_list:
        send_attendance_notifications(
            notification_list,
            class_session.subject.name,
            class_session.class_datetime
        )
    
    return Response(status=status.HTTP_200_OK)

@api_view(["GET"])
def attendance_status(request, task_id,*args, **kwargs):

    if not task_id:
        return Response({"error": "Task ID is required"}, status=400)

    task = AsyncResult(task_id)

    if task.successful():
        return Response({"status": task.status, "result": task.result}, status=200)
    elif task.failed():
        return Response({"status": task.status, "result": task.result}, status=500)
    
    return Response({"status": task.status,"result":{"num_faces":0,"image_url":""}}, status=202)

@api_view(["GET"])
def teacher_profile(request,teacher_id, *args, **kwargs):
    print(teacher_id)
    if not teacher_id:
        return Response({"error": "Teacher ID is required"}, status=400)
    try:
        teacher = get_object_or_404(Teacher, id=teacher_id)
        teacher_subject_qs = TeacherSubject.objects.filter(teacher_id_id=teacher_id).select_related("division")
        total_Subject = teacher_subject_qs.count()
        total_Student = 0
        for teacher_subject in teacher_subject_qs:
            enrollment_qs = StudentEnrollment.objects.filter(subject_id=teacher_subject.subject_id)
            if teacher_subject.division_id:
                enrollment_qs = enrollment_qs.filter(
                    student_prn__in=Student.objects.filter(division_id=teacher_subject.division_id).values_list("prn", flat=True)
                )
            total_Student += enrollment_qs.count()
        department = teacher.department.name if teacher.department else None
        profile_data = {
            "name": teacher.name,
            "email": teacher.email,
            "total_subjects": total_Subject,
            "total_students": total_Student,
            "department_name": department,
            "date_joined": teacher.date_joined
        }
        return Response({"teacher_profile": profile_data}, status=200)
    except Exception as e:
        traceback.print_exc()
        return Response(
            {"detail": "Something went wrong"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def _resolve_student_semester(student):
    subject_ids = set(
        StudentEnrollment.objects.filter(student_prn=student.prn).values_list("subject_id", flat=True)
    )
    subject_mappings = (
        SubjectFromDept.objects.filter(department=student.department, year=student.year)
        .prefetch_related("subject")
        .order_by("semester")
    )

    best_semester = None
    best_score = -1

    for subject_mapping in subject_mappings:
        mapped_subject_ids = set(subject_mapping.subject.values_list("id", flat=True))
        score = len(subject_ids.intersection(mapped_subject_ids))

        if score > best_score:
            best_score = score
            best_semester = subject_mapping.semester

    if best_score > 0:
        return best_semester

    first_mapping = subject_mappings.first()
    return first_mapping.semester if first_mapping else None


def _resolve_student_program(student):
    from Home.models import TimetableTemplate, DailySession
    p = TimetableTemplate.objects.filter(division=student.division).exclude(program__isnull=True).exclude(program='').values_list('program', flat=True).first()
    if p:
        return p
    p = DailySession.objects.filter(division=student.division).exclude(program__isnull=True).exclude(program='').values_list('program', flat=True).first()
    if p:
        return p
    if student.department:
        dept_name = student.department.name.lower()
        if "computer" in dept_name or "cse" in dept_name:
            return "B.E. CSE"
        elif "electronics" in dept_name or "extc" in dept_name:
            return "B.E. EXTC"
        elif "mechanical" in dept_name:
            return "B.E. Mech"
        elif "civil" in dept_name:
            return "B.E. Civil"
        elif "information technology" in dept_name or "it" in dept_name:
            return "B.E. IT"
    return "B.E. CSE"


@api_view(['POST'])
@permission_classes([AllowAny])
def admin_login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    
    try:
        admin = AdminUser.objects.get(username=username, is_active=True)
        if admin.check_password(password):
            
            refresh = RefreshToken()
            
            refresh['user_id'] = admin.id 
            refresh['username'] = admin.username
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'username': admin.username
            })
        else:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    except AdminUser.DoesNotExist:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(["POST"])
def get_student_dashboard(request, *args, **kwargs):
    """
    Fetches all subjects and attendance data for a specific student.
    Expects: student_id
    """
    try:
        student_id = request.data.get("student_id")

        if student_id is None:
            return Response(
                {"detail": "student_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        student = get_object_or_404(Student, id=student_id)
        semester = _resolve_student_semester(student)

        enrollments = StudentEnrollment.objects.filter(student_prn=student.prn).select_related('subject')

        subjects_data = []
        for enrollment in enrollments:
            subject = enrollment.subject
            
            total_sessions = AttendanceRecord.objects.filter(
                student=student,
                class_session__subject=subject
            ).count()
            
            data = StudentAttendancePercentage.objects.filter(
                student=student,
                subject=subject
            ).first()

            if data is None:
                present_count = 0
            else:
                present_count = data.present_count

            percentage = 0.0
            if total_sessions > 0:
                percentage = (present_count * 100.0) / total_sessions

            teacher = None
            if student.division is not None:
                teacher = TeacherSubject.objects.filter(
                    subject=subject,
                    division=student.division
                ).select_related('teacher_id').first()
                if teacher is None:
                    teacher = TeacherSubject.objects.filter(
                        subject=subject,
                        division__isnull=True
                    ).select_related('teacher_id').first()
            else:
                teacher = TeacherSubject.objects.filter(
                    subject=subject
                ).select_related('teacher_id').first()

            teacher_name = teacher.teacher_id.name if teacher else "N/A"

            subjects_data.append({
                "id": subject.id,
                "name": subject.name,
                "code": subject.code,
                "teacher": teacher_name,
                "total": total_sessions,
                "attended": present_count,
                "percentage": round(float(percentage), 2)
            })

        recent_records = AttendanceRecord.objects.filter(
            student=student
        ).select_related('class_session__subject').order_by('-marked_at')[:5]

        recent_activity = []
        for record in recent_records:
            recent_activity.append({
                "subject": record.class_session.subject.name,
                "status": "Present" if record.status else "Absent",
                "date": record.marked_at.isoformat()
            })

        # compute overall attendance across all subjects (weighted by total sessions)
        total_classes_sum = sum(item.get('total', 0) for item in subjects_data)
        attended_sum = sum(item.get('attended', 0) for item in subjects_data)
        overall_percentage = None
        if total_classes_sum > 0:
            overall_percentage = round((attended_sum / total_classes_sum) * 100.0, 2)

        return Response({
            "student_name": student.name,
            "prn": student.prn,
            "email": student.email,
            "year": student.year,
            "department_name": student.department.name if student.department else None,
            "division_id": student.division_id,
            "division_name": student.division.name if student.division else None,
            "semester": semester,
            "overall_attendance": overall_percentage,
            "subjects": subjects_data,
            "recent_activity": recent_activity,
        }, status=status.HTTP_200_OK)

    except Exception as e:
        traceback.print_exc()
        return Response(
            {"detail": "Something went wrong"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(["POST"])
def update_notification_token(request, *args, **kwargs):
    """
    Updates the FCM notification token for a student.
    Expects: student_id, notification_token
    """
    try:
        student_id = request.data.get("student_id")
        notification_token = request.data.get("notification_token")

        if student_id is None or notification_token is None:
            return Response(
                {"detail": "student_id and notification_token are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        student = get_object_or_404(Student, id=student_id)
        student.notification_token = notification_token
        student.save()

        return Response(
            {"message": "Notification token updated successfully"},
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        traceback.print_exc()
        return Response(
            {"detail": "Something went wrong"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
def remove_notification_token(request, *args, **kwargs):
    """
    Removes the FCM notification token for a student (on logout).
    Expects: student_id
    """
    try:
        student_id = request.data.get("student_id")

        if student_id is None:
            return Response(
                {"detail": "student_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        student = get_object_or_404(Student, id=student_id)
        student.notification_token = None
        student.save()

        return Response(
            {"message": "Notification token removed successfully"},
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        traceback.print_exc()
        return Response(
            {"detail": "Something went wrong"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    
@api_view(["GET"])
def health(request,*args,**kwargs):
    return Response(
        {"message":"ok"},
        status=200
    )

@api_view(["GET"])
def get_session_photos(request, session_id, *args, **kwargs):
    from urllib.parse import urljoin
    try:
        photos = AttendancePhotos.objects.filter(class_session_id=session_id).order_by('id')
        base_url = f"{request.scheme}://{request.get_host().rstrip('/')}"
        
        results = []
        for p in photos:
            photo_url = urljoin(f"{base_url}/", p.photo.url)
            detected_photo_url = urljoin(f"{base_url}/", p.detected_photo.url) if p.detected_photo else photo_url
            
            results.append({
                "id": p.id,
                "original_url": photo_url,
                "detected_url": detected_photo_url,
            })
            
        return Response({"photos": results}, status=200)
    except Exception as e:
        traceback.print_exc()
        return Response({"error": str(e)}, status=500)

@api_view(["POST"])
@parser_classes([MultiPartParser])
def resubmit_attendance(request, *args, **kwargs):
    from .tasks import evaluate_additional_attendance
    class_session_id = request.data.get("class_session_id")
    photos = request.FILES.getlist("photo")
    
    if not class_session_id:
        return Response({"error": "class_session_id is required"}, status=400)
    if not photos:
        return Response({"error": "No photos uploaded"}, status=400)
        
    try:
        class_session = get_object_or_404(ClassSession, id=class_session_id)
        
        new_photo_ids = []
        for photo in photos:
            p = AttendancePhotos.objects.create(
                class_session=class_session,
                photo=photo
            )
            new_photo_ids.append(p.id)
            
        division_id = None
        teacher_subject = TeacherSubject.objects.filter(
            teacher_id=class_session.teacher,
            subject=class_session.subject
        ).first()
        if teacher_subject:
            division_id = teacher_subject.division_id
            
        task = evaluate_additional_attendance.delay(
            class_session.id,
            new_photo_ids,
            request.scheme,
            request.get_host(),
            division_id,
        )
        
        return Response({
            "message": "Additional attendance photos processing started.",
            "task_id": task.id
        }, status=202)
    except Exception as e:
        traceback.print_exc()
        return Response({"error": f"Failed to start additional attendance processing: {str(e)}"}, status=500)


@api_view(['GET'])
def get_daily_schedule(request):
    """
    Fetches the schedule for today. Checks for holidays first.
    """
    target_date_str = request.GET.get('date')
    if target_date_str:
        try:
            target_date = date.fromisoformat(target_date_str)
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
    else:
        target_date = date.today()

    # 1. The Holiday Gatekeeper
    holiday = Holiday.objects.filter(date=target_date, is_working_day=False).first()
    
    if holiday:
        return Response({
            "is_holiday": True,
            "holiday_name": holiday.name,
            "message": f"Enjoy your holiday for {holiday.name}! No classes today.",
            "sessions": []
        }, status=status.HTTP_200_OK)

    # Filter by student_id or teacher_id
    student_id = request.GET.get('student_id')
    teacher_id = request.GET.get('teacher_id')

    division_id = None
    if student_id:
        try:
            student = Student.objects.get(id=student_id)
            division_id = student.division_id
        except Student.DoesNotExist:
            return Response({"error": "Student not found."}, status=status.HTTP_404_NOT_FOUND)
    elif teacher_id:
        division_ids = list(
            TeacherSubject.objects.filter(teacher_id=teacher_id)
            .exclude(division__isnull=True)
            .values_list('division_id', flat=True)
            .distinct()
        )
        if division_ids:
            division_id = division_ids

    # Trigger generation dynamically to sync daily sessions with timetable template
    from .tasks import generate_daily_sessions
    generate_daily_sessions(for_date_str=target_date.isoformat(), division_id=division_id)

    sessions = DailySession.objects.filter(date=target_date)

    if student_id:
        if division_id:
            sessions = sessions.filter(division_id=division_id)
        else:
            sessions = sessions.none()

    if teacher_id:
        sessions = sessions.filter(Q(teacher_id=teacher_id) | Q(proxy_teacher_id=teacher_id))

    sessions = sessions.order_by('ui_order')
    serializer = DailySessionSerializer(sessions, many=True)

    return Response({
        "is_holiday": False,
        "holiday_name": None,
        "sessions": serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
def update_session_order(request):
    """
    Updates the ui_order of a DailySession.
    Expects: session_id (int), ui_order (int)
    """
    session_id = request.data.get('session_id')
    ui_order = request.data.get('ui_order')
    if session_id is None or ui_order is None:
        return Response({"error": "session_id and ui_order are required"}, status=400)
    try:
        session = DailySession.objects.get(id=session_id)
        session.ui_order = ui_order
        session.save(update_fields=['ui_order'])
        return Response({"message": "ui_order updated successfully"}, status=200)
    except DailySession.DoesNotExist:
        return Response({"error": "Session not found"}, status=404)



@api_view(['GET'])
def list_holidays(request):
    """
    Lists all holidays, sorted by date.
    """
    try:
        holidays = Holiday.objects.all().order_by('date')
        from .serializers import HolidaySerializer
        serializer = HolidaySerializer(holidays, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        traceback.print_exc()
        return Response(
            {"error": f"Failed to retrieve holidays: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def declare_holiday(request):
    """
    Creates a new Holiday.
    Expected request body:
    {
        "date": "YYYY-MM-DD",
        "name": "Holiday",
        "is_working_day": false
    }
    """
    data = request.data
    date_str = data.get("date")
    name = data.get("name")
    is_working_day = data.get("is_working_day", False)

    if not date_str or not name:
        return Response(
            {"error": "Both 'date' and 'name' are required fields."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return Response(
            {"error": "Invalid date format. Use YYYY-MM-DD."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check if holiday for this date already exists
    if Holiday.objects.filter(date=date_str).exists():
        return Response(
            {"error": "Holiday for this date already exists."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        holiday = Holiday.objects.create(
            date=date_str,
            name=name,
            is_working_day=is_working_day
        )
        from .serializers import HolidaySerializer
        return Response(
            HolidaySerializer(holiday).data,
            status=status.HTTP_201_CREATED
        )
    except Exception as e:
        traceback.print_exc()
        return Response(
            {"error": f"Failed to declare holiday: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
def delete_holiday(request, pk):
    """
    Deletes an existing holiday by id.
    """
    try:
        holiday = Holiday.objects.filter(pk=pk).first()
        if not holiday:
            return Response(
                {"error": "Holiday not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        holiday.delete()
        return Response(
            {"message": "Holiday deleted successfully."},
            status=status.HTTP_200_OK
        )
    except Exception as e:
        traceback.print_exc()
        return Response(
            {"error": f"Failed to delete holiday: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_weekly_timetable(request):
    """
    Fetches the full weekly timetable for a student's division.
    """
    student_id = request.GET.get('student_id')
    if not student_id:
        return Response({"error": "student_id is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        student = Student.objects.get(id=student_id)
        if not student.division:
            return Response({
                "division_name": None,
                "timetable": {}
            }, status=status.HTTP_200_OK)

        templates = TimetableTemplate.objects.filter(division=student.division).order_by('day_of_week')
        from .serializers import TimetableTemplateSerializer
        serializer = TimetableTemplateSerializer(templates, many=True)
        
        # Group by day of week
        days_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        grouped = {day: [] for day in days_names}
        for item in serializer.data:
            day_idx = item.get('day_of_week')
            if day_idx is not None and 0 <= day_idx < len(days_names):
                day_name = days_names[day_idx]
                grouped[day_name].append(item)

        return Response({
            "division_name": student.division.name,
            "timetable": grouped
        }, status=status.HTTP_200_OK)

    except Student.DoesNotExist:
        return Response({"error": "Student not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        traceback.print_exc()
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def student_bulk_upload(request):
    """
    Bulk upload students from CSV/Excel linked to specific department, program, and division.
    """
    import pandas as pd
    from django.db import transaction

    department_id = request.data.get('department')
    division_id = request.data.get('division')
    program = request.data.get('program')
    file = request.FILES.get('file')

    if not file:
        return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
    if not department_id:
        return Response({'error': 'Department is required'}, status=status.HTTP_400_BAD_REQUEST)
    if not division_id:
        return Response({'error': 'Division is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        department = Department.objects.get(id=department_id)
        division = Division.objects.get(id=division_id)

        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        else:
            return Response({'error': 'Invalid file format. Use CSV or Excel.'}, status=status.HTTP_400_BAD_REQUEST)

        df.columns = [str(column).strip() for column in df.columns]

        required_columns = {'prn', 'name', 'email'}
        missing_columns = required_columns.difference(df.columns)
        if missing_columns:
            return Response(
                {'error': f"Missing required columns in file: {', '.join(sorted(missing_columns))}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        created_count = 0
        errors = []
        default_year = division.year if hasattr(division, 'year') else 1

        with transaction.atomic():
            for index, row in df.iterrows():
                try:
                    prn = int(row['prn'])
                    name = str(row['name']).strip()
                    email = str(row['email']).strip()
                    year = int(row.get('year', default_year))

                    student, created = Student.objects.update_or_create(
                        prn=prn,
                        defaults={
                            'name': name,
                            'email': email,
                            'department': department,
                            'division': division,
                            'year': year,
                        }
                    )
                    
                    if created:
                        created_count += 1
                except Exception as e:
                    errors.append(f"Row {index + 1}: {str(e)}")

        return Response({
            'message': f'Successfully processed {created_count} students.',
            'created_count': created_count,
            'errors': errors
        }, status=status.HTTP_201_CREATED)

    except Department.DoesNotExist:
        return Response({'error': 'Department not found.'}, status=status.HTTP_404_NOT_FOUND)
    except Division.DoesNotExist:
        return Response({'error': 'Division not found.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def attendance_analytics(request):
    """
    Fetch attendance stats/logs.
    Accepts: class (subject_id), batch (division_id/year), student_id, department, program, search_student, threshold_percentage.
    """
    subject_id = request.GET.get('class')
    division_id = request.GET.get('batch')
    student_id = request.GET.get('student_id')
    department_id = request.GET.get('department')
    program = request.GET.get('program')
    student_search = request.GET.get('search_student')
    threshold_str = request.GET.get('threshold_percentage')

    try:
        # 1. Dynamically sync attendance cache table on demand
        sync_all_attendance_percentages()

        # 2. Filter students matching criteria
        students_queryset = Student.objects.all().select_related('division', 'department')
        if student_id:
            students_queryset = students_queryset.filter(id=student_id)
        if division_id:
            students_queryset = students_queryset.filter(division_id=division_id)
        if department_id:
            students_queryset = students_queryset.filter(department_id=department_id)
        if program:
            from Home.models import TimetableTemplate, DailySession
            div_ids = set(TimetableTemplate.objects.filter(program__icontains=program).values_list('division_id', flat=True))
            div_ids.update(DailySession.objects.filter(program__icontains=program).values_list('division_id', flat=True))
            students_queryset = students_queryset.filter(division_id__in=div_ids)

        student_profile = None

        if student_search:
            student = None
            search_str = student_search.strip()
            if search_str.isdigit():
                student = Student.objects.filter(prn=int(search_str)).first()
            if not student:
                tokens = search_str.split()
                if tokens:
                    q_obj = Q()
                    for token in tokens:
                        q_obj &= Q(name__icontains=token)
                    student = Student.objects.filter(q_obj).first()
            
            if student:
                semester = _resolve_student_semester(student)
                
                # Fetch all enrolled subjects for this student
                enrolled_subjects = Subject.objects.filter(
                    id__in=StudentEnrollment.objects.filter(student_prn=student.prn).values_list('subject_id', flat=True)
                )
                
                # Map subject ID to absolute semester
                subject_to_sem = {}
                from Home.models import SubjectFromDept
                for mapping in SubjectFromDept.objects.filter(department=student.department).prefetch_related("subject"):
                    abs_sem = (mapping.year - 1) * 2 + mapping.semester
                    for sub in mapping.subject.all():
                        subject_to_sem[sub.id] = abs_sem

                current_abs_sem = (student.year - 1) * 2 + semester
                
                subjects_data = []
                total_classes_sum = 0
                attended_sum = 0
                semesters_map = {}
                
                for subject in enrolled_subjects:
                    sap = StudentAttendancePercentage.objects.filter(student=student, subject=subject).first()
                    present_count = sap.present_count if sap else 0
                    attendance_percentage = sap.attendancePercentage if sap else 0.0
                    
                    total_sessions = AttendanceRecord.objects.filter(student=student, class_session__subject=subject).count()
                    
                    if total_sessions > 0 and not sap:
                        attended = AttendanceRecord.objects.filter(student=student, class_session__subject=subject, status=True).count()
                        present_count = attended
                        attendance_percentage = (attended / total_sessions) * 100.0
                    
                    sub_detail = {
                        "id": subject.id,
                        "name": subject.name,
                        "code": subject.code,
                        "total": total_sessions,
                        "attended": present_count,
                        "percentage": round(attendance_percentage, 2)
                    }
                    
                    subjects_data.append(sub_detail)
                    total_classes_sum += total_sessions
                    attended_sum += present_count
                    
                    abs_sem = subject_to_sem.get(subject.id, current_abs_sem)
                    if abs_sem not in semesters_map:
                        semesters_map[abs_sem] = {
                            "semester_number": abs_sem,
                            "subjects": [],
                            "total_classes": 0,
                            "total_attended": 0
                        }
                    semesters_map[abs_sem]["subjects"].append(sub_detail)
                    semesters_map[abs_sem]["total_classes"] += total_sessions
                    semesters_map[abs_sem]["total_attended"] += present_count
                
                semesters_data = []
                for abs_sem, sem_info in sorted(semesters_map.items()):
                    sem_overall = 0.0
                    if sem_info["total_classes"] > 0:
                        sem_overall = round((sem_info["total_attended"] / sem_info["total_classes"]) * 100.0, 2)
                    
                    semesters_data.append({
                        "semester_number": abs_sem,
                        "overall_attendance": sem_overall,
                        "subjects": sem_info["subjects"]
                    })
                
                overall_percentage = 0.0
                if total_classes_sum > 0:
                    overall_percentage = round((attended_sum / total_classes_sum) * 100.0, 2)
                
                student_profile = {
                    "id": student.id,
                    "name": student.name,
                    "prn": student.prn,
                    "email": student.email,
                    "year": student.year,
                    "semester": semester,
                    "division_name": student.division.name if student.division else "N/A",
                    "department_name": student.department.name if student.department else "N/A",
                    "program": _resolve_student_program(student),
                    "overall_attendance": overall_percentage,
                    "subjects": subjects_data,
                    "semesters": semesters_data
                }
                
                students_queryset = students_queryset.filter(id=student.id)
            else:
                students_queryset = students_queryset.none()

        # If subject is filtered, keep only students enrolled in that subject
        if subject_id:
            enrolled_prns = StudentEnrollment.objects.filter(subject_id=subject_id).values_list('student_prn', flat=True)
            students_queryset = students_queryset.filter(prn__in=enrolled_prns)

        # Count total class sessions per student per subject in a single query
        student_subject_totals = {}
        totals_qs = AttendanceRecord.objects.filter(student__in=students_queryset).values('student_id', 'class_session__subject_id').annotate(count=Count('id'))
        for item in totals_qs:
            student_subject_totals[(item['student_id'], item['class_session__subject_id'])] = item['count']

        # Query StudentAttendancePercentage for filtered students
        saps_queryset = StudentAttendancePercentage.objects.filter(student__in=students_queryset).select_related('subject')
        from collections import defaultdict
        student_saps = defaultdict(list)
        for sap in saps_queryset:
            student_saps[sap.student_id].append(sap)

        # Map student PRN to their enrolled subjects
        student_enrollments = defaultdict(list)
        se_records = StudentEnrollment.objects.filter(student_prn__in=students_queryset.values_list('prn', flat=True))
        for se in se_records:
            student_enrollments[se.student_prn].append(se.subject_id)

        stats = []
        for student in students_queryset:
            if subject_id:
                sub_id = int(subject_id)
                subject_obj = Subject.objects.filter(id=sub_id).first()
                if not subject_obj:
                    continue
                sap_record = next((s for s in student_saps[student.id] if s.subject_id == sub_id), None)
                present = sap_record.present_count if sap_record else 0
                total = student_subject_totals.get((student.id, sub_id), 0)
                percentage = (present * 100.0) / total if total > 0 else 0.0
                subj_name = subject_obj.name
                subj_code = subject_obj.code
            else:
                enrolled_subj_ids = student_enrollments.get(student.prn, [])
                total = 0
                present = 0
                for s_id in enrolled_subj_ids:
                    total += student_subject_totals.get((student.id, s_id), 0)
                    sap_record = next((s for s in student_saps[student.id] if s.subject_id == s_id), None)
                    if sap_record:
                        present += sap_record.present_count
                
                percentage = (present * 100.0) / total if total > 0 else 0.0
                subj_name = "All Subjects"
                subj_code = "ALL"

            stats.append({
                "student_id": student.id,
                "student_name": student.name,
                "prn": student.prn,
                "email": student.email,
                "division_name": student.division.name if student.division else "N/A",
                "division_id": student.division_id,
                "subject_id": int(subject_id) if subject_id else None,
                "subject_name": subj_name,
                "subject_code": subj_code,
                "present_count": present,
                "total_sessions": total,
                "attendance_percentage": round(percentage, 2)
            })

        if threshold_str:
            try:
                threshold = float(threshold_str)
                stats = [s for s in stats if s['attendance_percentage'] < threshold]
            except ValueError:
                pass

        return Response({
            "analytics": stats,
            "student_profile": student_profile
        }, status=status.HTTP_200_OK)

    except Exception as e:
        traceback.print_exc()
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)