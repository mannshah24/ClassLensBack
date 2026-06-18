from celery import shared_task
import os
from rest_framework.response import Response
import uuid
from django.conf import settings
from django.http import request
from urllib.parse import urljoin
import numpy as np
from scipy.spatial.distance import cosine
import json
import sys, types
from django.db.models import F as DbF

# Optional heavy dependencies — import lazily or fall back to None so management commands work without them
try:
    import matplotlib.pyplot as plt
except Exception:
    plt = None
try:
    import cv2
except Exception:
    cv2 = None
try:
    from deepface import DeepFace
except Exception:
    DeepFace = None
try:
    import torch
except Exception:
    torch = None
try:
    import torchvision.transforms.functional as F
except Exception:
    F = None
try:
    import firebase_admin
    from firebase_admin import credentials, messaging
except Exception:
    firebase_admin = None
    credentials = None
    messaging = None
try:
    from gfpgan import GFPGANer
except Exception:
    GFPGANer = None

module_name = 'torchvision.transforms.functional_tensor'

if F is not None:
    if module_name not in sys.modules:
        functional_tensor_module = types.ModuleType(module_name)
        functional_tensor_module.rgb_to_grayscale = F.rgb_to_grayscale
        sys.modules[module_name] = functional_tensor_module

if torch is not None:
    _original_torch_load = torch.load

    def patched_torch_load(f, *args, **kwargs):
        if 'weights_only' not in kwargs:
            kwargs['weights_only'] = False
        return _original_torch_load(f, *args, **kwargs)

    torch.load = patched_torch_load

from .models import Student, AttendanceRecord, ClassSession, StudentEnrollment, StudentAttendancePercentage
from .utils import sync_student_subject_attendance
from django.utils import timezone

# Defer GFPGAN restorer initialization until a task runs to avoid import-time file access
restorer = None

def get_restorer():
    global restorer
    if restorer is not None:
        return restorer

    # If GFPGANer isn't available, skip initialization
    if GFPGANer is None:
        print("GFPGAN not available; skipping restorer initialization")
        return None

    model_path = None
    try:
        from django.conf import settings as _settings
        if hasattr(_settings, 'GFPGAN_MODEL_PATH') and _settings.GFPGAN_MODEL_PATH:
            model_path = _settings.GFPGAN_MODEL_PATH
        else:
            # default to BASE_DIR/GFPGANv1.4.pth
            model_path = str(_settings.BASE_DIR / 'GFPGANv1.4.pth')
    except Exception:
        model_path = 'GFPGANv1.4.pth'

    try:
        restorer = GFPGANer(
            model_path=model_path,
            upscale=2,
            arch='clean',
            channel_multiplier=2,
            bg_upsampler=None
        )
        print(f"GFPGAN restorer initialized with model: {model_path}")
    except Exception as e:
        print(f"Warning: GFPGAN restorer failed to initialize: {e}")
        restorer = None

    return restorer

def initialize_firebase():
    if firebase_admin is None or credentials is None:
        print("Firebase Admin SDK not available; skipping notifications")
        return

    if not firebase_admin._apps:
        cred_path = os.path.join(settings.BASE_DIR, 'firebase-service-account.json')
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print("Firebase Admin SDK initialized")
        else:
            print(f"Warning: Firebase credentials not found at {cred_path}")

def send_attendance_notifications(student_records, subject_name, class_datetime):
    """
    Send push notifications to all students with valid FCM tokens.
    """
    initialize_firebase()
    
    if not firebase_admin._apps:
        print("Firebase not initialized, skipping notifications")
        return
    
    for student, is_present in student_records:
        if student.notification_token:
            try:
                status_text = "Present ✓" if is_present else "Absent ✗"
                message = messaging.Message(
                    notification=messaging.Notification(
                        title=f"Attendance Marked - {subject_name}",
                        body=f"You were marked {status_text} for the class on {class_datetime.strftime('%d %b %Y, %I:%M %p')}",
                    ),
                    data={
                        "type": "attendance",
                        "subject": subject_name,
                        "status": "present" if is_present else "absent",
                        "datetime": class_datetime.isoformat(),
                    },
                    token=student.notification_token,
                )
                response = messaging.send(message)
                print(f"Notification sent to {student.name}: {response}")
            except Exception as e:
                print(f"Failed to send notification to {student.name}: {e}")

