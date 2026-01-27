import json
import re

# input and output files
input_file = "ComperDial_data_formatted.json"
output_file = "ComperDial_data_truecased.json"


def truecase_sentence(text):
    # remove spaces before punctuation and capitalize
    text = re.sub(r"\s+([.,!?])", r"\1", text)
    text = text.strip()
    if text:
        text = text[0].upper() + text[1:]
    return text


def truecase_persona_list(persona_list):
    return [truecase_sentence(p) for p in persona_list]


# load data
with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

# apply truecasing to personas
for item in data:
    persona = item["persona"]
    for speaker_id in list(persona.keys()):
        persona[speaker_id] = truecase_persona_list(persona[speaker_id])

# save new file
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4)

print(f"File saved as {output_file} with improved personas.")
