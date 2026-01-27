import os
from collections import defaultdict

profile_dir = "C:/Users/Juan/Desktop/TFM/personachat_ParlAI/profiles"

files = [
    "train_both_original_profiles.txt",
    "train_both_revised_profiles.txt",
    "valid_both_original_profiles.txt",
    "valid_both_revised_profiles.txt",
    "test_both_original_profiles.txt",
    "test_both_revised_profiles.txt"
]

profile_occurrences = defaultdict(list)  # frozenset -> list of (file, dialogue_id, 'your' or 'partner')
file_profile_sets = defaultdict(set)  # filename -> set of frozenset (unique profiles in that file)

for filename in files:
    path = os.path.join(profile_dir, filename)
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    dialogue_id = None
    your_persona = []
    partner_persona = []

    for line in lines:
        line = line.strip()
        if line.startswith("Dialogue"):
            # save previous dialogue
            if your_persona:
                key = frozenset(your_persona)
                profile_occurrences[key].append((filename, dialogue_id, "your"))
                file_profile_sets[filename].add(key)
            if partner_persona:
                key = frozenset(partner_persona)
                profile_occurrences[key].append((filename, dialogue_id, "partner"))
                file_profile_sets[filename].add(key)

            # prepare new dialogue
            dialogue_id = int(line.split()[1])
            your_persona = []
            partner_persona = []

        elif "your persona:" in line:
            your_persona.append(line.split("your persona:")[1].strip())
        elif "partner's persona:" in line:
            partner_persona.append(line.split("partner's persona:")[1].strip())

    # save the last dialogue of the file
    if your_persona:
        key = frozenset(your_persona)
        profile_occurrences[key].append((filename, dialogue_id, "your"))
        file_profile_sets[filename].add(key)
    if partner_persona:
        key = frozenset(partner_persona)
        profile_occurrences[key].append((filename, dialogue_id, "partner"))
        file_profile_sets[filename].add(key)

# show duplicates
print("\nDuplicate profiles found:\n")
duplicates_found = False
for profile, locations in profile_occurrences.items():
    if len(locations) > 1:
        duplicates_found = True
        print("Duplicate profile:")
        for line in profile:
            print(f"  - {line}")
        print("Used in:")
        for loc in locations:
            print(f"  -> File: {loc[0]}, Dialogue: {loc[1]}, Type: {loc[2]}")
        print("-" * 60)

if not duplicates_found:
    print("No duplicate profiles found.")

# show total unique profiles per file
print("\nTotal unique profiles per file:")
for filename in files:
    print(f"{filename}: {len(file_profile_sets[filename])} unique profiles")
