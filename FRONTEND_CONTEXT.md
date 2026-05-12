# ClassLens Frontend Context & Requirements

**Project Goal:** Attendance tracking and display system. Students see their attendance by division, subject, semester, year, and department. Admins manage enrollment sync and divisions. Teachers mark attendance via photo uploads.

---

## 1. Database Schema Summary (Attendance-Focused)

### Mirror Layer (APIEnrollment - Admin Sync)
```
APIEnrollment {
  prn: BigInt (indexed)
  subject_code: String
  department_name: String
  program_name: String
  year: Int
  semester: Int
  division: String (A, B, C, etc.)
  raw_payload: JSON
  synced_at: DateTime
}
```

### Core Layer (Attendance Tracking)

**Core Entities:**
- **Department** — Department name (CS, ECE, ME, etc.)
- **Student** — prn, name, email, year, department, face_embedding, notification_token
- **Subject** — code, name, department_id
- **Division** — department_id, program_name, year, semester, name (A/B/C) — **Unique by (dept, program, year, semester, name)**
- **StudentEnrollment** — student_prn, subject_id, division_id — **Unique by (student_prn, subject, division)**
- **Teacher** — name, email, department_id
- **TeacherSubject** — teacher_id, subject_id (NO division-level control yet)

**Attendance Tracking:**
- **ClassSession** — department_id, year, subject_id, teacher_id, division_id, class_datetime
- **AttendanceRecord** — class_session_id, student_id, status (bool), marked_at — **Unique by (class_session, student)**
- **StudentAttendancePercentage** — student_id, subject_id, present_count, attendancePercentage

---

## 2. Frontend: Student Dashboard

### What Students See

**Overall Attendance Card:**
```
┌─────────────────────────────────┐
│ Your Attendance Overview         │
├─────────────────────────────────┤
│ Overall: 82.5%                  │
│ Classes Attended: 33 / 40       │
│ Last Marked: Today, 10:30 AM    │
└─────────────────────────────────┘
```

**Subject-wise Breakdown (Filtered by Division):**
```
┌──────────────────────────────────────────┐
│ Attendance by Subject                    │
├──────────────────────────────────────────┤
│ Subject         | Attended | Total | %   │
├──────────────────────────────────────────┤
│ Data Structures | 16/20    | 20    | 80% │
│ Algorithms      | 17/20    | 20    | 85% │
│ DBMS            | 14/18    | 18    | 78% │
└──────────────────────────────────────────┘
```

**Filter Options:**
- **By Division:** Current division (auto-selected based on enrollment)
- **By Semester:** Dropdown (1-8)
- **By Year:** Dropdown (1-4)
- **By Department:** Auto-selected from student's enrollment

### API Endpoints (Student)

```
GET /api/student/dashboard/
  Returns:
  {
    "student": {
      "prn": 2021001,
      "name": "John Kumar",
      "year": 2,
      "department": "Computer Science"
    },
    "enrollments": [
      {
        "subject_id": 50,
        "subject_code": "CS101",
        "subject_name": "Data Structures",
        "division": "A",
        "semester": 3,
        "year": 2
      }
    ],
    "overall_attendance": 82.5,
    "attendance_by_subject": [
      {
        "subject_code": "CS101",
        "subject_name": "Data Structures",
        "present_count": 16,
        "total_classes": 20,
        "percentage": 80.0
      }
    ]
  }

GET /api/student/attendance/subject/{subject_id}/?division_id={div_id}&year={year}&semester={sem}
  Returns: Detailed attendance records for that subject

GET /api/student/divisions/
  Returns: List of divisions student is enrolled in
  [
    {
      "id": 1,
      "name": "A",
      "department": "CSE",
      "program": "B.E Computer Science",
      "year": 2,
      "semester": 3
    }
  ]
```

---

## 3. Frontend: Teacher Interface

### What Teachers Do

**Mark Attendance:**
1. Select Subject
2. Select Division (auto-populated from TeacherSubject, currently no division-level constraint)
3. Upload class photo
4. System recognizes faces via face_embedding (pgvector similarity search)
5. Auto-marks attendance for recognized students
6. Teacher reviews and confirms

**View Attendance:**
- Per-subject attendance report
- Attendance history (CSV export)
- Per-student attendance breakdown

### API Endpoints (Teacher)

