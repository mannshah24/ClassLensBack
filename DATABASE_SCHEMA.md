# ClassLens Attendance Tracking Database Schema

## Overview

ClassLens uses a **focused database architecture optimized for attendance tracking**. Students can view their attendance grouped by divisions, subjects, semesters, years, and departments.

```
┌─────────────────────────────────────┐
│ MSUIS External API                  │
│ (Faculty, Student, Subject)         │
│ (Enrollment & Division Info)        │
└──────────────┬──────────────────────┘
               │ (Sync Payload)
               ▼
┌──────────────────────────────────────────┐
│ LAYER 1: ENROLLMENT DATA (Mirror)        │
│ (Enrollment & Division mapping only)     │
├──────────────────────────────────────────┤
│ • APIEnrollment (student-subject-div)    │
└──────────────┬───────────────────────────┘
               │ (Project to Core)
               ▼
┌──────────────────────────────────────────┐
│ LAYER 2: ATTENDANCE CORE TABLES           │
│ (Attendance tracking & statistics)       │
├──────────────────────────────────────────┤
│ • Department                             │
│ • Student                                │
│ • Subject                                │
│ • Division                               │
│ • StudentEnrollment                      │
│ • Teacher                                │
│ • TeacherSubject                         │
│ • ClassSession                           │
│ • AttendanceRecord                       │
│ • StudentAttendancePercentage            │
│ • AdminUser                              │
└──────────────────────────────────────────┘
```

---

## Layer 1: Enrollment Data Mirror (Simplified)

This minimal mirror table stores enrollment data from MSUIS used to sync divisions and student enrollments. Focus is on attendance information only.

### 1. APIEnrollment — Student Enrollment with Division & Semester

**Location:** `DatabaseAdminApp/models.py`

```python
class APIEnrollment(models.Model):
    """Mirrors student enrollment with division and semester info from MSUIS."""
    prn = models.BigIntegerField(db_index=True)
    subject_code = models.CharField(max_length=100)
    department_name = models.CharField(max_length=200)
    program_name = models.CharField(max_length=200)
    year = models.IntegerField()
    semester = models.IntegerField()
    division = models.CharField(max_length=20)  # A, B, C, etc.
    raw_payload = models.JSONField(default=dict)
    synced_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('prn', 'subject_code', 'division', 'semester')
```

| Field | Type | Purpose |
|-------|------|---------|
| `prn` | BigInt (indexed) | Student PRN |
| `subject_code` | Char(100) | Subject code (e.g., "CS101") |
| `department_name` | Char(200) | Department name |
| `program_name` | Char(200) | Program/degree name |
| `year` | Int | Student year (1, 2, 3, 4) |
| `semester` | Int | Semester (1-8) |
| `division` | Char(20) | Division code (A, B, C, etc.) |
| `raw_payload` | JSON | Original API data |
| `synced_at` | DateTime | Last sync timestamp |

**Why needed:**
- Store enrollment info with division and semester
- Minimal data for division and enrollment creation in core tables
- No academic grades, marks, or specialized fields
- Focus purely on attendance grouping

**Example data:**
```
prn: 2021001
subject_code: "CS101"
department_name: "Department of Computer Science"
program_name: "B.E Computer Science"
year: 2
semester: 3
division: "A"
synced_at: 2026-05-11 12:00:00
```

---

## Layer 2: Core Attendance Tracking Tables (Home App)

These tables are **optimized for attendance tracking**. They contain only the essential data for recording and displaying attendance by divisions, subjects, semesters, years, and departments.

### 6. Department — Core Department Entity

**Location:** `Home/models.py`

```python
class Department(models.Model):
    name = models.TextField(unique=True, null=False)
```

| Field | Type | Purpose |
|-------|------|---------|
| `id` | AutoInt (PK) | Unique identifier |
| `name` | Text (unique) | Department name; must be unique |

**Source:** Created from `APIFaculty.name` during MSUIS sync  
**Purpose:** Core reference for all department-related data in ClassLens  
**Example:**
```
id: 10
name: "Department of Computer Science"
```

---

### 7. Student — Core Student Entity

**Location:** `Home/models.py`

```python
class Student(models.Model):
    prn = models.BigIntegerField(unique=True, null=False)
    name = models.TextField(null=False)
    email = models.EmailField(unique=True, null=False)
    password_hash = models.TextField(null=True, blank=True)
    year = models.IntegerField(null=False)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    face_embedding = VectorField(dimensions=512, null=True, blank=True)
    notification_token = models.TextField(null=True, blank=True)
```

