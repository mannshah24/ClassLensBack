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

# Monkeypatch torchvision.transforms.functional_tensor before importing gfpgan/basicsr
module_name = 'torchvision.transforms.functional_tensor'
if F is not None:
    if module_name not in sys.modules:
        import sys, types
        functional_tensor_module = types.ModuleType(module_name)
        functional_tensor_module.rgb_to_grayscale = F.rgb_to_grayscale
        sys.modules[module_name] = functional_tensor_module

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

# Safe, device-agnostic fallback logic for GPU targeting
device = None
if torch is not None:
    try:
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    except Exception:
        device = 'cpu'

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
            bg_upsampler=None,
            device=device
        )
        print(f"GFPGAN restorer initialized with model: {model_path} on device: {device}")
    except Exception as e:
        print(f"Warning: GFPGAN restorer failed to initialize: {e}")
        restorer = None

    return restorer

def enhance_faces_batched(restorer, face_crops, weight=0.6):
    """
    Restore a batch of face crops in a single forward pass on the target device.
    Falls back to sequential processing on failure or if restorer is not available.
    """
    if not face_crops:
        return []

    if restorer is None:
        return face_crops

    import torch
    from basicsr.utils import img2tensor, tensor2img
    from torchvision.transforms.functional import normalize

    target_device = getattr(restorer, 'device', 'cpu')
    tensors = []
    
    try:
        for face in face_crops:
            # Resize crop to 512x512 as required by GFPGAN Clean architecture
            face_resized = cv2.resize(face, (512, 512))
            # Convert image to float tensor, normalize, and prepend channel dimension
            face_t = img2tensor(face_resized / 255.0, bgr2rgb=True, float32=True)
            normalize(face_t, (0.5, 0.5, 0.5), (0.5, 0.5, 0.5), inplace=True)
            tensors.append(face_t)
            
        # Stack all face tensors into a single batch: (Batch, Channel, Height, Width)
        batch_t = torch.stack(tensors).to(target_device)
        
        restored_faces = []
        with torch.no_grad():
            # GFPGAN forward pass
            outputs = restorer.gfpgan(batch_t, return_rgb=False, weight=weight)

            # Unpack outputs if it is a tuple (GFPGAN forward returns (restored_tensor, features))
            if isinstance(outputs, tuple):
                outputs = outputs[0]

            # Convert output tensors back to numpy images
            for i in range(outputs.size(0)):
                out_t = outputs[i]
                # Explicitly move to CPU for safety before passing to tensor2img
                out_t_cpu = out_t.cpu()
                restored_face = tensor2img(out_t_cpu, rgb2bgr=True, min_max=(-1, 1))
                restored_faces.append(restored_face.astype(np.uint8))

        return restored_faces
    except Exception as e:
        print(f"Warning: Batched GFPGAN inference failed: {e}. Falling back to sequential enhancement.")
        # Device-agnostic fallback: process sequentially using standard enhance method
        restored_faces = []
        for face in face_crops:
            try:
                _, restored, _ = restorer.enhance(
                    face,
                    has_aligned=True,
                    only_center_face=True,
                    paste_back=False,
                    weight=weight
                )
                if restored:
                    restored_faces.append(restored[0].astype(np.uint8))
                else:
                    restored_faces.append(face)
            except Exception as inner_e:
                print(f"GFPGAN enhancement fallback failed for face: {inner_e}")
                restored_faces.append(face)
        return restored_faces

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

    grouped_tokens = {
        True: [],
        False: [],
    }
    token_to_student = {}

    for student, is_present in student_records:
        token = (student.notification_token or "").strip()
        if token:
            grouped_tokens[is_present].append(token)
            token_to_student[token] = student

    for is_present, tokens in grouped_tokens.items():
        if not tokens:
            continue

        status_value = "present" if is_present else "absent"
        status_text = "Present" if is_present else "Absent"

        for start in range(0, len(tokens), 500):
            token_batch = tokens[start:start + 500]
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=f"Attendance Marked - {subject_name}",
                    body=f"You were marked {status_text} for the class on {class_datetime.strftime('%d %b %Y, %I:%M %p')}",
                ),
                data={
                    "type": "attendance",
                    "subject": subject_name,
                    "status": status_value,
                    "datetime": class_datetime.isoformat(),
                },
                android=messaging.AndroidConfig(
                    priority="high",
                    notification=messaging.AndroidNotification(
                        channel_id="attendance_channel",
                        default_sound=True,
                    ),
                ),
                tokens=token_batch,
            )

            try:
                response = messaging.send_each_for_multicast(message)
                print(
                    f"Attendance notifications sent for {subject_name} ({status_value}): "
                    f"{response.success_count} succeeded, {response.failure_count} failed"
                )

                for idx, send_response in enumerate(response.responses):
                    if send_response.success:
                        continue

                    token = token_batch[idx]
                    student = token_to_student.get(token)
                    error_code = getattr(send_response.exception, "code", "")
                    print(
                        f"Failed to send attendance notification to "
                        f"{student.name if student else 'unknown student'}: {send_response.exception}"
                    )

                    if error_code in {"registration-token-not-registered", "invalid-registration-token"} and student:
                        Student.objects.filter(
                            id=student.id,
                            notification_token=token,
                        ).update(notification_token=None)
            except Exception as e:
                print(f"Failed to send attendance notification batch for {subject_name} ({status_value}): {e}")

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
                android=messaging.AndroidConfig(
                    priority="high",
                    notification=messaging.AndroidNotification(
                        channel_id="attendance_channel",
                        default_sound=True,
                    ),
                ),
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
                android=messaging.AndroidConfig(
                    priority="high",
                    notification=messaging.AndroidNotification(
                        channel_id="attendance_channel",
                        default_sound=True,
                    ),
                ),
                token=teacher_token,
            )
            response = messaging.send(message)
            print(f"Notification sent to teacher: {response}")
        except Exception as e:
            print(f"Failed to send notification to teacher: {e}")

