import json
import random

# input paths
comperdial_path = "C:/Users/Juan/Desktop/TFM/finales/ComperDial_Mallo.json"
personachat_path = "C:/Users/Juan/Desktop/TFM/finales/PersonaChat_Mallo.json"

# output path
output_path = "C:/Users/Juan/Desktop/TFM/1000/1000_Mallo.json"

# load datasets
with open(comperdial_path, "r", encoding="utf-8") as f:
    comper_data = json.load(f)

with open(personachat_path, "r", encoding="utf-8") as f:
    personachat_data = json.load(f)

# select random samples
comper_sample = random.sample(comper_data, 100)
personachat_sample = random.sample(personachat_data, 900)

# combine and save
combined = comper_sample + personachat_sample
random.shuffle(combined)  # shuffle to interleave

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(combined, f, ensure_ascii=False, indent=4)

print(f"File created: {output_path} with {len(combined)} samples.")
