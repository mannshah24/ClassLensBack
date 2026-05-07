from django.urls import path
from django.urls import include

from Home.views import getDepartments,registerNewStudent,mark_attendance,teacher_profile,registerNewTeacher,validateStudent,validateTeacher,send_otp,verify_otp,set_password,get_subject_details,verify_email, verify_prn, get_student_attendance,attendance_status,teacher_subjects, get_present_absent_list,change_attendance,get_student_dashboard,update_notification_token,remove_notification_token
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("getDepartments/", getDepartments, name="get_departments"),
    path("registerNewStudent", registerNewStudent, name="register_new_student"),
    path("registerNewTeacher", registerNewTeacher, name="register_new_teacher"),
    path("validateStudent", validateStudent, name="validate_student"),
    path("validateTeacher", validateTeacher, name="validate_teacher"),
    path("sendOtp", send_otp, name="send_otp"),
    path("verifyOtp", verify_otp, name="verify_otp"),
    path("setPassword", set_password, name="set_password"),
    path("getSubjectDetails", get_subject_details, name="get_subject_details"),
    path("verifyEmail", verify_email, name="verify_email"),
    path("students/attendance/", get_student_attendance, name="get_student_attendance"),
    path('verifyPRN',verify_prn, name='verify_prn'),
    path('markAttendance',mark_attendance, name='mark_attendance'),
    path('attendanceStatus/<str:task_id>/',attendance_status, name='attendance_status'),
    path('getSubjects/',teacher_subjects, name='get_teacher_subjects'),
    path('getPresentAbsentList/',get_present_absent_list, name='get_present_absent_list'),
    path('changeAttendance/',change_attendance, name='change_attendance'),
    path('teacherProfile/<int:teacher_id>/',teacher_profile, name='teacher_profile'),
    path('student/dashboard/', get_student_dashboard, name='get_student_dashboard'),
    path('student/notification-token/', update_notification_token, name='update_notification_token'),
    path('student/notification-token/remove/', remove_notification_token, name='remove_notification_token'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
