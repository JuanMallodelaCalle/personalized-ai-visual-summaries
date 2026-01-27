import os
import json


def parse_conversation_block_swapped(block_lines, conv_id):
    partner_persona = []
    your_persona = []
    dialogue = []

    for line in block_lines:
        line = line.strip()

        if line.startswith("partner's persona:"):
            partner_persona.append(line.replace("partner's persona:", "").strip())

        elif line.startswith("your persona:"):
            your_persona.append(line.replace("your persona:", "").strip())

        elif line.startswith("PP:"):
            dialogue.append({
                "persona_id": f"persona_chat_{conv_id}_A",
                "text": line.replace("PP:", "").strip()
            })

        elif line.startswith("YP:"):
            dialogue.append({
                "persona_id": f"persona_chat_{conv_id}_B",
                "text": line.replace("YP:", "").strip()
            })

    return {
        "dialogue_id": f"persona_chat_{conv_id}",
        "persona": {
            f"persona_chat_{conv_id}_A": partner_persona,
            f"persona_chat_{conv_id}_B": your_persona,
        },
        "dialogue": dialogue
    }


def convert_txt_to_json_swapped(txt_path, json_path):
    with open(txt_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    all_data = []
    current_block = []
    conv_id = 1

    for line in lines:
        if line.strip().startswith("Conversation"):
            if current_block:
                parsed = parse_conversation_block_swapped(current_block, conv_id)
                all_data.append(parsed)
                current_block = []
                conv_id += 1
        else:
            current_block.append(line)

    # process the last block
    if current_block:
        parsed = parse_conversation_block_swapped(current_block, conv_id)
        all_data.append(parsed)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=4)

    print(f"Saved {len(all_data)} conversations to: {json_path}")


# paths
input_folder = "C:/Users/Juan/Desktop/TFM/personachat_ParlAI/cleaned/second_cleaned/truecased"
output_folder = "C:/Users/Juan/Desktop/TFM/personachat_ParlAI/cleaned/second_cleaned/truecased/json"

os.makedirs(output_folder, exist_ok=True)

# process all .txt files
for filename in os.listdir(input_folder):
    if filename.endswith(".txt"):
        txt_path = os.path.join(input_folder, filename)
        json_filename = filename.replace(".txt", ".json")
        json_path = os.path.join(output_folder, json_filename)
        convert_txt_to_json_swapped(txt_path, json_path)