| Field | Type | Purpose |
|-------|------|---------|
| `prn` | BigInt (unique) | Student PRN; primary identifier |
| `name` | Text | Full student name |
| `email` | Email (unique) | Student email for login |
| `password_hash` | Text | Hashed password for authentication |
| `year` | Int | Academic year (1, 2, 3, 4) |
| `department` | FK to Department | Department enrollment |
| `face_embedding` | Vector(512) | Face recognition during attendance photo processing |
| `notification_token` | Text | Firebase FCM token for push notifications |

**Source:** Created/updated from `APIEnrollment` during sync  
**Purpose:** Core student entity for attendance tracking  
**Example:**
```
prn: 2021001
name: "John Kumar Singh"
email: "john@example.com"
year: 2
department_id: 10
```

---

### 8. Subject — Course/Paper Entity

**Location:** `Home/models.py`

```python
class Subject(models.Model):
    code = models.TextField(unique=True, null=False)
    name = models.TextField(null=False)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
```

| Field | Type | Purpose |
|-------|------|---------|
| `id` | AutoInt (PK) | Unique identifier |
| `code` | Text (unique) | Subject code (e.g., "CS101") |
| `name` | Text | Subject name (e.g., "Data Structures") |
| `department` | FK to Department | Department offering this subject |

**Source:** Extracted from `APIEnrollment` during sync  
**Purpose:** Defines subjects for attendance tracking  
**Example:**
```
id: 50
code: "CS101"
name: "Data Structures and Algorithms"
department_id: 10
```

---

### 9. Division — ⭐ NEW — Teaching Division Classification

**Location:** `Home/models.py`

```python
class Division(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    program_name = models.TextField(null=False, default="")
    year = models.IntegerField(null=False)
    semester = models.IntegerField(null=False)
    name = models.CharField(max_length=20, null=False)

    class Meta:
        unique_together = ("department", "program_name", "year", "semester", "name")
```

| Field | Type | Purpose |
|-------|------|---------|
| `id` | AutoInt (PK) | Unique identifier |
| `department` | FK to Department | Which department offers this division |
| `program_name` | Text | Degree program name (e.g., "B.E Computer Science") |
| `year` | Int | Academic year (1, 2, 3, 4) |
| `semester` | Int | Semester (1-8, where 1-2=year1, 3-4=year2, etc.) |
| `name` | Char(20) | Division code (A, B, C, D, etc.) |

**Why this table was added:**
- **Requirement**: Group students by division for attendance tracking
- Students in the same division attend the same class sessions together
- Teachers mark attendance per division
- Each division can have separate schedules/teachers

**Uniqueness constraint:** `(department, program_name, year, semester, name)` ensures no duplicates like "CSE B.E 2nd year Sem 3 Division A"

**Example data:**
```
id: 1
department_id: 10
program_name: "B.E Computer Science"
year: 2
semester: 3
name: "A"

id: 2
department_id: 10
program_name: "B.E Computer Science"
year: 2
semester: 3
name: "B"
```

This creates two parallel divisions (A and B) for the same year/semester, allowing independent attendance tracking.

---

### 10. StudentEnrollment — Student-Subject-Division Mapping

**Location:** `Home/models.py`

```python
class StudentEnrollment(models.Model):
    student_prn = models.BigIntegerField(null=False)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    division = models.ForeignKey(Division, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('student_prn', 'subject', 'division')
```

| Field | Type | Purpose |
|-------|------|---------|
| `student_prn` | BigInt | Student's PRN |
| `subject` | FK to Subject | Enrolled subject |
| `division` | FK to Division | Division (A, B, C, etc.) |

**Source:** Created from `APIEnrollment` during sync  
**Purpose:** Track which students are enrolled in which subjects within specific divisions  
**Example:**
```
student_prn: 2021001, subject_id: 50, division_id: 1  # John in CS101, Division A
student_prn: 2021001, subject_id: 51, division_id: 1  # John in CS102, Division A
```

---

### 11. TeacherSubject — Teacher-Subject Mapping

**Location:** `Home/models.py`

```python
class TeacherSubject(models.Model):
    teacher_id = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('teacher_id', 'subject')
```

**Purpose:** Track which teacher teaches which subject  
**Example:**
```
teacher_id: 5, subject_id: 50  # Dr. Smith teaches CS101
```

---

### 12. ClassSession — ⭐ MODIFIED — Attendance Session Record

**Location:** `Home/models.py`

```python
class ClassSession(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    year = models.IntegerField(null=False)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    division = models.ForeignKey(Division, on_delete=models.SET_NULL, null=True, blank=True)  # ⭐ NEW
    class_datetime = models.DateTimeField(null=False)
```

| Field | Type | Purpose |
|-------|------|---------|
| `id` | AutoInt (PK) | Unique session identifier |
| `department` | FK to Department | Which department |
| `year` | Int | Student year |
| `subject` | FK to Subject | Subject taught |
| `teacher` | FK to Teacher | Teacher who taught |
| `division` | FK to Division | ⭐ **NEW** — Which division attended |
| `class_datetime` | DateTime | When the class happened |

