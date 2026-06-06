from rest_framework import status
import string
from django.db.models import F
from rest_framework.decorators import api_view, parser_classes,permission_classes
from rest_framework.response import Response
from .models import Department, Student, Teacher, SubjectFromDept, StudentAttendancePercentage,AttendanceRecord, StudentEnrollment,TeacherSubject, ClassSession, Subject,AttendancePhotos,AdminUser, Division
from django.db.models import Count, Q
from .serializers import DepartmentSerializer,SubjectSerializer
from rest_framework.parsers import MultiPartParser
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django.contrib.auth.hashers import make_password, check_password
from django.shortcuts import get_object_or_404
import traceback
import random
from datetime import datetime
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
            subject_from_dept = get_object_or_404(
                SubjectFromDept, department=department, year=year, semester=semester
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

        if not teacher_subject_qs.exists():
            return Response(
                {"error": "Teacher is not mapped to this subject/division"},
                status=400,
            )

        resolved_division_id = int(division_id) if division_id else None
        if resolved_division_id is None and teacher_subject_qs.count() == 1:
            resolved_division_id = teacher_subject_qs.first().division_id

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
        subjects = TeacherSubject.objects.filter(teacher_id=teacher_id).select_related(
            "subject",
            "division",
        )

        clean_subjects = []
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
            
            # 2. If division was not set or semester/dept/year not found, fallback to subject's department or SubjectFromDept mapping
            if not dept_name or not year or not semester:
                sfd_qs = SubjectFromDept.objects.filter(subject=row.subject_id)
                if row.subject.department:
                    sfd_qs = sfd_qs.filter(department=row.subject.department)
                sfd = sfd_qs.first() or SubjectFromDept.objects.filter(subject=row.subject_id).first()
                
                if sfd:
                    if not dept_name:
                        dept_name = sfd.department.name
                    if not year:
                        year = sfd.year
                    if not semester:
                        semester = sfd.semester

            # 3. Last fallbacks
            if not dept_name:
                dept_name = row.subject.department.name if row.subject.department else (row.teacher_id.department.name if row.teacher_id.department else "General")
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
            })

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
            StudentAttendancePercentage.objects.filter(
                student=attendance_record.student,
                subject=attendance_record.class_session.subject
            ).update(present_count=F('present_count') + (1 if attendance_record.status else -1))

            StudentAttendancePercentage.objects.filter(
                student=attendance_record.student,
                subject=attendance_record.class_session.subject
            ).update(attendancePercentage=(F('present_count')*100.0)/total_sessions)

            attendance_record.save()
            
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
            
            total_sessions = ClassSession.objects.filter(subject=subject).count()
            
            data = StudentAttendancePercentage.objects.filter(
                student=student,
                subject=subject
            ).first()

            if data is None:
                percentage = 0
                present_count = 0
            else:
                percentage = data.attendancePercentage
                present_count = data.present_count

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