def send_student_registration_notification(student, is_success, message_body):
    """
    Send push notification to student confirming registration/face update status.
    """
    initialize_firebase()
    
    if firebase_admin is None or not firebase_admin._apps:
        print("Firebase not initialized, skipping student notifications")
        return
        
    if student.notification_token:
        try:
            title = "Face ID Registration Completed" if is_success else "Face ID Registration Failed"
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=message_body,
                ),
                data={
                    "type": "registration",
                    "status": "success" if is_success else "failure",
                },
                token=student.notification_token,
            )
            response = messaging.send(message)
            print(f"Notification sent to student {student.name}: {response}")
        except Exception as e:
            print(f"Failed to send notification to student {student.name}: {e}")

def send_teacher_attendance_notification(teacher_token, is_success, subject_name, present_count=0, absent_count=0, error_message=None):
    """
    Send push notification to teacher about attendance completion.
    """
    initialize_firebase()
    
    if firebase_admin is None or not firebase_admin._apps:
        print("Firebase not initialized, skipping teacher notifications")
        return
        
    if teacher_token:
        try:
            if is_success:
                title = f"Attendance Processed - {subject_name}"
                body = f"Attendance processing completed successfully. Present: {present_count}, Absent: {absent_count}."
            else:
                title = f"Attendance Failed - {subject_name}"
                body = f"Attendance processing failed. {error_message or 'Please try resubmitting.'}"
                
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data={
                    "type": "teacher_attendance",
                    "status": "success" if is_success else "failure",
                    "subject": subject_name,
                },
                token=teacher_token,
            )
            response = messaging.send(message)
            print(f"Notification sent to teacher: {response}")
        except Exception as e:
            print(f"Failed to send notification to teacher: {e}")

