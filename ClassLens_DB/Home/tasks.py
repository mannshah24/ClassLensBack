from celery import shared_task
import matplotlib.pyplot as plt
import cv2
import os
from rest_framework.response import Response
from deepface import DeepFace
import uuid
import torch
from django.conf import settings
from django.http import request
import numpy as np
from scipy.spatial.distance import cosine
import json
import sys, types
import torchvision.transforms.functional as F
from django.db.models import F as DbF
import firebase_admin
from firebase_admin import credentials, messaging

module_name = 'torchvision.transforms.functional_tensor'

if module_name not in sys.modules:
    functional_tensor_module = types.ModuleType(module_name)
    functional_tensor_module.rgb_to_grayscale = F.rgb_to_grayscale
    sys.modules[module_name] = functional_tensor_module

_original_torch_load = torch.load

def patched_torch_load(f, *args, **kwargs):
    if 'weights_only' not in kwargs:
        kwargs['weights_only'] = False
    return _original_torch_load(f, *args, **kwargs)

torch.load = patched_torch_load

from gfpgan import GFPGANer
from .models import Student, AttendanceRecord, ClassSession, StudentEnrollment, StudentAttendancePercentage

restorer = GFPGANer(
    model_path='GFPGANv1.4.pth',
    upscale=2,
    arch='clean',
    channel_multiplier=2,
    bg_upsampler=None
)

def initialize_firebase():
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

@shared_task
def evaluate_attendance(total_sessions,class_session_id:int,scheme, host):

    session = ClassSession.objects.get(id=class_session_id)
    images=session.photos.all()
    image_urls=[]
    total_faces=0

    enrolled_prns = list(StudentEnrollment.objects.filter(
        subject=session.subject
    ).values_list('student_prn', flat=True))

    all_students_qs = Student.objects.filter(prn__in=enrolled_prns)
    
    student_obj_map = {s.prn: s for s in all_students_qs}

    known_embeddings = {}
    for s in all_students_qs:
        if s.face_embedding is not None:
            emb = s.face_embedding
            if isinstance(emb, str):
                emb = json.loads(emb)
            known_embeddings[s.prn] = emb

    present_student_prns = set()
    output_dir = settings.MEDIA_ROOT / 'images'
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

            _, restored_list, _ = restorer.enhance(
                face_crop_bgr,
                has_aligned=False,
                only_center_face=True,
                paste_back=False,
                weight=0.1
            )
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
            except ValueError:
                cv2.rectangle(img_bgr, (x, y), (x + w, y + h), (0, 0, 255), 2)
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
        
        image_urls.append(f"{scheme}://{host}/media/images/{filename}")

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
                    marked_at=session.class_datetime
                )
            )
            
            student_notification_list.append((student_obj, is_present))

            StudentAttendancePercentage.objects.filter(
                student=student_obj,
                subject=session.subject
            ).update(present_count=DbF('present_count') + (1 if is_present else 0))

            StudentAttendancePercentage.objects.filter(
                student=student_obj,
                subject=session.subject
            ).update(attendancePercentage=(DbF('present_count')*100.0)/total_sessions)

    AttendanceRecord.objects.bulk_create(records_to_create)
    
    send_attendance_notifications(
        student_notification_list,
        session.subject.name,
        session.class_datetime
    )
    print(f"images url {image_urls[0]}")

    return {
        "num_faces": total_faces,
        "image_url": image_urls[0] if image_urls else None,
        "class_session_id": class_session_id,
        "present_count": len(present_student_prns),
        "absent_count": len(enrolled_prns) - len(present_student_prns),
        "subject": session.subject.name
    }