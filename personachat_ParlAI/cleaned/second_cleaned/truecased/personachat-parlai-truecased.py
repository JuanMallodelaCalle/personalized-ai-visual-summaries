import os
import re 


def normalize_ellipses(text):
    # replace ". .", ". . .", ". . . .", etc. with "..."
    text = re.sub(r'(\s*\.\s*){2,}', '...', text)

    # replace four or more dots with three dots
    text = re.sub(r'\.{4,}', '...', text)

    # remove space before "..."
    text = re.sub(r'\s+\.\.\.', '...', text)

    return text


def truecase_text(text):
    text = normalize_ellipses(text)

    # protect real ellipses
    text = text.replace('...', '__ELLIPSIS__')

    # basic punctuation and spacing cleanup
    text = re.sub(r'\s+([?.!,;:])', r'\1', text)
    text = re.sub(r'\s+', ' ', text).strip()

    # fix "i" contractions
    contractions = {
        "i'm": "I'm", "i've": "I've", "i'll": "I'll", "i'd": "I'd",
        "i am": "I am", "i have": "I have", "i will": "I will", "i would": "I would"
    }
    for wrong, correct in contractions.items():
        text = re.sub(rf'\b{wrong}\b', correct, text)

    text = re.sub(r'\bi\b', 'I', text)  # capitalize isolated "i"

    # split by sentences and capitalize each
    sentence_endings = re.split(r'([.?!])', text)
    sentences = []
    for i in range(0, len(sentence_endings) - 1, 2):
        sentence = sentence_endings[i].strip()
        punctuation = sentence_endings[i + 1]
        if sentence:
            sentence = sentence[0].upper() + sentence[1:]
        sentences.append(f"{sentence}{punctuation}")
    
    # handle dangling text without punctuation
    if len(sentence_endings) % 2 != 0:
        last = sentence_endings[-1].strip()
        if last and not last.endswith('__ELLIPSIS__'):
            last = last[0].upper() + last[1:]
            sentences.append(f"{last}.")
        else:
            # if it ends in __ELLIPSIS__, only capitalize previous part without adding extra dot
            last = last.replace('__ELLIPSIS__', '').strip()
            if last:
                last = last[0].upper() + last[1:]
                sentences.append(f"{last}__ELLIPSIS__")

    # restore ellipses, adding space if missing
    def restore_ellipsis(match):
        after = match.group(1)
        if after and not after.startswith((' ', '.', ',', '!', '?')):
            return '... ' + after
        return '...' + after

    result = ' '.join(sentences)
    result = re.sub(r'__ELLIPSIS__(\S*)', restore_ellipsis, result)

    return result


def apply_truecasing_clean(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as infile:
        lines = infile.readlines()

    output_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("Conversation"):
            output_lines.append(line)
        elif re.match(r'^\d+\s+(your persona|partner\'s persona):', stripped):
            # remove initial number and truecase
            prefix, content = re.sub(r'^\d+\s+', '', stripped).split(':', 1)
            cleaned = truecase_text(content)
            output_lines.append(f"{prefix}: {cleaned}\n")
        elif stripped.startswith(('YP:', 'PP:')):
            prefix, content = stripped.split(':', 1)
            # remove number if present (e.g., "YP: 12 text")
            content = re.sub(r'^\s*\d+\s*', '', content)
            cleaned = truecase_text(content)
            output_lines.append(f"{prefix}: {cleaned}\n")
        elif stripped == '':
            output_lines.append('\n')
        else:
            output_lines.append(line)

    with open(output_path, 'w', encoding='utf-8') as outfile:
        outfile.writelines(output_lines)


# paths
input_folder = "C:/Users/Juan/Desktop/TFM/personachat_ParlAI/cleaned/second_cleaned"
output_folder = "C:/Users/Juan/Desktop/TFM/personachat_ParlAI/cleaned/second_cleaned/truecased"
os.makedirs(output_folder, exist_ok=True)

for filename in os.listdir(input_folder):
    if filename.endswith(".txt"):
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, filename)
        apply_truecasing_clean(input_path, output_path)
        print(f"Processed file: {filename}")