@shared_task
def evaluate_attendance(total_sessions, class_session_id: int, scheme, host, division_id=None):

    session = ClassSession.objects.get(id=class_session_id)
    images=session.photos.all()
    image_urls=[]
    total_faces=0

    enrolled_prns_qs = StudentEnrollment.objects.filter(
        subject=session.subject
    ).values_list('student_prn', flat=True)

    all_students_qs = Student.objects.filter(
        prn__in=enrolled_prns_qs,
        year=session.year,
        department=session.department,
    )
    if division_id:
        all_students_qs = all_students_qs.filter(division_id=division_id)

    enrolled_prns = list(all_students_qs.values_list('prn', flat=True))
    
    student_obj_map = {s.prn: s for s in all_students_qs}

    known_embeddings = {}
    for s in all_students_qs:
        if s.face_embedding is not None:
            emb = s.face_embedding
            if isinstance(emb, str):
                emb = json.loads(emb)
            known_embeddings[s.prn] = emb

    present_student_prns = set()
    output_dir = settings.MEDIA_ROOT / 'detected_photos'
    output_dir.mkdir(parents=True, exist_ok=True)

    for img_obj in images:
        image_path = img_obj.photo.path
        
        if not os.path.exists(image_path):
            continue

        img_bgr = cv2.imread(image_path)
        if img_bgr is None:
            continue

        try:
            all_face_data = DeepFace.extract_faces(
                img_path=img_bgr,
                detector_backend='retinaface',
                enforce_detection=True,
                align=True
            )
        except Exception:
            all_face_data = []

        total_faces += len(all_face_data)

        for face_data in all_face_data:
            face_crop_array = (face_data['face'] * 255).astype(np.uint8)
            face_crop_bgr = cv2.cvtColor(face_crop_array, cv2.COLOR_RGB2BGR)
            
            facial_area = face_data['facial_area']
            x, y, w, h = facial_area['x'], facial_area['y'], facial_area['w'], facial_area['h']

            _restorer = get_restorer()
            if _restorer is not None:
                try:
                    _, restored_list, _ = _restorer.enhance(
                        face_crop_bgr,
                        has_aligned=False,
                        only_center_face=True,
                        paste_back=False,
                        weight=0.1
                    )
                except Exception:
                    restored_list = []
            else:
                restored_list = []

            face_to_scan = restored_list[0] if restored_list else face_crop_bgr

            face_to_scan_rgb = cv2.cvtColor(face_to_scan, cv2.COLOR_BGR2RGB)

            try:
                embedding_result = DeepFace.represent(
                    img_path=face_to_scan_rgb,
                    model_name='Facenet512',
                    detector_backend='retinaface',
                    enforce_detection=False,
                    align=True
                )
                captured_embedding = embedding_result[0]['embedding']
            except Exception:
                if cv2 is not None:
                    try:
                        cv2.rectangle(img_bgr, (x, y), (x + w, y + h), (0, 0, 255), 2)
                    except Exception:
                        pass
                continue

            best_score = 1.0
            best_prn = None
            
            for prn, known_emb in known_embeddings.items():
                print(prn)
                distance = cosine(known_emb, captured_embedding)
                if distance < best_score:
                    best_score = distance
                    best_prn = prn

            if best_score < 0.4:
                present_student_prns.add(best_prn)
                cv2.rectangle(img_bgr, (x, y), (x + w, y + h), (0, 255, 0), 2)
            else:
                print(best_score)
                cv2.rectangle(img_bgr, (x, y), (x + w, y + h), (0, 0, 255), 2)

        unique_id = uuid.uuid4()
        filename = f"detected_{unique_id}.jpg"
        save_path = output_dir / filename
        cv2.imwrite(str(save_path), img_bgr)

        # Save path relative to MEDIA_ROOT in DB record
        img_obj.detected_photo = f"detected_photos/{filename}"
        img_obj.save()

        base_url = f"{scheme}://{host.rstrip('/')}"
        image_urls.append(urljoin(f"{base_url}/", f"media/detected_photos/{filename}"))

    records_to_create = []
    student_notification_list = [] 
    
    for prn in enrolled_prns:
        student_obj = student_obj_map.get(prn)
        if student_obj:
            is_present = prn in present_student_prns
            records_to_create.append(
                AttendanceRecord(
                    class_session=session,
                    student=student_obj,
                    status=is_present,
                    marked_at=timezone.now()
                )
            )
            
            student_notification_list.append((student_obj, is_present))

    AttendanceRecord.objects.bulk_create(records_to_create)

    # Sync cache percentages for all enrolled students
    for prn in enrolled_prns:
        student_obj = student_obj_map.get(prn)
        if student_obj:
            sync_student_subject_attendance(student_obj, session.subject)
    
    send_attendance_notifications(
        student_notification_list,
        session.subject.name,
        session.class_datetime
    )
    print(f"images url {image_urls[0] if image_urls else None}")

    return {
        "num_faces": total_faces,
        "image_url": image_urls[0] if image_urls else None,
        "image_urls": image_urls,
        "class_session_id": class_session_id,
        "division_id": division_id,
        "present_count": len(present_student_prns),
        "absent_count": len(enrolled_prns) - len(present_student_prns),
        "subject": session.subject.name
    }

