try:
    from deepface import DeepFace
except Exception:
    DeepFace = None

try:
    from PIL import Image
except Exception:
    Image = None

import numpy as np


def extract_face_embedding(photo):
    if not photo:
        raise ValueError("No photo uploaded")

    if DeepFace is None:
        raise ValueError("Face embedding dependencies are unavailable")

    if Image is None:
        raise ValueError("Face image processing dependencies are unavailable")

    try:
        if hasattr(photo, "seek"):
            photo.seek(0)

        image = Image.open(photo)
        image = image.convert("RGB")
        img_arr = np.array(image)

        image_embedding = DeepFace.represent(
            img_path=img_arr,
            model_name="Facenet512",
            detector_backend="ssd",
            enforce_detection=True,
        )[0]["embedding"]

        return [float(value) for value in image_embedding]
    except ValueError as exc:
        raise ValueError(str(exc)) from exc
    except Exception as exc:
        raise ValueError(f"Face Not Detected, Upload A New Image: {exc}") from exc