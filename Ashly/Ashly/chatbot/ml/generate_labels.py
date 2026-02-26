import os
import json

# Ruta de tu dataset (ajústala si es necesario)
dataset_path = os.path.join("Ashly", "chatbot", "dataset")

labels = []

# Recorremos todas las carpetas de cultivos
for crop in sorted(os.listdir(dataset_path)):
    crop_path = os.path.join(dataset_path, crop)
    if os.path.isdir(crop_path):
        # Subcarpetas = enfermedades o plagas
        for disease in sorted(os.listdir(crop_path)):
            disease_path = os.path.join(crop_path, disease)
            if os.path.isdir(disease_path):
                labels.append(f"{crop}_{disease}")

# Guardamos las etiquetas en formato JSON
labels_path = os.path.join("Ashly", "chatbot", "ml", "labels.json")
with open(labels_path, "w", encoding="utf-8") as f:
    json.dump(labels, f, ensure_ascii=False, indent=4)

print("✅ Nuevo labels.json generado correctamente:")
print(labels)