**Why `division` field was added:**
- **Before:** Couldn't distinguish "Class of CS101 for Div A" from "Class of CS101 for Div B"
- **After:** Can track separate class sessions for each division
- When teacher marks attendance, they specify division
- Attendance only applies to that division's students

**Example:**
```
ClassSession 1:
  subject_id: 50 (CS101)
  teacher_id: 5 (Dr. Smith)
  division_id: 1 (CSE B.E 2nd year Sem 3 Div A)
  class_datetime: 2026-05-11 10:00 AM

ClassSession 2:
  subject_id: 50 (CS101)
  teacher_id: 5 (Dr. Smith)
  division_id: 2 (CSE B.E 2nd year Sem 3 Div B)
  class_datetime: 2026-05-11 12:00 PM
```

---

### 13. AttendanceRecord — Individual Student Attendance

**Location:** `Home/models.py`

```python
class AttendanceRecord(models.Model):
    class_session = models.ForeignKey(ClassSession, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    status = models.BooleanField()  # True = Present, False = Absent
    marked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('class_session', 'student')
```

**Purpose:** One record per student per class session  
**Example:**
```
class_session_id: 1
student_id: 1001
status: True  # Student was present
marked_at: 2026-05-11 10:30 AM
```

---

### 14. StudentAttendancePercentage — Aggregated Per-Subject Attendance

**Location:** `Home/models.py`

```python
class StudentAttendancePercentage(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    present_count = models.IntegerField(null=False, default=0)
    attendancePercentage = models.FloatField(null=False, default=0.0)
```

| Field | Type | Purpose |
|-------|------|---------|
| `student` | FK to Student | Which student |
| `subject` | FK to Subject | For which subject |
| `present_count` | Int | Number of classes attended |
| `attendancePercentage` | Float | (present_count / total_classes) * 100 |

**Purpose:** Quick lookup of per-subject attendance without recalculating  
**Used by:** Student dashboard to show per-subject attendance breakdown  
**Example:**
```
student_id: 1001
subject_id: 50
present_count: 17
attendancePercentage: 85.0  # (17 / 20) * 100
```

---

### 15. Teacher — Existing Core Table

**Location:** `Home/models.py`

```python
class Teacher(models.Model):
    name = models.TextField(null=False)
    email = models.EmailField(unique=True, null=False)
    password_hash = models.TextField(null=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    date_joined = models.DateField(null=True, auto_now_add=True)
```

**Purpose:** Core teacher entity for ClassLens  
**No changes in this release**

---

### 16. AdminUser — Admin Authentication

**Location:** `Home/models.py`

```python
class AdminUser(models.Model):
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_authenticated(self):
        return True
```

**Purpose:** Admin users for managing MSUIS sync and system configuration

---

## Data Flow: Attendance-Only Sync Workflow

### Scenario: Sync 1 student enrolled in 2 subjects in Division A

#### Input: Enrollment API Payload

```json
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
    },
    {
      "prn": 2021001,
      "subject_code": "CS102",
      "department_name": "Department of Computer Science",
      "program_name": "B.E Computer Science",
      "year": 2,
      "semester": 3,
      "division": "A"
    }
  ],
  "apply_to_core": true
}
```

#### Step 1: Mirror Storage (APIEnrollment)

**APIEnrollment table (2 records):**
```
prn: 2021001
subject_code: "CS101"
department_name: "Department of Computer Science"
program_name: "B.E Computer Science"
year: 2
semester: 3
division: "A"
synced_at: 2026-05-11 12:00:00

prn: 2021001
subject_code: "CS102"
department_name: "Department of Computer Science"
program_name: "B.E Computer Science"
year: 2
semester: 3
division: "A"
synced_at: 2026-05-11 12:00:00
```

