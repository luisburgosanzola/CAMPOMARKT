import os
import shutil

# Ruta base del proyecto (donde está este script)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Carpeta original: ml/dataset (cultivo/plaga)
DATASET_SRC = os.path.join(BASE_DIR, 'Ashly', 'chatbot', 'ml', 'dataset')

# Carpeta destino: ml/dataset_flat (clase = cultivo_plaga)
DATASET_FLAT = os.path.join(BASE_DIR, 'Ashly', 'chatbot', 'ml', 'dataset_flat')

os.makedirs(DATASET_FLAT, exist_ok=True)

for crop_name in os.listdir(DATASET_SRC):
    crop_path = os.path.join(DATASET_SRC, crop_name)
    if not os.path.isdir(crop_path):
        continue

    for disease_name in os.listdir(crop_path):
        disease_path = os.path.join(crop_path, disease_name)
        if not os.path.isdir(disease_path):
            continue

        # nombre de la clase: cultivo_plaga (todo en minúscula y sin espacios)
        class_name = f"{crop_name}_{disease_name}".lower().replace(" ", "_")
        class_dir = os.path.join(DATASET_FLAT, class_name)
        os.makedirs(class_dir, exist_ok=True)

        for fname in os.listdir(disease_path):
            src_file = os.path.join(disease_path, fname)
            if not os.path.isfile(src_file):
                continue

            dst_file = os.path.join(class_dir, fname)
            # copiamos la imagen si no existe ya
            if not os.path.exists(dst_file):
                shutil.copy2(src_file, dst_file)

print("✅ dataset_flat creado en:", DATASET_FLAT)
