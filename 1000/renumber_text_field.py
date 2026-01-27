import json
import os


def rename_texts(input_path, output_path):
    # load data
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for dialogue in data:
        new_turns = []
        for i, turn in enumerate(dialogue["dialogue"], start=1):
            new_turn = {
                "persona_id": turn["persona_id"],
                f"text_{i}": turn["text"]
            }
            new_turns.append(new_turn)
        dialogue["dialogue"] = new_turns

    # save data
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# input and output paths
input_outputs = [
    ("C:/Users/Juan/Desktop/TFM/ComperDial/ComperDial_data_cleaned.json", "ComperDial_Mallo.json"),
    ("C:/Users/Juan/Desktop/TFM/personachat_ParlAI/cleaned/second_cleaned/truecased/json/train_both_revised.json", "PersonaChat_Mallo.json")
]

for input_file, output_file in input_outputs:
    if os.path.exists(input_file):
        print(f"Processing {input_file}...")
        rename_texts(input_file, output_file)
        print(f"Saved as {output_file}")
    else:
        print(f"File not found: {input_file}")