#### Step 2: Core Table Projection (When apply_to_core=true)
programme_name: "B.E Computer Science"
part_term_status: "Active"
```

**APIStudentPartTermPaperMap table (2 records):**
```
msuis_id: 1000, prn: 2021001, paper_id: 50, division: "A"
msuis_id: 1001, prn: 2021001, paper_id: 51, division: "A"
```

#### Step 2: Projection → Core Operational Tables

**Department table (if not exists):**
```
id: 10
name: "Department of Computer Science"
```

**Student table (create/update):**
```
prn: 2021001
name: "John Kumar Singh"  # Merged from first/middle/last
email: "john.singh@example.com"
year: 2
department_id: 10
```

**Subject table (2 records, if not exist):**
```
id: 50, code: "CS101", name: "Data Structures"
id: 51, code: "CS102", name: "Algorithms"
```

**Division table (create/update):**
```
id: 1
department_id: 10
program_name: "B.E Computer Science"
year: 2
semester: 3
name: "A"
```

**StudentEnrollment table (2 records):**
```
student_prn: 2021001, subject_id: 50, division_id: 1
student_prn: 2021001, subject_id: 51, division_id: 1
```

**StudentAttendancePercentage table (2 records, initialized):**
```
student_id: 1001, subject_id: 50, present_count: 0, attendancePercentage: 0.0
student_id: 1001, subject_id: 51, present_count: 0, attendancePercentage: 0.0
```

---

## Why Two Layers?

| Aspect | Mirror Layer | Core Layer |
|--------|--------------|-----------|
| **Purpose** | Store enrollment data from API exactly | Track attendance and display to students |
| **Data Retention** | Keep enrollment records | Keep attendance records and metrics |
| **Transformations** | None—raw API data | Normalized enrollments + attendance aggregations |
| **Update Pattern** | Upsert (idempotent) | Insert attendance records, update percentages |
| **Key Focus** | Enrollment data (student-subject-division) | Attendance metrics (present%, per-subject, per-division) |
| **Access Pattern** | Historical sync lookup | Real-time attendance dashboard queries |

### Real-world Scenario:

1. API sends enrollment: PRN 2021001 in CS101 Division A Semester 3
2. Mirror table (APIEnrollment) stores exactly as received
3. Core creates: Student, Subject, Division, StudentEnrollment
4. Teacher marks attendance for 20 classes of this division
5. Student dashboard shows: "Overall: 85%, CS101: 85%, CS102: 90%"

---

## Summary of Attendance-Focused Architecture

### Core Purpose
**Track and display student attendance by division, subject, semester, year, and department**

### Key Components

**Mirror Layer (DatabaseAdminApp):**
- APIEnrollment — Stores enrollment data with division and semester info

**Core Layer (Home app):**
- Division — Groups students by year, semester, program, department
- StudentEnrollment — Links student to subject + division
- ClassSession — Records when a class session occurs (per division)
- AttendanceRecord — Individual student attendance in each session
- StudentAttendancePercentage — Computed per-subject attendance %

**Data Flow:**
1. Admin syncs enrollments via `POST /api/admin/sync/msuis/`
2. API data stored in APIEnrollment mirror table
3. Core tables auto-created/updated (Division, Student, Subject, StudentEnrollment)
4. Teachers use app to mark attendance (upload class photos)
5. System recognizes faces and marks attendance in AttendanceRecord
6. StudentAttendancePercentage automatically computed
7. Students see dashboard: Overall attendance + per-subject breakdown + by division/semester/year

---

## Database Diagrams

### Entity Relationship: Core Layer

```
Department
    ├─ Student
    ├─ Teacher
    ├─ Subject
    │   ├─ TeacherSubject
    │   └─ StudentEnrollment
    └─ Division
        └─ ClassSession
            ├─ AttendanceRecord
            │   └─ Student
            └─ AttendancePhotos
```

### Data Flow: API → Mirror → Core

```
MSUIS API
    ↓
APIFaculty, APIStudent, APIPaper, APIStudentAcademicInformation, APIStudentPartTermPaperMap
    ↓ (Projection with apply_to_core=true)
Department, Student, Subject, Division, StudentEnrollment
    ↓
ClassSession → AttendanceRecord → StudentAttendancePercentage
```

---

## Indexing Strategy

- **APIStudent.prn**: Primary key, used for lookups
- **APIStudentAcademicInformation.prn**: Indexed for joins
- **APIStudentPartTermPaperMap.prn**: Indexed for lookups
- **Student.face_embedding**: HNSW vector index for face recognition similarity search
- **AttendanceRecord**: Unique constraint (class_session, student)
- **StudentEnrollment**: Unique constraint (student_prn, subject)

---

## Access Patterns

### Admin Operations
```
POST /api/admin/sync/msuis/  → Populates all mirror tables → Projects to core tables
GET  /api/admin/divisions/    → Lists Division records
```

### Teacher Operations
```
POST /api/markAttendance      → Creates ClassSession with division → Creates AttendanceRecords
GET  /api/teacher/subjects/   → Lists Teacher's subjects via TeacherSubject
```

### Student Operations
```
POST /api/student/dashboard/  → Queries:
  - Student by prn
  - StudentEnrollment by student_prn
  - StudentAttendancePercentage per subject
  - AttendanceRecord recent activity
```

---

## Notes

1. **Mirror tables use MSUIS IDs as primary keys** — ensures idempotent upserts during sync
2. **Core tables use auto-increment IDs** — standard ClassLens references
3. **Division is unique by (dept, program, year, semester, name)** — prevents duplicates
4. **StudentAttendancePercentage is computed** — updated when attendance is marked
5. **face_embedding uses pgvector** — enables similarity-based student identification during attendance photo processing
6. **RABBITMQ_URL required in .env** — settings.py imports it at module load time

