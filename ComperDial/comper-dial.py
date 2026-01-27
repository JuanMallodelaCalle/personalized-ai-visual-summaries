import json

# path to the original input file
input_file = 'ComperDial_data.json'
output_file = 'ComperDial_data_formatted.json'

# load original data
with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

formatted_data = []

# process each dialogue
for idx, entry in enumerate(data, start=1):
    dialogue_id = f"comper_dial_{idx}"
    
    # get profiles and reorder
    persona_a = entry['persona']['A']
    persona_b = entry['persona']['B']

    formatted_persona = {
        f"{dialogue_id}_A": persona_a,
        f"{dialogue_id}_B": persona_b
    }

    # update persona ids in dialogue turns
    formatted_dialogue = []
    for turn in entry['dialogue']:
        old_id = turn['persona_id']
        new_id = f"{dialogue_id}_{old_id}"
        formatted_dialogue.append({
            "persona_id": new_id,
            "text": turn['text']
        })

    # assemble formatted entry
    formatted_entry = {
        "dialogue_id": dialogue_id,
        "persona": formatted_persona,
        "dialogue": formatted_dialogue
    }

    formatted_data.append(formatted_entry)

# save formatted file
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(formatted_data, f, indent=4)

print(f"File saved as '{output_file}' with {len(formatted_data)} dialogues.")
