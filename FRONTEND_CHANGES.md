# Frontend Changes Required - ClassLens Attendance System

## Summary
Backend schema updated to support:
- **Division** model (department-level grouping)
- **API mirror tables** for MSUIS data ingestion
- **Overall + per-subject attendance** in student dashboard

This document outlines all frontend changes needed to work with the new backend API contract.

---

## 1. Admin App Changes

### 1.1 Division Management (New Feature)
**Location:** Admin Dashboard → Division Management

**New CRUD Endpoint:**
```
GET    /api/admin/divisions/           - List all divisions
POST   /api/admin/divisions/           - Create division
GET    /api/admin/divisions/{id}/      - Get division details
PUT    /api/admin/divisions/{id}/      - Update division
DELETE /api/admin/divisions/{id}/      - Delete division
```

**Form Fields (for Create/Edit):**
- `department` (ForeignKey) - dropdown, required
- `program_name` (CharField) - e.g., "B.E Computer Science"
- `year` (IntegerField) - 1, 2, 3, 4
- `semester` (IntegerField) - 1-8
- `name` (CharField) - e.g., "A", "B", "C" (division code)

**UI Changes:**
- Add "Divisions" menu item in admin sidebar
- Show table with columns: Department, Program, Year, Semester, Name
- Add "Add Division", "Edit", "Delete" buttons
- Validation: unique constraint on (department, program_name, year, semester, name)

### 1.2 MSUIS Data Sync (New Feature)
**Location:** Admin Dashboard → Data Management → Sync MSUIS

**New Endpoint:**
```
POST /api/admin/sync/msuis/
Content-Type: application/json

Request Payload:
{
  "faculties": [
    { "Id": 1, "FacultyName": "CS Dept", "IsActive": 1, ... }
  ],
  "students": [
    { "PRN": 2021001, "FirstName": "John", "LastName": "Doe", 
      "EmailId": "john@example.com", "FacultyId": 1, "Year": 2, ... }
  ],
  "papers": [
    { "Id": 10, "PaperCode": "CS101", "PaperName": "Data Structures", 
      "SubjectId": 10, ... }
  ],
  "student_academic_information": [
    { "Id": 100, "PRN": 2021001, "FacultyId": 1, "AcademicYearId": 2025, ... }
  ],
  "student_part_term_paper_maps": [
    { "Id": 1000, "PRN": 2021001, "PaperId": 10, "Division": "A", 
      "Semester": 3, ... }
  ],
  "apply_to_core": true
}

Response (200 OK):
{
  "message": "MSUIS payload synced via admin app",
  "apply_to_core": true,
  "counts": {
    "faculties_synced": 1,
    "students_synced": 100,
    "papers_synced": 50,
    "academic_records_synced": 150,
    "part_term_maps_synced": 500,
    "core_departments_upserted": 1,
    "core_students_upserted": 100,
    "core_subjects_upserted": 50,
    "core_enrollments_upserted": 500,
    "core_divisions_upserted": 10
  }
}
```

**UI Changes:**
- Add "Sync MSUIS Data" section in admin
- Large JSON text area to paste API payload (or file upload button for JSON)
- Toggle: "Apply to Core Tables" (default: checked)
- "Sync" button → POST to /api/admin/sync/msuis/
- Show results: success/failure count, summary of upserted records
- Optional: Show mirror table counts (APIFaculty, APIStudent, etc.)

---

## 2. Teacher App / Mark Attendance Changes

### 2.1 Mark Attendance Form Update
**Location:** Teacher Dashboard → Mark Attendance

**New Field Added:**
- **Division** (Dropdown, required)
  - Fetch from: `GET /api/admin/divisions/` filtered by teacher's department
  - Or fetch from: `GET /api/admin/subject-from-dept/?department={dept}&year={year}&semester={semester}`
  - Display as: "Division: [A / B / C / ...]"

**Request Update:**
```javascript
// Old request (multipart)
POST /api/markAttendance
{
  photo: [file1, file2, ...],
  subjectID: 5,
  teacherID: 12,
  departmentName: "CSE",
  year: 2
}

// New request (multipart) - ADD divisionID
POST /api/markAttendance
{
  photo: [file1, file2, ...],
  subjectID: 5,
  teacherID: 12,
  departmentName: "CSE",
  year: 2,
  divisionID: 3  // NEW - division ID
}
```

**UI Changes:**
1. In the mark attendance form, add a Division dropdown **after** the Subject field
2. Populate division dropdown when subject is selected:
   ```
   GET /api/admin/divisions/?department={teacher_dept}&year={selected_year}
   ```
   Display: option value=division.id, text=division.name
3. Make divisionID required (validate before submit)
4. Send `divisionID` in the multipart POST request

**Example HTML:**
```html
<form id="markAttendanceForm" enctype="multipart/form-data">
  <select name="subjectID" id="subject" required>
    <option>Select Subject</option>
    <!-- populated from getSubjects endpoint -->
  </select>

  <!-- NEW -->
  <select name="divisionID" id="division" required>
    <option>Select Division</option>
    <!-- populated dynamically on subject change -->
  </select>

  <input type="file" name="photo" multiple required />
  <button type="submit">Mark Attendance</button>
</form>
```

---

## 3. Student App / Dashboard Changes