def load_and_detect_faces(image_path, max_dim=2560):
    from PIL import Image, ImageOps
    import numpy as np
    
    # 1. Load image using PIL and apply EXIF transpose to rotate upright based on sensor metadata
    try:
        pil_img = Image.open(image_path)
        pil_img = ImageOps.exif_transpose(pil_img)
        # Convert PIL to BGR NumPy array for OpenCV compatibility
        if pil_img.mode != "RGB":
            pil_img = pil_img.convert("RGB")
        img_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    except Exception as e:
        print(f"Error loading and transposing image {image_path}: {e}")
        # Fallback to direct OpenCV load if PIL fails
        img_bgr = cv2.imread(image_path)
        if img_bgr is None:
            return None, []

    # 2. Fast Orientation Auto-Detection comparison using low-resolution (800px) scans
    try:
        h, w = img_bgr.shape[:2]
        scale = 800.0 / max(h, w)
        img_preview = cv2.resize(img_bgr, (int(w * scale), int(h * scale)))
        
        # Scan orientation 1: 0 degrees (current)
        try:
            faces_0 = DeepFace.extract_faces(
                img_path=img_preview,
                detector_backend='retinaface',
                enforce_detection=True,
                align=True
            )
        except Exception:
            faces_0 = []
            
        # Scan orientation 2: 90 degrees clockwise (rotated)
        img_preview_90 = cv2.rotate(img_preview, cv2.ROTATE_90_CLOCKWISE)
        try:
            faces_90 = DeepFace.extract_faces(
                img_path=img_preview_90,
                detector_backend='retinaface',
                enforce_detection=True,
                align=True
            )
        except Exception:
            faces_90 = []
            
        print(f"Orientation comparison preview scan: 0° -> {len(faces_0)} faces, 90° CW -> {len(faces_90)} faces.")
        
        # If the 90-degree clockwise orientation detects strictly more faces, rotate original high-res image
        if len(faces_90) > len(faces_0):
            print("Winning orientation is 90° CW. Rotating original high-resolution image.")
            img_bgr = cv2.rotate(img_bgr, cv2.ROTATE_90_CLOCKWISE)
    except Exception as e:
        print(f"Error during preview orientation detection: {e}")

    # 3. Apply CLAHE contrast normalization to improve shadows / uneven lighting on winning orientation
    try:
        lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl_channel = clahe.apply(l_channel)
        limg = cv2.merge((cl_channel, a_channel, b_channel))
        processed_img = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
    except Exception as e:
        print(f"Failed to apply CLAHE: {e}")
        processed_img = img_bgr

    # 4. Resize to final high-resolution max_dim (preserving aspect ratio)
    h, w = processed_img.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        resized_img = cv2.resize(processed_img, (int(w * scale), int(h * scale)))
    else:
        resized_img = processed_img

    # 5. Run final high-resolution face detection
    try:
        final_face_data = DeepFace.extract_faces(
            img_path=resized_img,
            detector_backend='retinaface',
            enforce_detection=True,
            align=True
        )
    except Exception:
        final_face_data = []

    return resized_img, final_face_data