@shared_task
def evaluate_additional_attendance(class_session_id: int, new_photo_ids: list, scheme, host, division_id=None):
    from .models import AttendancePhotos
    session = ClassSession.objects.get(id=class_session_id)
    new_images = AttendancePhotos.objects.filter(id__in=new_photo_ids)
    
    # Get all students currently marked as ABSENT for this session
    absent_records = AttendanceRecord.objects.filter(class_session=session, status=False)
    absent_student_ids = list(absent_records.values_list('student_id', flat=True))
    
    # We only care about students who are currently absent and enrolled
    all_students_qs = Student.objects.filter(id__in=absent_student_ids)
    
    # Map them by prn
    student_obj_map = {s.prn: s for s in all_students_qs}
    
    known_embeddings = {}
    for s in all_students_qs:
        if s.face_embedding is not None:
            emb = s.face_embedding
            if isinstance(emb, str):
                emb = json.loads(emb)
            known_embeddings[s.prn] = emb
            
    present_student_prns = set()
    output_dir = settings.MEDIA_ROOT / 'detected_photos'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    total_faces = 0
    image_urls = []
    
    for img_obj in new_images:
        image_path = img_obj.photo.path
        if not os.path.exists(image_path):
            continue
            
        img_bgr = cv2.imread(image_path)
        if img_bgr is None:
            continue
            
        try:
            all_face_data = DeepFace.extract_faces(
                img_path=img_bgr,
                detector_backend='retinaface',
                enforce_detection=True,
                align=True
            )
        except Exception:
            all_face_data = []
            
        total_faces += len(all_face_data)
        
        for face_data in all_face_data:
            face_crop_array = (face_data['face'] * 255).astype(np.uint8)
            face_crop_bgr = cv2.cvtColor(face_crop_array, cv2.COLOR_RGB2BGR)
            
            facial_area = face_data['facial_area']
            x, y, w, h = facial_area['x'], facial_area['y'], facial_area['w'], facial_area['h']
            
            _restorer = get_restorer()
            if _restorer is not None:
                try:
                    _, restored_list, _ = _restorer.enhance(
                        face_crop_bgr,
                        has_aligned=False,
                        only_center_face=True,
                        paste_back=False,
                        weight=0.1
                    )
                except Exception:
                    restored_list = []
            else:
                restored_list = []
                
            face_to_scan = restored_list[0] if restored_list else face_crop_bgr
            face_to_scan_rgb = cv2.cvtColor(face_to_scan, cv2.COLOR_BGR2RGB)
            
            try:
                embedding_result = DeepFace.represent(
                    img_path=face_to_scan_rgb,
                    model_name='Facenet512',
                    detector_backend='retinaface',
                    enforce_detection=False,
                    align=True
                )
                captured_embedding = embedding_result[0]['embedding']
            except Exception:
                if cv2 is not None:
                    try:
                        cv2.rectangle(img_bgr, (x, y), (x + w, y + h), (0, 0, 255), 2)
                    except Exception:
                        pass
                continue
                
            best_score = 1.0
            best_prn = None
            
            for prn, known_emb in known_embeddings.items():
                distance = cosine(known_emb, captured_embedding)
                if distance < best_score:
                    best_score = distance
                    best_prn = prn
                    
            if best_score < 0.4:
                present_student_prns.add(best_prn)
                cv2.rectangle(img_bgr, (x, y), (x + w, y + h), (0, 255, 0), 2)
            else:
                cv2.rectangle(img_bgr, (x, y), (x + w, y + h), (0, 0, 255), 2)
                
        unique_id = uuid.uuid4()
        filename = f"detected_{unique_id}.jpg"
        save_path = output_dir / filename
        cv2.imwrite(str(save_path), img_bgr)
        
        img_obj.detected_photo = f"detected_photos/{filename}"
        img_obj.save()
        
        base_url = f"{scheme}://{host.rstrip('/')}"
        image_urls.append(urljoin(f"{base_url}/", f"media/detected_photos/{filename}"))
        
    total_sessions = ClassSession.objects.filter(subject=session.subject).count()
    student_notification_list = []
    
    for prn in present_student_prns:
        student_obj = student_obj_map.get(prn)
        if student_obj:
            AttendanceRecord.objects.filter(
                class_session=session,
                student=student_obj
            ).update(status=True, marked_at=timezone.now())
            
            student_notification_list.append((student_obj, True))
            
            sync_student_subject_attendance(student_obj, session.subject)
            
    if student_notification_list:
        send_attendance_notifications(
            student_notification_list,
            session.subject.name,
            session.class_datetime
        )
        
    final_present_count = AttendanceRecord.objects.filter(class_session=session, status=True).count()
    final_absent_count = AttendanceRecord.objects.filter(class_session=session, status=False).count()
    
    return {
        "num_faces": total_faces,
        "image_url": image_urls[0] if image_urls else None,
        "image_urls": image_urls,
        "class_session_id": class_session_id,
        "division_id": division_id,
        "present_count": final_present_count,
        "absent_count": final_absent_count,
        "newly_marked_present_count": len(present_student_prns),
        "subject": session.subject.name
    }


