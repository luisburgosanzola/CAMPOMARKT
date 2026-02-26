import os, shutil
import tensorflow_datasets as tfds
import tensorflow as tf

OUT_DIR = os.path.join(os.path.dirname(__file__), "dataset_plantvillage")
os.makedirs(OUT_DIR, exist_ok=True)

ds_train, info = tfds.load("plant_village", split="train", with_info=True, as_supervised=True)
labels = info.features["label"].names

print("Clases:", len(labels))

for i, (img, label) in enumerate(tfds.as_numpy(ds_train)):
    class_name = labels[int(label)]
    class_dir = os.path.join(OUT_DIR, class_name)
    os.makedirs(class_dir, exist_ok=True)

    # guardar como jpg
    path = os.path.join(class_dir, f"{i}.jpg")
    tf.keras.utils.save_img(path, img)

print("✅ Dataset listo en:", OUT_DIR)
