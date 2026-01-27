import os
import re


def clean_formatted_dialogues(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    conversations = []
    current_your_persona = []
    current_partner_persona = []
    current_dialogue = []
    in_dialogue = False
    conversation_id = 1

    def save_conversation():
        nonlocal conversation_id
        if not current_your_persona and not current_partner_persona and not current_dialogue:
            return
        conversation_text = [f"Conversation {conversation_id}"]
        conversation_text += current_partner_persona + [""]
        conversation_text += current_your_persona + [""]
        conversation_text += current_dialogue + [""]
        conversations.append("\n".join(conversation_text))
        conversation_id += 1

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # check if it is a profile line
        if 'your persona:' in stripped or "partner's persona:" in stripped:
            if in_dialogue:
                save_conversation()
                current_your_persona = []
                current_partner_persona = []
                current_dialogue = []
                in_dialogue = False

            if 'your persona:' in stripped:
                current_your_persona.append(stripped)
            else:
                current_partner_persona.append(stripped)

        # check if it is a conversation line
        else:
            in_dialogue = True
            # split by tab or multiple spaces
            split_match = re.split(r'\t+|\s{2,}', stripped)
            if len(split_match) == 2:
                current_dialogue.append(f"PP: {split_match[0].strip()}")
                current_dialogue.append(f"YP: {split_match[1].strip()}")

    # save the last conversation
    save_conversation()

    # write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(conversations))


# usage example
input_folder = "C:/Users/Juan/Desktop/TFM/personachat_ParlAI/cleaned"
output_folder = "C:/Users/Juan/Desktop/TFM/personachat_ParlAI/cleaned/second_cleaned"

os.makedirs(output_folder, exist_ok=True)

for filename in os.listdir(input_folder):
    if filename.endswith(".txt"):
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, filename)
        clean_formatted_dialogues(input_path, output_path)
        print(f"Processed: {filename}")
