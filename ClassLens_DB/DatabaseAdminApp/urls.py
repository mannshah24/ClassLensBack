# urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
# from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    DepartmentViewSet,
    TeacherViewSet,
    StudentViewSet,
    SubjectViewSet,
    SubjectFromDeptViewSet,
    StudentEnrollmentViewSet,
    admin_login,
    get_dashboard_stats,
    AdminUserViewSet,
    APIStudentViewSet,
    APIPaperViewSet,
    sync_msuis_payload,
    sync_staging_to_core,
    DivisionViewSet,
)

router = DefaultRouter()
router.register(r"departments", DepartmentViewSet, basename="department")
router.register(r"teachers", TeacherViewSet, basename="teacher")
router.register(r"students", StudentViewSet, basename="student")
router.register(r"subjects", SubjectViewSet, basename="subject")
router.register(
    r"subject-from-dept", SubjectFromDeptViewSet, basename="subject-from-dept"
)
router.register(
    r"student-enrollments", StudentEnrollmentViewSet, basename="student-enrollment"
)
router.register(r"admin-users", AdminUserViewSet, basename="admin-user")
router.register(r"api-students", APIStudentViewSet, basename="api-student")
router.register(r"api-papers", APIPaperViewSet, basename="api-paper")
router.register(r"divisions", DivisionViewSet, basename="division")

urlpatterns = [
    # Authentication
    path("admin/login/", admin_login, name="admin-login"),
    path("admin/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("admin/sync/msuis/", sync_msuis_payload, name="sync-msuis-payload"),
    path("admin/sync/staging/", sync_staging_to_core, name="sync-staging-to-core"),
    # CRUD APIs
    path("admin/stats/", get_dashboard_stats, name="admin-stats"),
    path("admin/", include(router.urls)),
]

"""
API Endpoints:

Authentication:
- POST /api/admin/login/ - Login with username and password
- POST /api/admin/token/refresh/ - Refresh JWT token
- POST /api/admin/create-user/ - Create new admin user (authenticated)

Departments:
- GET    /api/admin/departments/ - List all departments
- POST   /api/admin/departments/ - Create department
- GET    /api/admin/departments/{id}/ - Get department
- PUT    /api/admin/departments/{id}/ - Update department
- DELETE /api/admin/departments/{id}/ - Delete department

Teachers:
- GET    /api/admin/teachers/ - List all teachers
- POST   /api/admin/teachers/ - Create teacher
- POST   /api/admin/teachers/bulk_upload/ - Bulk upload teachers (CSV/Excel)
- GET    /api/admin/teachers/{id}/ - Get teacher
- PUT    /api/admin/teachers/{id}/ - Update teacher
- DELETE /api/admin/teachers/{id}/ - Delete teacher

Students:
- GET    /api/admin/students/ - List all students
- POST   /api/admin/students/ - Create student
- POST   /api/admin/students/bulk_upload/ - Bulk upload students (CSV/Excel)
- GET    /api/admin/students/{id}/ - Get student
- PUT    /api/admin/students/{id}/ - Update student
- DELETE /api/admin/students/{id}/ - Delete student

Subjects:
- GET    /api/admin/subjects/ - List all subjects
- POST   /api/admin/subjects/ - Create subject
- POST   /api/admin/subjects/bulk_upload/ - Bulk upload subjects (CSV/Excel)
- GET    /api/admin/subjects/{id}/ - Get subject
- PUT    /api/admin/subjects/{id}/ - Update subject
- DELETE /api/admin/subjects/{id}/ - Delete subject

SubjectFromDept:
- GET    /api/admin/subject-from-dept/ - List all mappings
- POST   /api/admin/subject-from-dept/ - Create mapping
- POST   /api/admin/subject-from-dept/bulk_upload/ - Bulk upload (CSV/Excel)
- GET    /api/admin/subject-from-dept/{id}/ - Get mapping
- PUT    /api/admin/subject-from-dept/{id}/ - Update mapping
- DELETE /api/admin/subject-from-dept/{id}/ - Delete mapping

StudentEnrollments:
- GET    /api/admin/student-enrollments/ - List all enrollments
- POST   /api/admin/student-enrollments/ - Create enrollment
- POST   /api/admin/student-enrollments/bulk_upload/ - Bulk upload (CSV/Excel)
- GET    /api/admin/student-enrollments/{id}/ - Get enrollment
- PUT    /api/admin/student-enrollments/{id}/ - Update enrollment
- DELETE /api/admin/student-enrollments/{id}/ - Delete enrollment

CRUD for AdminUser:
- GET    /api/admin/admin-users/       -> list admins
- POST   /api/admin/admin-users/       -> create admin
- GET    /api/admin/admin-users/{id}/  -> retrieve admin
- PUT    /api/admin/admin-users/{id}/  -> full update
- PATCH  /api/admin/admin-users/{id}/  -> partial update
- DELETE /api/admin/admin-users/{id}/  -> delete admin
  
"""
