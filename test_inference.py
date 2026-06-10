import os
import sys
import numpy as np
import cv2
from app.services.inference import run_inference, model, class_names
from app.services.preprocessing import preprocess_image

print("Model loaded?", model is not None)
print("Classes loaded:", len(class_names))

# Test on Corn image
img_path = "appdataset/PlantVillage/Corn_Common_Rust/RS_Rust 1562.JPG"
if not os.path.exists(img_path):
    corn_dir = "appdataset/PlantVillage/Corn_Common_Rust"
    if os.path.exists(corn_dir):
        files = os.listdir(corn_dir)
        if files:
            img_path = os.path.join(corn_dir, files[0])

print("Testing on image:", img_path)

if os.path.exists(img_path):
    with open(img_path, "rb") as f:
        img_bytes = f.read()
    
    preprocessed = preprocess_image(img_bytes)
    
    # Try direct prediction to inspect logits
    if model is not None:
        input_tensor = np.expand_dims(preprocessed, axis=0)
        predictions = model.predict(input_tensor)
        import tensorflow as tf
        probs = tf.nn.softmax(predictions[0]).numpy()
        
        print("Top 5 Probabilities:")
        top_5_idx = np.argsort(probs)[-5:][::-1]
        for idx in top_5_idx:
            print(f"{class_names[idx]}: {probs[idx]*100:.2f}%")
    else:
        print("Model is not loaded. Skipping direct model predictions and inspecting fallback response instead.")
        
    try:
        response = run_inference(preprocessed)
        print("Inference response:", response)
    except Exception as e:
        print("Error during inference:", e)
else:
    print("Test image not found.")
