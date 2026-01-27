import os

# input and output paths
input_dir = "C:/Users/Juan/Desktop/TFM/personachat_ParlAI"
output_dir = "C:/Users/Juan/Desktop/TFM/personachat_ParlAI/profiles"
os.makedirs(output_dir, exist_ok=True)

files = [
    "train_both_original.txt",
    "train_both_revised.txt",
    "valid_both_original.txt",
    "valid_both_revised.txt",
    "test_both_original.txt",
    "test_both_revised.txt"
]

for filename in files:
    input_path = os.path.join(input_dir, filename)
    output_path = os.path.join(output_dir, filename.replace(".txt", "_profiles.txt"))

    with open(input_path, "r", encoding="utf-8") as infile, open(output_path, "w", encoding="utf-8") as outfile:
        dialogue_id = 1
        current_profile_lines = []

        for line in infile:
            line = line.strip()

            if not line:
                continue

            if "your persona:" in line or "partner's persona:" in line:
                current_profile_lines.append(line)
            else:
                if current_profile_lines:
                    outfile.write(f"Dialogue {dialogue_id} profiles:\n")
                    for profile_line in current_profile_lines:
                        outfile.write(f"{profile_line}\n")
                    outfile.write("\n")
                    current_profile_lines = []
                    dialogue_id += 1

        # last block if the file does not end in a dialogue
        if current_profile_lines:
            outfile.write(f"Dialogue {dialogue_id} profiles:\n")
            for profile_line in current_profile_lines:
                outfile.write(f"{profile_line}\n")
            outfile.write("\n")