```
POST /api/markAttendance
  Input:
  {
    "subject_id": 50,
    "division_id": 1,
    "class_photo": <file>,  // Image to extract faces from
    "class_datetime": "2026-05-11T10:00:00Z"
  }
  Returns:
  {
    "class_session_id": 123,
    "recognized_count": 28,
    "unrecognized_count": 2,
    "attendance_records": [
      {
        "student_prn": 2021001,
        "status": true,  // Present
        "confidence": 0.95
      }
    ]
  }

GET /api/teacher/subjects/
  Returns: List of subjects teacher teaches (via TeacherSubject)

GET /api/teacher/subject/{subject_id}/divisions/
  Returns: Divisions this teacher teaches this subject in

GET /api/teacher/attendance/subject/{subject_id}/?division_id={div_id}
  Returns: Attendance records for that subject/division
```

---

## 4. Frontend: Admin Interface

### What Admins Do

**1. Sync MSUIS Enrollments**
- Upload enrollment JSON or call sync endpoint
- Enrollments must include: (prn, subject_code, division, department_name, program_name, year, semester)
- System auto-creates/updates: Department, Division, Student, Subject, StudentEnrollment

**2. Manage Divisions**
- View all divisions by department, program, year, semester
- Create new divisions (if needed)
- Edit division name/settings

**3. Manage Teachers & Assignments**
- Assign teachers to subjects
- ⚠️ **NOTE:** Currently TeacherSubject has no division-level control
  - Teacher A can teach Subject CS101 (to all divisions)
  - If needed, add division FK to TeacherSubject

**4. View Sync Status**
- Last sync timestamp
- Number of enrollments synced
- Errors/warnings during sync

### API Endpoints (Admin)

```
POST /api/admin/sync/msuis/
  Input:
  {
    "enrollments": [
      {
        "prn": 2021001,
        "subject_code": "CS101",
        "department_name": "Department of Computer Science",
        "program_name": "B.E Computer Science",
        "year": 2,
        "semester": 3,
        "division": "A"
      }
    ],
    "apply_to_core": true  // Create core tables
  }
  Returns:
  {
    "status": "success",
    "api_enrollments_created": 2,
    "core_divisions_created": 1,
    "core_students_created": 1,
    "core_enrollments_created": 2,
    "timestamp": "2026-05-11T12:00:00Z"
  }

GET /api/admin/divisions/
  Returns: All divisions with filters by department, program, year, semester
  [
    {
      "id": 1,
      "department": "CSE",
      "program": "B.E Computer Science",
      "year": 2,
      "semester": 3,
      "name": "A",
      "student_count": 45
    }
  ]

GET /api/admin/sync-status/
  Returns: Last sync info, error logs

POST /api/admin/teachers/assign-subject/
  Input:
  {
    "teacher_id": 5,
    "subject_id": 50
    // division_id: Not currently supported, consider adding
  }
  Returns: TeacherSubject record created
```

---

## 5. Key Data Flow

### Enrollment Sync Workflow
```
Admin POST /api/admin/sync/msuis/ with APIEnrollment payload
  ↓
Store in APIEnrollment mirror table
  ↓
If apply_to_core=true:
  - Create/update Department (from department_name)
  - Create/update Student (from prn)
  - Create/update Subject (from subject_code)
  - Create/update Division (from program_name, year, semester, division)
  - Create/update StudentEnrollment (link student → subject → division)
  - Initialize StudentAttendancePercentage (present_count=0, percentage=0.0)
```

### Attendance Marking Workflow
```
Teacher POST /api/markAttendance with class photo
  ↓
Extract faces from photo (RetinaFace detector)
  ↓
Get student enrollments for that (subject, division)
  ↓
For each enrolled student:
  - Compute face embedding (Facenet512 via DeepFace)
  - Search pgvector for matching student.face_embedding (HNSW index)
  - If match > confidence_threshold: mark present
  - If no match: mark absent
  ↓
Create ClassSession record
  ↓
Create AttendanceRecord for each student
  ↓
Recompute StudentAttendancePercentage (present_count, percentage)
  ↓
Return results to teacher for review/confirmation
```

### Student Dashboard Query Workflow
```
Student GET /api/student/dashboard/
  ↓
Query Student by auth token (student.prn)
  ↓
Get StudentEnrollment records filtered by (student_prn, division_id)
  ↓
Get StudentAttendancePercentage for enrolled subjects
  ↓
Compute overall attendance: sum(present_count) / sum(total_classes)
  ↓
Return formatted response to frontend
```

