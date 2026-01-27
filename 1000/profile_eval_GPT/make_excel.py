import json
from pathlib import Path
import pandas as pd

# paths
input_dir = Path(r"C:/Users/Juan/Desktop/TFM/1000/profile_eval_GPT/Evaluated")
output_path = Path(r"C:/Users/Juan/Desktop/TFM/1000/profile_eval_GPT/profiles_gpt.xlsx")

# JSON reading
if not input_dir.exists():
    raise FileNotFoundError(f"Folder not found: {input_dir}")

files = sorted([p for p in input_dir.iterdir() if p.is_file() and p.suffix.lower() == ".json"])
print(f"JSON files found: {len(files)}")

if not files:
    raise RuntimeError("No JSON files found in the specific foulder.")

records = []

for p in files:
    try:
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        records.append({
            "User": "GPT-5",
            "Dialogue ID": data.get("dialogue_id", ""),
            "Profile": data.get("speaker", ""),
            "Profile Image": data.get("filename", ""),
            "Selected appearance(s)": data.get("ethnicity", ""),
            "Estimated age (profile)": data.get("age", ""),
            "Estimated sex (profile)": data.get("gender", ""),
        })
    except Exception as e:
        records.append({
            "User": "GPT-5",
            "Dialogue ID": "",
            "Profile": "",
            "Profile Image": p.name,
            "Selected appearance(s)": f"ERROR parsing JSON: {e}",
            "Estimated age (profile)": "",
            "Estimated sex (profile)": "",
        })

# dataframe creation and excel export
df = pd.DataFrame.from_records(records, columns=[
    "User",
    "Dialogue ID",
    "Profile",
    "Profile Image",
    "Selected appearance(s)",
    "Estimated age (profile)",
    "Estimated sex (profile)",
])

# save Excel file
output_path.parent.mkdir(parents=True, exist_ok=True)
with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
    df.to_excel(writer, index=False, sheet_name="Profiles")

print(f"Excel created successfully at: {output_path}")
print(f"Total rows (excluding header): {len(df)}  |  Total with header: {len(df) + 1}")
