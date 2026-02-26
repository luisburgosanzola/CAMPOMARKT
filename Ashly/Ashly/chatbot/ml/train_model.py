import os
import json
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

# =========================
# CONFIG
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATASET_DIR = os.path.join(BASE_DIR, "dataset")  # carpeta dataset/ (por carpetas)
MODEL_OUT = os.path.join(BASE_DIR, "plant_disease_model.h5")
LABELS_OUT = os.path.join(BASE_DIR, "labels.json")

IMG_SIZE = (224, 224)
BATCH_SIZE = 32
SEED = 42

EPOCHS_HEAD = 8          # entreno solo la “cabeza”
EPOCHS_FINE = 10         # fine-tuning
LR_HEAD = 1e-3
LR_FINE = 1e-5

# =========================
# VALIDACIONES
# =========================
if not os.path.isdir(DATASET_DIR):
    raise FileNotFoundError(f"No existe DATASET_DIR: {DATASET_DIR}")

# =========================
# DATASETS (train/val split)
# =========================
train_ds = tf.keras.utils.image_dataset_from_directory(
    DATASET_DIR,
    validation_split=0.2,
    subset="training",
    seed=SEED,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    label_mode="int",
)

val_ds = tf.keras.utils.image_dataset_from_directory(
    DATASET_DIR,
    validation_split=0.2,
    subset="validation",
    seed=SEED,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    label_mode="int",
)

class_names = train_ds.class_names
num_classes = len(class_names)

print(f"✅ Clases detectadas: {num_classes}")
print(class_names)

# Guardar labels.json
with open(LABELS_OUT, "w", encoding="utf8") as f:
    json.dump(class_names, f, ensure_ascii=False, indent=2)
print(f"✅ labels.json guardado en: {LABELS_OUT}")

# Performance
AUTOTUNE = tf.data.AUTOTUNE
train_ds = train_ds.shuffle(1000, seed=SEED).prefetch(AUTOTUNE)
val_ds = val_ds.prefetch(AUTOTUNE)

# =========================
# DATA AUGMENTATION (clave)
# =========================
data_augmentation = keras.Sequential(
    [
        layers.RandomFlip("horizontal"),
        layers.RandomRotation(0.08),
        layers.RandomZoom(0.10),
        layers.RandomContrast(0.10),
    ],
    name="data_augmentation",
)

# =========================
# MODEL: EfficientNetB0
# =========================
base_model = tf.keras.applications.EfficientNetB0(
    include_top=False,
    input_shape=(IMG_SIZE[0], IMG_SIZE[1], 3),
    weights="imagenet",
)
base_model.trainable = False  # primero congelado

inputs = keras.Input(shape=(IMG_SIZE[0], IMG_SIZE[1], 3))
x = data_augmentation(inputs)
x = tf.keras.applications.efficientnet.preprocess_input(x)
x = base_model(x, training=False)
x = layers.GlobalAveragePooling2D()(x)
x = layers.Dropout(0.35)(x)
outputs = layers.Dense(num_classes, activation="softmax")(x)

model = keras.Model(inputs, outputs)

# =========================
# TRAIN HEAD
# =========================
model.compile(
    optimizer=keras.optimizers.Adam(LR_HEAD),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"],
)

callbacks = [
    keras.callbacks.EarlyStopping(
        monitor="val_accuracy",
        patience=3,
        restore_best_weights=True,
    ),
    keras.callbacks.ReduceLROnPlateau(
        monitor="val_loss",
        factor=0.5,
        patience=2,
        min_lr=1e-6,
    ),
]

print("🚀 Entrenando HEAD (base congelada)...")
history_head = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=EPOCHS_HEAD,
    callbacks=callbacks,
)

# =========================
# FINE TUNING (descongelar final)
# =========================
base_model.trainable = True

# congelar las primeras capas, entrenar solo las últimas (estabilidad)
fine_tune_at = int(len(base_model.layers) * 0.7)
for layer in base_model.layers[:fine_tune_at]:
    layer.trainable = False

model.compile(
    optimizer=keras.optimizers.Adam(LR_FINE),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"],
)

print("🔥 Fine-tuning (últimas capas de EfficientNet)...")
history_fine = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=EPOCHS_HEAD + EPOCHS_FINE,
    initial_epoch=history_head.epoch[-1] + 1 if history_head.epoch else 0,
    callbacks=callbacks,
)

# =========================
# SAVE
# =========================
model.save(MODEL_OUT)
print(f"✅ Modelo guardado en: {MODEL_OUT}")

# Evaluación final
val_loss, val_acc = model.evaluate(val_ds)
print(f"📌 Val accuracy final: {val_acc:.4f}")
