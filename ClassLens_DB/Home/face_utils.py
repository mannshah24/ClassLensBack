try:
    from deepface import DeepFace
except Exception:
    DeepFace = None

try:
    from PIL import Image
except Exception:
    Image = None

import math
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

        # Primary extraction using RetinaFace backend
        try:
            image_embedding = DeepFace.represent(
                img_path=img_arr,
                model_name="Facenet512",
                detector_backend="retinaface",
                enforce_detection=True,
            )[0]["embedding"]

            # Validate that the embedding is clean and has finite numbers
            if not image_embedding or any(math.isnan(val) or math.isinf(val) for val in image_embedding):
                raise ValueError("Embedding contains invalid NaN or non-finite values.")
        except Exception as exc:
            # Friendly instruction message for user
            raise ValueError(
                "Face registration failed. Please ensure your photo:\n"
                "1. Has good lighting.\n"
                "2. You are looking directly at the camera.\n"
                "3. The image is clear and not blurry.\n"
                "4. Only one face is visible in the frame.\n"
                "Please try capturing or uploading a different photo."
            ) from exc

        return [float(value) for value in image_embedding]
    except ValueError as exc:
        raise ValueError(str(exc)) from exc
    except Exception as exc:
        raise ValueError(f"Face Not Detected, Upload A New Image: {exc}") from exc