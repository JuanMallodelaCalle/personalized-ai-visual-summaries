import os
import json
import time

# paths
source_folder = "C:/Users/Juan/Desktop/TFM/1000/out_profile_extension/response_clean"
target_folder = os.path.join(source_folder, "../dialogue_ids")

os.makedirs(target_folder, exist_ok=True)

# process files from 1 to 1000
for i in range(1, 1001):
    filename = f"prompt_{i}.json"
    source_path = os.path.join(source_folder, filename)

    # read file and extract dialogue_id
    try:
        with open(source_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            dialogue_id = data.get("dialogue_id")

        if not dialogue_id:
            print(f"[WARN] No 'dialogue_id' found in {filename}")
            continue

        # create new name and path
        new_filename = f"{dialogue_id}.json"
        target_path = os.path.join(target_folder, new_filename)

        # save with new name
        with open(target_path, "w", encoding="utf-8") as out_f:
            json.dump(data, out_f, ensure_ascii=False, indent=4)

        print(f"Renamed {filename} → {new_filename}")

        # delay 1 sec
        time.sleep(1)

    except Exception as e:
        print(f"[ERROR] Processing {filename}: {e}")

print("All files have been renamed and copied to 'dialogue_ids'.")