@shared_task(acks_late=True, reject_on_worker_lost=True)
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

        img_bgr, all_face_data = load_and_detect_faces(image_path, max_dim=2560)
        if img_bgr is None:
            continue

        total_faces += len(all_face_data)

        # Collect faces that need restoration in this image
        faces_to_enhance = []
        enhance_indices = []
        face_crops = []
        
        for idx, face_data in enumerate(all_face_data):
            face_crop_array = (face_data['face'] * 255).astype(np.uint8)
            face_crop_bgr = cv2.cvtColor(face_crop_array, cv2.COLOR_RGB2BGR)
            face_crops.append(face_crop_bgr)
            
            facial_area = face_data['facial_area']
            w, h = facial_area['w'], facial_area['h']
            
            gfpgan_min_face_size = getattr(settings, 'GFPGAN_MIN_FACE_SIZE', 80)
            if w < gfpgan_min_face_size or h < gfpgan_min_face_size:
                faces_to_enhance.append(face_crop_bgr)
                enhance_indices.append(idx)
                
        # Perform batched enhancement on the GPU if restorer is available
        _restorer = get_restorer()
        gfpgan_enhance_weight = getattr(settings, 'GFPGAN_ENHANCE_WEIGHT', 0.6)
        enhanced_faces = []
        if faces_to_enhance and _restorer is not None:
            enhanced_faces = enhance_faces_batched(_restorer, faces_to_enhance, weight=gfpgan_enhance_weight)
            
        # Map enhanced faces back to the list of face crops
        enhanced_map = {}
        if len(enhanced_faces) == len(enhance_indices):
            enhanced_map = {enhance_indices[i]: enhanced_faces[i] for i in range(len(enhance_indices))}
        else:
            print(f"Warning: Batch restoration returned {len(enhanced_faces)} faces but expected {len(enhance_indices)}. Skipping enhancement mapping.")

        for idx, face_data in enumerate(all_face_data):
            face_crop_bgr = face_crops[idx]
            facial_area = face_data['facial_area']
            x, y, w, h = facial_area['x'], facial_area['y'], facial_area['w'], facial_area['h']

            # Use enhanced face if available
            face_to_scan = enhanced_map[idx] if idx in enhanced_map else face_crop_bgr
            face_to_scan_rgb = cv2.cvtColor(face_to_scan, cv2.COLOR_BGR2RGB)

            # Read configurable settings
            face_rec_threshold = getattr(settings, 'FACE_RECOGNITION_THRESHOLD', 0.35)

            try:
                embedding_result = DeepFace.represent(
                    img_path=face_to_scan_rgb,
                    model_name='Facenet512',
                    detector_backend='skip',
                    enforce_detection=False,
                    align=False # Pre-aligned crop, avoid warp distortion
                )
                captured_embedding = embedding_result[0]['embedding']
                import math
                if not captured_embedding or any(math.isnan(val) or math.isinf(val) for val in captured_embedding):
                    raise ValueError("Captured embedding contains invalid non-finite values.")
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
                # print(prn)
                distance = cosine(known_emb, captured_embedding)
                if distance < best_score:
                    best_score = distance
                    best_prn = prn

            if best_score < face_rec_threshold:
                present_student_prns.add(best_prn)
                cv2.rectangle(img_bgr, (x, y), (x + w, y + h), (0, 255, 0), 2)
            else:
                # print(best_score)
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

    # Delete any duplicate records for this session in case of a celery task retry
    AttendanceRecord.objects.filter(class_session=session).delete()
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

