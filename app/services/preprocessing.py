import cv2
import numpy as np
from PIL import Image
import io

def preprocess_image(image_bytes: bytes) -> np.ndarray:
    """
    Preprocess the uploaded leaf image:
    1. Decode bytes to numpy array
    2. Convert to RGB (if not already)
    3. Noise Removal (Gaussian Blur)
    4. Contrast Enhancement (Histogram Equalization on Y channel)
    5. Resize to 224x224
    6. Normalize pixel values (0-1)
    """
    # 1. Decode image from bytes
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        raise ValueError("Invalid image data")

    # 2. Convert BGR to RGB (OpenCV loads in BGR, we want RGB for most ML models)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # 3. Resize to 224x224
    img_resized = cv2.resize(img_rgb, (224, 224))

    # 4. Keep pixel values in [0, 255] to match training dataset loader
    img_normalized = img_resized.astype('float32')

    return img_normalized