@shared_task
def generate_daily_sessions(for_date_str=None, division_id=None):
    from datetime import date
    from django.db import transaction
    from .models import TimetableTemplate, DailySession, Holiday, Division
    from collections import defaultdict

    if for_date_str:
        target_date = date.fromisoformat(for_date_str)
    else:
        target_date = date.today()

    # Check for non-working holiday
    holiday = Holiday.objects.filter(date=target_date, is_working_day=False).first()
    if holiday:
        return f"Skipped: holiday '{holiday.name}' on {target_date}"

    with transaction.atomic():
        # Lock Division objects to serialize execution for the affected divisions
        if division_id is not None:
            if isinstance(division_id, (list, tuple, set)):
                division_ids = list(division_id)
                list(Division.objects.filter(id__in=division_ids).select_for_update())
                sessions_q = DailySession.objects.filter(date=target_date, division_id__in=division_ids)
            else:
                Division.objects.select_for_update().filter(id=division_id).first()
                sessions_q = DailySession.objects.filter(date=target_date, division_id=division_id)
        else:
            list(Division.objects.all().select_for_update())
            sessions_q = DailySession.objects.filter(date=target_date)

        # 1. Clean up exact duplicates (same subject, division, ui_order)
        seen = set()
        for session in list(sessions_q):
            key = (session.subject_id, session.division_id, session.ui_order)
            if key in seen:
                session.delete()
            else:
                seen.add(key)

        weekday = target_date.weekday()  # 0 = Monday, 6 = Sunday

        templates = TimetableTemplate.objects.filter(day_of_week=weekday)
        if division_id is not None:
            if isinstance(division_id, (list, tuple, set)):
                templates = templates.filter(division_id__in=division_id)
            else:
                templates = templates.filter(division_id=division_id)

        # Group templates by (subject_id, division_id)
        templates_by_key = defaultdict(list)
        for t in templates:
            key = (t.subject_id, t.division_id)
            templates_by_key[key].append(t)

        # Group existing sessions by (subject_id, division_id)
        sessions_by_key = defaultdict(list)
        for s in list(sessions_q):
            key = (s.subject_id, s.division_id)
            sessions_by_key[key].append(s)

        from .models import AttendanceRecord
        if division_id is not None:
            if isinstance(division_id, (list, tuple, set)):
                division_ids = list(division_id)
            else:
                division_ids = [division_id]
        else:
            division_ids = list(Division.objects.all().values_list('id', flat=True))

        marked_subject_ids = set(
            AttendanceRecord.objects.filter(
                student__division_id__in=division_ids,
                class_session__class_datetime__date=target_date
            ).values_list('class_session__subject_id', flat=True)
        )

        created = 0

        # A. Clean up stale sessions (subjects that are no longer in templates)
        for key, s_list in sessions_by_key.items():
            if key not in templates_by_key:
                for session in s_list:
                    # If it has no edits or attendance, delete it
                    has_attendance = session.subject_id in marked_subject_ids
                    if not session.is_cancelled and session.proxy_teacher_id is None and not has_attendance:
                        session.delete()

        # B. Sync existing sessions and create missing ones for active templates
        for key, t_list in templates_by_key.items():
            sub_id, div_id = key
            s_list = sessions_by_key.get(key, [])
            
            # Remove exact duplicates if any (same subject, division, ui_order)
            # which could cause counts to mismatch
            unique_sessions = []
            seen_ui_orders = set()
            for session in s_list:
                # If we see same ui_order twice, delete the second one
                if session.ui_order in seen_ui_orders:
                    # but only delete if it has no attendance/edits
                    has_attendance = session.subject_id in marked_subject_ids
                    if not session.is_cancelled and session.proxy_teacher_id is None and not has_attendance:
                        session.delete()
                    else:
                        unique_sessions.append(session)
                else:
                    seen_ui_orders.add(session.ui_order)
                    unique_sessions.append(session)
            
            existing_count = len(unique_sessions)
            template_count = len(t_list)

            # Sync fields of existing sessions to match templates
            for idx in range(min(existing_count, template_count)):
                session = unique_sessions[idx]
                template = t_list[idx]
                
                # Update fields if they changed in template
                updated = False
                if session.teacher_id != template.default_teacher_id and session.proxy_teacher_id is None:
                    session.teacher = template.default_teacher
                    updated = True
                if session.ui_order != template.ui_order:
                    session.ui_order = template.ui_order
                    updated = True
                if session.department_id != template.department_id:
                    session.department = template.department
                    updated = True
                if session.program != template.program:
                    session.program = template.program
                    updated = True
                if session.year != template.year:
                    session.year = template.year
                    updated = True
                if session.semester != template.semester:
                    session.semester = template.semester
                    updated = True
                if updated:
                    session.save()

            if existing_count > template_count:
                # Delete excess sessions if they are untouched
                for session in unique_sessions[template_count:]:
                    has_attendance = session.subject_id in marked_subject_ids
                    if not session.is_cancelled and session.proxy_teacher_id is None and not has_attendance:
                        session.delete()
            elif existing_count < template_count:
                # Create missing sessions
                needed = template_count - existing_count
                for i in range(needed):
                    template = t_list[existing_count + i]
                    DailySession.objects.create(
                        subject=template.subject,
                        date=target_date,
                        department=template.department,
                        program=template.program,
                        division=template.division,
                        year=template.year,
                        semester=template.semester,
                        teacher=template.default_teacher,
                        ui_order=template.ui_order
                    )
                    created += 1
                
    return f"Created {created} daily sessions for {target_date}"