@shared_task(acks_late=True, reject_on_worker_lost=True)
def evaluate_additional_attendance(class_session_id: int, new_photo_ids: list, scheme, host, division_id=None):
    import tensorflow as tf
    import torch

    print("="*60)
    print("TensorFlow GPU :", tf.config.list_physical_devices("GPU"))
    print("Torch CUDA     :", torch.cuda.is_available())

    if torch.cuda.is_available():
        print("Torch Device :", torch.cuda.get_device_name(0))

    print("="*60)

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
            
        img_bgr, all_face_data = load_and_detect_faces(image_path, max_dim=2560)
        if img_bgr is None:
            continue
            
        total_faces += len(all_face_data)
        
        # Collect faces that need restoration in this image
        faces_to_enhance = []
        enhance_indices = []
        face_crops = []
        
        for idx, face_data in enumerate(all_face_data):
            face_crop_array = (face_data['face'] * 255).astype(np.uint8)
            face_crop_bgr = cv2.cvtColor(face_crop_array, cv2.COLOR_RGB2BGR)
            face_crops.append(face_crop_bgr)
            
            facial_area = face_data['facial_area']
            w, h = facial_area['w'], facial_area['h']
            
            gfpgan_min_face_size = getattr(settings, 'GFPGAN_MIN_FACE_SIZE', 80)
            if w < gfpgan_min_face_size or h < gfpgan_min_face_size:
                faces_to_enhance.append(face_crop_bgr)
                enhance_indices.append(idx)
                
        # Perform batched enhancement on the GPU if restorer is available
        _restorer = get_restorer()
        gfpgan_enhance_weight = getattr(settings, 'GFPGAN_ENHANCE_WEIGHT', 0.6)
        enhanced_faces = []
        if faces_to_enhance and _restorer is not None:
            enhanced_faces = enhance_faces_batched(_restorer, faces_to_enhance, weight=gfpgan_enhance_weight)
            
        # Map enhanced faces back to the list of face crops
        enhanced_map = {}
        if len(enhanced_faces) == len(enhance_indices):
            enhanced_map = {enhance_indices[i]: enhanced_faces[i] for i in range(len(enhance_indices))}
        else:
            print(f"Warning: Batch restoration returned {len(enhanced_faces)} faces but expected {len(enhance_indices)}. Skipping enhancement mapping.")

        for idx, face_data in enumerate(all_face_data):
            face_crop_bgr = face_crops[idx]
            facial_area = face_data['facial_area']
            x, y, w, h = facial_area['x'], facial_area['y'], facial_area['w'], facial_area['h']

            # Use enhanced face if available
            face_to_scan = enhanced_map[idx] if idx in enhanced_map else face_crop_bgr
            face_to_scan_rgb = cv2.cvtColor(face_to_scan, cv2.COLOR_BGR2RGB)

            # Read configurable settings
            face_rec_threshold = getattr(settings, 'FACE_RECOGNITION_THRESHOLD', 0.35)

            try:
                embedding_result = DeepFace.represent(
                    img_path=face_to_scan_rgb,
                    model_name='Facenet512',
                    detector_backend='skip',
                    enforce_detection=False,
                    align=False # Pre-aligned crop, avoid warp distortion
                )
                captured_embedding = embedding_result[0]['embedding']
                import math
                if not captured_embedding or any(math.isnan(val) or math.isinf(val) for val in captured_embedding):
                    raise ValueError("Captured embedding contains invalid non-finite values.")
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
                # print(prn)
                distance = cosine(known_emb, captured_embedding)
                if distance < best_score:
                    best_score = distance
                    best_prn = prn
                    
            if best_score < face_rec_threshold:
                present_student_prns.add(best_prn)
                cv2.rectangle(img_bgr, (x, y), (x + w, y + h), (0, 255, 0), 2)
            else:
                # print(best_score)
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

