from django.urls import path, re_path
from django.urls import include

from Home.views import getDepartments,mark_attendance,teacher_profile,registerNewTeacher,validateStudent,validateTeacher,send_otp,verify_otp,set_password,get_subject_details,verify_email, verify_prn, get_student_attendance,attendance_status,teacher_subjects,teacher_class_sessions, get_present_absent_list,change_attendance,get_student_dashboard,update_notification_token,remove_notification_token, register_student, get_student_subject_attendance, update_face
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    re_path(r"^getDepartments/?$", getDepartments, name="get_departments"),
    re_path(r"^registerNewStudent/?$", register_student, name="register_new_student"),
    re_path(r"^registerStudent/?$", register_student, name="register_student"),
    re_path(r"^updateFace/?$", update_face, name="update_face"),
    re_path(r"^registerNewTeacher/?$", registerNewTeacher, name="register_new_teacher"),
    re_path(r"^validateStudent/?$", validateStudent, name="validate_student"),
    re_path(r"^validateTeacher/?$", validateTeacher, name="validate_teacher"),
    re_path(r"^sendOtp/?$", send_otp, name="send_otp"),
    re_path(r"^verifyOtp/?$", verify_otp, name="verify_otp"),
    re_path(r"^setPassword/?$", set_password, name="set_password"),
    re_path(r"^getSubjectDetails/?$", get_subject_details, name="get_subject_details"),
    re_path(r"^verifyEmail/?$", verify_email, name="verify_email"),
    re_path(r"^students/attendance/?$", get_student_attendance, name="get_student_attendance"),
    re_path(
        r"^student/attendance/subject/(?P<subject_id>\d+)/?$",
        get_student_subject_attendance,
        name="get_student_subject_attendance",
    ),
    re_path(r"^verifyPRN/?$", verify_prn, name="verify_prn"),
    re_path(r"^markAttendance/?$", mark_attendance, name="mark_attendance"),
    re_path(
        r"^attendanceStatus/(?P<task_id>[^/]+)/?$",
        attendance_status,
        name="attendance_status",
    ),
    re_path(r"^teacher/subjects/?$", teacher_subjects, name="teacher_subjects"),
    re_path(r"^getSubjects/?$", teacher_subjects, name="get_teacher_subjects"),
    re_path(r"^teacher/class-sessions/?$", teacher_class_sessions, name="teacher_class_sessions"),
    re_path(r"^getTeacherClassSessions/?$", teacher_class_sessions, name="get_teacher_class_sessions"),
    re_path(r"^getPresentAbsentList/?$", get_present_absent_list, name="get_present_absent_list"),
    re_path(r"^changeAttendance/?$", change_attendance, name="change_attendance"),
    re_path(
        r"^teacherProfile/(?P<teacher_id>\d+)/?$",
        teacher_profile,
        name="teacher_profile",
    ),
    re_path(r"^student/dashboard/?$", get_student_dashboard, name="get_student_dashboard"),
    re_path(r"^student/notification-token/?$", update_notification_token, name="update_notification_token"),
    re_path(
        r"^student/notification-token/remove/?$",
        remove_notification_token,
        name="remove_notification_token",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