@shared_task
def process_student_face_embedding(student_prn, temp_image_path, is_registration, password=None):
    from .models import Student
    from django.contrib.auth.hashers import make_password
    from .face_utils import extract_face_embedding
    import os

    try:
        student = Student.objects.get(prn=student_prn)
    except Student.DoesNotExist:
        if os.path.exists(temp_image_path):
            try:
                os.remove(temp_image_path)
            except Exception:
                pass
        return {"status": "FAILED", "error": f"Student with PRN {student_prn} not found."}

    try:
        if not os.path.exists(temp_image_path):
            raise ValueError("Temporary image file not found.")

        # Extract face embedding
        with open(temp_image_path, 'rb') as f:
            embedding = extract_face_embedding(f)
        
        student.face_embedding = [float(value) for value in embedding]
        
        if is_registration and password:
            student.password_hash = make_password(password)

        student.save()
        
        # Cleanup
        if os.path.exists(temp_image_path):
            os.remove(temp_image_path)

        # Notify
        msg = "Your face registration has been completed successfully." if is_registration else "Your face ID image has been updated successfully."
        send_student_registration_notification(student, is_success=True, message_body=msg)

        return {"status": "SUCCESS", "message": msg}

    except Exception as e:
        import traceback
        traceback.print_exc()
        if os.path.exists(temp_image_path):
            try:
                os.remove(temp_image_path)
            except Exception:
                pass
        
        err_msg = str(e)
        notify_msg = f"Registration/Face update failed: {err_msg}"
        send_student_registration_notification(student, is_success=False, message_body=notify_msg)
        raise e

from celery.signals import task_failure, task_success

@task_failure.connect
def on_task_failure(sender, task_id, exception, args, kwargs, traceback, einfo, **extra_kwargs):
    if sender.name in ['Home.tasks.evaluate_attendance', 'Home.tasks.evaluate_additional_attendance']:
        try:
            class_session_id = args[1] if sender.name == 'Home.tasks.evaluate_attendance' else args[0]
            session = ClassSession.objects.get(id=class_session_id)
            teacher_token = session.teacher.notification_token
            if teacher_token:
                send_teacher_attendance_notification(
                    teacher_token=teacher_token,
                    is_success=False,
                    subject_name=session.subject.name,
                    error_message="Attendance processing failed. Please try resubmitting."
                )
        except Exception as e:
            print(f"Error in failure signal handler: {e}")

@task_success.connect
def on_task_success(sender, result, **kwargs):
    if sender.name in ['Home.tasks.evaluate_attendance', 'Home.tasks.evaluate_additional_attendance']:
        try:
            class_session_id = result.get("class_session_id")
            session = ClassSession.objects.get(id=class_session_id)
            teacher_token = session.teacher.notification_token
            if teacher_token:
                send_teacher_attendance_notification(
                    teacher_token=teacher_token,
                    is_success=True,
                    subject_name=session.subject.name,
                    present_count=result.get("present_count", 0),
                    absent_count=result.get("absent_count", 0)
                )
        except Exception as e:
            print(f"Error in success signal handler: {e}")