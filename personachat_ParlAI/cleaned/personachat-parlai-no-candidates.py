import os
import re

# input and output directories
input_folder = "C:/Users/Juan/Desktop/TFM/personachat_ParlAI"
output_folder = "C:/Users/Juan/Desktop/TFM/personachat_ParlAI/cleaned"
os.makedirs(output_folder, exist_ok=True)

# files to process
filenames = [
    "test_both_original.txt",
    "test_both_revised.txt",
    "train_both_original.txt",
    "train_both_revised.txt",
    "valid_both_original.txt",
    "valid_both_revised.txt"
]

# pattern to identify profile lines
profile_pattern = re.compile(r"^\d+\s+(your persona|partner's persona):")


def clean_dialogue_line(line):
    # try splitting by tab
    if '\t' in line:
        parts = line.split('\t')[:2]
    else:
        # if no tabs, split by multiple spaces
        parts = re.split(r'\s{2,}', line)[:2]
    return '\t'.join(parts).strip()


# process per file
for filename in filenames:
    input_path = os.path.join(input_folder, filename)
    output_path = os.path.join(output_folder, filename)

    with open(input_path, "r", encoding="utf-8") as infile:
        lines = infile.readlines()

    output_lines = []
    buffer = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue  # skip empty lines

        if stripped.startswith("1 your persona:") or stripped.startswith("1 partner's persona:"):
            # new block detected: process the previous one
            if buffer:
                profiles_partner = [l for l in buffer if "partner's persona:" in l]
                profiles_your = [l for l in buffer if "your persona:" in l]
                dialogue = [l for l in buffer if not profile_pattern.match(l)]
                output_lines.extend(profiles_partner + profiles_your + dialogue + ["\n"])
                buffer = []
        
        buffer.append(stripped)

    # process last block if buffer is not empty
    if buffer:
        profiles_partner = [l for l in buffer if "partner's persona:" in l]
        profiles_your = [l for l in buffer if "your persona:" in l]
        dialogue = [l for l in buffer if not profile_pattern.match(l)]
        output_lines.extend(profiles_partner + profiles_your + dialogue + ["\n"])

    # save file
    with open(output_path, "w", encoding="utf-8") as outfile:
        for line in output_lines:
            if profile_pattern.match(line):
                outfile.write(line + "\n")
            else:
                cleaned_line = clean_dialogue_line(line)
                if cleaned_line:
                    outfile.write(cleaned_line + "\n")