@shared_task(
    bind=True,
    autoretry_for=(ConnectionError, OSError, Exception),
    retry_backoff=True,
    max_retries=3
)
def send_otp_email_task(self, email, subject, plain_message, html_message, from_email):
    from django.core.mail import send_mail
    import socket
    import smtplib
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=from_email,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )
        print(f"OTP email sent successfully to {email}")
        return True
    except Exception as e:
        print(f"Failed to send OTP email to {email}: {e}")
        # Log a helpful message warning about potential local antivirus or firewall blockages
        if isinstance(e, ConnectionAbortedError) or "10053" in str(e):
            print("Tip: WinError 10053 usually indicates that local antivirus software (e.g., Avast, Kaspersky) or a Windows Firewall rule is actively aborting outbound connections on SMTP ports like 587.")
        raise e

@shared_task
def process_student_face_embedding(student_prn, temp_image_path, is_registration, password=None):
    from .models import Student
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

@shared_task(name="Home.tasks.log_normal_task")
def log_normal_task(module, action, actor_id=None, actor_email=None, request_path="", ip_address=None, summary=""):
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO classlens_normal_log 
            (timestamp, module, action, actor_id, actor_email, request_path, ip_address, summary)
            VALUES (CURRENT_TIMESTAMP, %s, %s, %s, %s, %s, %s, %s)
            """,
            [module, action, actor_id, actor_email, request_path, ip_address, summary]
        )

@shared_task(name="Home.tasks.log_error_task")
def log_error_task(module, error_type, error_message, traceback_str, request_payload=None, actor_id=None):
    from django.db import connection
    import json
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO classlens_error_log
            (timestamp, module, error_type, error_message, traceback, request_payload, actor_id)
            VALUES (CURRENT_TIMESTAMP, %s, %s, %s, %s, %s, %s)
            """,
            [module, error_type, error_message, traceback_str, json.dumps(request_payload) if request_payload else None, actor_id]
        )

@shared_task(name="Home.tasks.cleanup_old_logs")
def cleanup_old_logs(days_to_keep=180):
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute(
            "DELETE FROM classlens_normal_log WHERE timestamp < NOW() - %s * INTERVAL '1 day'",
            [days_to_keep]
        )
        cursor.execute(
            "DELETE FROM classlens_error_log WHERE timestamp < NOW() - %s * INTERVAL '1 day'",
            [days_to_keep]
        )

from celery.signals import task_postrun

@task_postrun.connect
def on_task_postrun(sender, task_id, task, args, kwargs, retval, state, **extra_kwargs):
    if sender.name in ['Home.tasks.log_normal_task', 'Home.tasks.log_error_task', 'Home.tasks.cleanup_old_logs']:
        return

    from Home.db_logger import log_normal, log_error
    import traceback

    module = 'celery_worker'
    action = f"TASK_{sender.name.upper()}"
    
    actor_id = None
    for key in ['actor_id', 'user_id', 'student_id', 'teacher_id']:
        if key in kwargs:
            actor_id = kwargs[key]
            break

    if state == 'SUCCESS':
        summary = f"Celery task {sender.name} [{task_id}] succeeded."
        log_normal(
            module=module,
            action=action,
            actor_id=actor_id,
            actor_email=None,
            request_path=f"celery://tasks/{sender.name}",
            ip_address="127.0.0.1",
            summary=summary
        )
    else:
        error_message = str(retval) if retval else "Task failed"
        error_type = "CeleryTaskError"
        tb_str = ""
        
        if 'exception' in extra_kwargs:
            exc = extra_kwargs['exception']
            error_type = exc.__class__.__name__
            error_message = str(exc)
        
        if 'traceback' in extra_kwargs:
            tb_str = str(extra_kwargs['traceback'])
        elif hasattr(retval, 'traceback'):
            tb_str = str(retval.traceback)
            
        payload = {
            "task_id": task_id,
            "args": [str(a) for a in args],
            "kwargs": {k: str(v) for k, v in kwargs.items()}
        }
        
        log_error(
            module=module,
            error_type=error_type,
            error_message=error_message,
            traceback_str=tb_str or traceback.format_exc(),
            request_payload=payload,
            actor_id=actor_id
        )