### 3.1 Student Dashboard Update
**Location:** Student Dashboard / Home

**Endpoint Update (same endpoint, enhanced response):**
```
POST /api/student/dashboard/
{
  "student_id": 1
}

Response (200 OK):
{
  "student_name": "John Doe",
  "prn": 2021001,
  "overall_attendance": 85.5,  // NEW - weighted average across all subjects
  "subjects": [
    {
      "id": 5,
      "name": "Data Structures",
      "code": "CS101",
      "teacher": "Dr. Smith",
      "total": 20,           // total classes held for this subject
      "attended": 17,        // classes attended by student
      "percentage": 85.0     // (attended / total) * 100
    },
    {
      "id": 6,
      "name": "Algorithms",
      "code": "CS102",
      "teacher": "Dr. Johnson",
      "total": 18,
      "attended": 15,
      "percentage": 83.33
    }
  ],
  "recent_activity": [
    {
      "subject": "Data Structures",
      "status": "Present",
      "date": "2026-05-10T14:30:00Z"
    },
    ...
  ]
}
```

**UI Changes:**

#### 3.1.1 Overall Attendance Summary Card (NEW)
Add a card/section at the top of dashboard:
```
┌─────────────────────────────────┐
│ Overall Attendance              │
│                                 │
│        85.5%                    │
│  ████████████░░░░░░░░░░░░░░░░   │ (progress bar)
│                                 │
│ Across 4 subjects               │
└─────────────────────────────────┘
```

**Implementation:**
- Display `response.overall_attendance` as percentage
- Show progress bar (green if >= 75%, yellow if >= 60%, red if < 60%)
- Optional: Show "Across X subjects" subtitle

#### 3.1.2 Per-Subject Attendance List
Keep existing subject cards but enhance:

```
┌─────────────────────────────────────────────┐
│ Data Structures (CS101)                      │
│ Teacher: Dr. Smith                           │
├─────────────────────────────────────────────┤
│ Attendance: 17/20 (85%)                     │
│ ████████████░░░░░░░░░░░░░░░░                │
├─────────────────────────────────────────────┤
│ • 3 classes missed                          │
└─────────────────────────────────────────────┘
```

**Changes:**
- Display `teacher` name (from response)
- Show `attended` and `total` (e.g., "17/20")
- Show `percentage` as progress bar color-coded:
  - **Green**: >= 75% (good attendance)
  - **Yellow**: 60-74% (warning)
  - **Red**: < 60% (at risk)
- Calculate missed = total - attended, display

#### 3.1.3 Recent Activity Feed
Keep existing; displayed below subjects.

---

## 4. API Contract Summary

### New/Updated Endpoints

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| GET | `/api/admin/divisions/` | List divisions | Yes |
| POST | `/api/admin/divisions/` | Create division | Yes |
| GET | `/api/admin/divisions/{id}/` | Get division | Yes |
| PUT | `/api/admin/divisions/{id}/` | Update division | Yes |
| DELETE | `/api/admin/divisions/{id}/` | Delete division | Yes |
| POST | `/api/admin/sync/msuis/` | Sync MSUIS payload | Yes |
| POST | `/api/markAttendance` | Mark attendance (UPDATED) | No |
| POST | `/api/student/dashboard/` | Student dashboard (UPDATED) | No |

### Field Additions
- `ClassSession.division` (ForeignKey to Division) - now passed from mark_attendance
- Student Dashboard response: `overall_attendance` (float, optional)
- Mark Attendance request: `divisionID` (integer, optional but recommended)

---

## 5. Implementation Checklist

### Admin App
- [ ] Create Division CRUD form/page
- [ ] Add Division menu item to sidebar
- [ ] Create MSUIS sync page with JSON textarea
- [ ] POST payload to /api/admin/sync/msuis/
- [ ] Display sync results

### Teacher App
- [ ] Add Division dropdown to mark attendance form
- [ ] Load divisions on subject selection
- [ ] Validate division is selected
- [ ] Send `divisionID` in mark attendance POST

### Student App
- [ ] Add overall_attendance card at top of dashboard
- [ ] Style progress bars (green/yellow/red)
- [ ] Display teacher name for each subject
- [ ] Show attended/total counts
- [ ] Keep recent activity feed

---

## 6. Testing Checklist

- [ ] Create test admin account and login
- [ ] Create 2-3 divisions via admin UI
- [ ] Test mark attendance with division selection
- [ ] Verify ClassSession.division is saved
- [ ] Check student dashboard shows overall_attendance
- [ ] Verify per-subject percentages calculate correctly
- [ ] Test MSUIS sync payload import
- [ ] Verify mirror tables populated (APIStudent, APIFaculty, etc.)
- [ ] Verify core tables updated (Student, Subject, Division, etc.)

---

## 7. Notes

1. **Division is optional in mark_attendance**: If not sent, ClassSession.division will be NULL. For full functionality, always send divisionID.
2. **Overall attendance is weighted**: Calculated as (total_attended / total_classes) * 100 across all enrolled subjects.
3. **MSUIS sync is admin-only**: Use JWT auth with admin user.
4. **Mirror tables** (APIStudent, APIFaculty, etc.) store raw API data; core tables (Student, Subject, Division) store operational data. Sync can populate either or both.
