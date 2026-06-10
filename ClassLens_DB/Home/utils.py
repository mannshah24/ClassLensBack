from django.db import transaction
from django.db.models import Count, Q

def sync_student_subject_attendance(student, subject):
    """
    Recalculate and update the StudentAttendancePercentage cache record for a specific student and subject.
    """
    from Home.models import AttendanceRecord, StudentAttendancePercentage
    
    total_sessions = AttendanceRecord.objects.filter(
        student=student,
        class_session__subject=subject
    ).count()
    present_count = AttendanceRecord.objects.filter(
        student=student, 
        class_session__subject=subject, 
        status=True
    ).count()
    
    attendance_percentage = 0.0
    if total_sessions > 0:
        attendance_percentage = (present_count * 100.0) / total_sessions
        
    sap, created = StudentAttendancePercentage.objects.update_or_create(
        student=student,
        subject=subject,
        defaults={
            "present_count": present_count,
            "attendancePercentage": attendance_percentage
        }
    )
    return sap

def sync_all_attendance_percentages():
    """
    Perform a highly efficient bulk synchronization of all enrollments
    with the StudentAttendancePercentage cache table.
    """
    from Home.models import Student, StudentEnrollment, StudentAttendancePercentage, AttendanceRecord
    
    # 1. Map student PRN to Student objects
    students = {s.prn: s for s in Student.objects.all()}
    
    # 2. Get all enrollments
    enrollments = StudentEnrollment.objects.all()
    
    # 3. Get existing StudentAttendancePercentage objects mapped by (student_id, subject_id)
    existing_saps = {
        (sap.student_id, sap.subject_id): sap 
        for sap in StudentAttendancePercentage.objects.all()
    }
    
    # 4. Aggregate attendance records (total recorded sessions, present count)
    attendance_summary = {}
    records = AttendanceRecord.objects.values('student_id', 'class_session__subject_id').annotate(
        total=Count('id'),
        present=Count('id', filter=Q(status=True))
    )
    for r in records:
        key = (r['student_id'], r['class_session__subject_id'])
        attendance_summary[key] = (r['total'], r['present'])
        
    saps_to_create = []
    saps_to_update = []
    
    for enrollment in enrollments:
        student = students.get(enrollment.student_prn)
        if not student:
            continue
        
        subject = enrollment.subject
        key = (student.id, subject.id)
        
        total_sessions, present_count = attendance_summary.get(key, (0, 0))
        
        attendance_percentage = 0.0
        if total_sessions > 0:
            attendance_percentage = (present_count * 100.0) / total_sessions
            
        sap = existing_saps.get(key)
        if sap is None:
            saps_to_create.append(
                StudentAttendancePercentage(
                    student=student,
                    subject=subject,
                    present_count=present_count,
                    attendancePercentage=attendance_percentage
                )
            )
        else:
            if sap.present_count != present_count or abs(sap.attendancePercentage - attendance_percentage) > 0.01:
                sap.present_count = present_count
                sap.attendancePercentage = attendance_percentage
                saps_to_update.append(sap)
                
    if saps_to_create or saps_to_update:
        with transaction.atomic():
            if saps_to_create:
                StudentAttendancePercentage.objects.bulk_create(saps_to_create)
            if saps_to_update:
                StudentAttendancePercentage.objects.bulk_update(saps_to_update, ['present_count', 'attendancePercentage'])