---

## 6. Frontend Components Needed

### Student App
- **Dashboard Component**
  - Overall attendance card
  - Subject-wise attendance table
  - Filters (division, semester, year, department)
  - Attendance history/timeline

- **Subject Attendance Detail**
  - Per-class attendance records
  - Export to CSV/PDF

- **Settings/Profile**
  - Notification preferences
  - Face registration (for attendance photo processing)

### Teacher App
- **Mark Attendance Component**
  - Subject/division selector
  - Photo upload
  - Face recognition preview + confirmation
  - Submit attendance

- **Attendance Reports**
  - Subject-wise report
  - Per-student report
  - Date range filter

### Admin App
- **Sync Dashboard**
  - Upload MSUIS enrollment JSON
  - Sync status/logs
  - API endpoint to trigger sync

- **Division Management**
  - View all divisions (table/list)
  - Create new division (if manual creation needed)
  - Edit division
  - View enrolled students per division

- **Teacher Assignments**
  - Assign teacher to subject
  - View TeacherSubject mappings

---

## 7. Important Notes

### ⚠️ Division-Level Teacher Control
**Current Status:** TeacherSubject has NO division FK. 
- Teacher A can teach Subject CS101, but system doesn't track if it's to Div A or Div B
- This is currently **flexible** (teacher can teach multiple divisions of same subject)
- If you want **stricter control** (one teacher per subject per division), add division FK to TeacherSubject

### ⚠️ Face Recognition Setup
- **Model:** Facenet512 via DeepFace library
- **Vector Index:** pgvector with HNSW (Hierarchical Navigable Small World)
- **Embedding Dimensions:** 512
- **Processing:** Celery task queue via RabbitMQ (async)
- **Requirements:**
  - Database must have pgvector extension installed
  - RabbitMQ broker running (amqp://guest:guest@localhost:5672/)
  - TensorFlow/DeepFace dependencies installed

### ⚠️ Authentication
- Students use JWT (drf-simplejwt) with student PRN
- Teachers use JWT with teacher ID
- Admins use JWT or session-based auth
- Implement refresh token rotation

### ⚠️ Data Consistency
- Attendance is **immutable once marked** (consider adding soft-delete or review workflow)
- StudentAttendancePercentage is **computed** (updated when attendance marked)
- Division assignments are **per-student-per-enrollment** (StudentEnrollment.division_id)

---

## 8. UI/UX Considerations

### Student View
- **Simplicity:** Show only their divisions/subjects
- **Real-time:** Update attendance immediately after marking
- **Mobile-friendly:** Responsive tables, dropdown filters
- **Visual clarity:** Color-code attendance % (green ≥75%, yellow 60-74%, red <60%)

### Teacher View
- **Ease of use:** Minimal clicks to upload and confirm attendance
- **Feedback:** Clear success/error messages
- **Batch operations:** Mark multiple classes at once if needed

### Admin View
- **Overview:** Dashboard showing last sync time, enrollment count, error logs
- **Drill-down:** View details of specific sync batches
- **Bulk operations:** CSV export/import for divisions and teachers

---

## 9. Integration Checklist

- [ ] **Student API integration** — Dashboard, attendance details, filters
- [ ] **Teacher API integration** — Mark attendance, view reports
- [ ] **Admin API integration** — Sync enrollments, manage divisions, assign teachers
- [ ] **Authentication** — JWT tokens, refresh logic, logout
- [ ] **Error handling** — Network errors, validation errors, API errors
- [ ] **Loading states** — Show spinners during API calls
- [ ] **Notification** — Firebase FCM integration (optional, for sync notifications)
- [ ] **Testing** — API mocking, unit tests for filters and calculations

---

## 10. Backend API Base URL

```
Development: http://localhost:8000/api/
Production: https://api.classlens.com/api/
```

All endpoints require `Authorization: Bearer <jwt_token>` header except public endpoints.

---

## Questions for Frontend Developer

1. **Division-level teacher control:** Should we enforce one teacher per subject per division, or allow flexibility?
2. **Face registration workflow:** Should students pre-register faces, or is on-demand recognition enough?
3. **Offline support:** Do teachers need to mark attendance offline and sync later?
4. **Multi-language support:** Required?
5. **Dark mode:** Required?

