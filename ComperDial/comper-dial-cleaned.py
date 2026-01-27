import json
import re


def clean_persona_sentence(sentence):
    # remove extra spaces
    sentence = sentence.strip()

    # unify multiple dots at the end
    sentence = re.sub(r'\.{2,}$', '.', sentence)

    # remove dot after "in the past/future" incorrectly separated
    sentence = re.sub(r'\.\s+(in the (past|future))', r' \1', sentence, flags=re.IGNORECASE)

    # fix capitalization after colons
    sentence = re.sub(r'(:\s*)([a-z])', lambda m: m.group(1) + m.group(2).capitalize(), sentence)

    # ensure final period if missing
    if not sentence.endswith(('.', '!', '?')):
        sentence += '.'

    return sentence


def clean_comperdial_personas(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for entry in data:
        for key in entry['persona']:
            cleaned = [clean_persona_sentence(s) for s in entry['persona'][key]]
            entry['persona'][key] = cleaned

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"Cleaned file saved at: {output_path}")


# usage
input_path = "C:/Users/Juan/Desktop/TFM/ComperDial/ComperDial_data_truecased.json"
output_path = "C:/Users/Juan/Desktop/TFM/ComperDial/ComperDial_data_cleaned.json"
clean_comperdial_personas(input_path, output_path)
