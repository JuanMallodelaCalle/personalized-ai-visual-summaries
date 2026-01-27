import os
import json
import shutil
import time

# paths
base_path = "C:/Users/Juan/Desktop/TFM/1000/out_profile_images_prompts"
images_folder = os.path.join(base_path, "images")
json_folder = os.path.join(base_path, "prompts_images")
target_folder = os.path.join(base_path, "images_with_ids")

os.makedirs(target_folder, exist_ok=True)

# process from 1 to 1000
for i in range(1, 1001):
    for suffix in ["A", "B"]:
        img_filename = f"prompt_{i}_{suffix}.png"
        json_filename = f"prompt_{i}_{suffix}.json"

        img_path = os.path.join(images_folder, img_filename)
        json_path = os.path.join(json_folder, json_filename)

        try:
            # read json to get persona_id
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                persona_id = data.get("persona_id")

            if not persona_id:
                print(f"No se encontró 'persona_id' en {json_filename}")
                continue

            # create new image name
            new_img_filename = f"{persona_id}.png"
            target_img_path = os.path.join(target_folder, new_img_filename)

            # copy image with new name
            shutil.copyfile(img_path, target_img_path)
            print(f"{img_filename} → {new_img_filename}")

        except Exception as e:
            print(f"Error con {img_filename}: {e}")

    # wait 1 second between pairs
    time.sleep(1)

print("images renamed in 'images_with_ids'")
