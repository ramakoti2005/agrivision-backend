import os
import json
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.applications import MobileNetV2

# Configuration
DATASET_DIR = "appdataset/PlantVillage"
MODEL_DIR = "app/ml_models"
MODEL_PATH = os.path.join(MODEL_DIR, "plant_disease_model.keras")
CLASS_NAMES_PATH = os.path.join(MODEL_DIR, "class_names.json")

IMG_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS = 5 # Use 5 epochs for reliable training; increase if needed.

def main():
    print(f"Loading dataset from {DATASET_DIR}...")
    
    if not os.path.exists(DATASET_DIR):
        print(f"Error: Dataset directory '{DATASET_DIR}' not found!")
        return

    # Ensure model directory exists
    os.makedirs(MODEL_DIR, exist_ok=True)

    # Load dataset
    train_ds = tf.keras.utils.image_dataset_from_directory(
        DATASET_DIR,
        validation_split=0.2,
        subset="training",
        seed=123,
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE
    )

    val_ds = tf.keras.utils.image_dataset_from_directory(
        DATASET_DIR,
        validation_split=0.2,
        subset="validation",
        seed=123,
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE
    )

    # Save class names for inference
    class_names = train_ds.class_names
    with open(CLASS_NAMES_PATH, "w") as f:
        json.dump(class_names, f)
    print(f"Saved {len(class_names)} classes to {CLASS_NAMES_PATH}")

    # Optimize dataset for performance (removed .cache() to prevent RAM crashing)
    AUTOTUNE = tf.data.AUTOTUNE
    train_ds = train_ds.shuffle(100).prefetch(buffer_size=AUTOTUNE)
    val_ds = val_ds.prefetch(buffer_size=AUTOTUNE)

    # Data augmentation
    data_augmentation = tf.keras.Sequential([
        layers.RandomFlip("horizontal_and_vertical"),
        layers.RandomRotation(0.2),
    ])

    print("Building MobileNetV2 model...")
    # Use MobileNetV2 as the base model
    base_model = MobileNetV2(
        input_shape=(224, 224, 3),
        include_top=False,
        weights='imagenet'
    )
    # Freeze the base model
    base_model.trainable = False

    # Create new model on top
    inputs = tf.keras.Input(shape=(224, 224, 3))
    x = data_augmentation(inputs)
    # MobileNetV2 expects pixel values in [-1, 1], but dataset loads [0, 255]
    x = tf.keras.applications.mobilenet_v2.preprocess_input(x)
    x = base_model(x, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(0.2)(x)
    outputs = layers.Dense(len(class_names))(x)

    model = models.Model(inputs, outputs)

    model.compile(
        optimizer='adam',
        loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
        metrics=['accuracy']
    )

    model.summary()

    print(f"Starting training for {EPOCHS} epochs...")
    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=EPOCHS
    )

    print(f"Training complete. Saving model to {MODEL_PATH}...")
    model.save(MODEL_PATH)
    print("Model saved successfully!")

if __name__ == "__main__":
    main()
