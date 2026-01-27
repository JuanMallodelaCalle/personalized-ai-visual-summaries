import os
import re
import json

# paths
INPUT_TXT_FOLDER = r"C:/Users/Juan/Desktop/TFM/1000/out_profile_images_prompts/response"
EXTENDED_JSON_FOLDER = r"C:/Users/Juan/Desktop/TFM/1000/out_profile_extension/response_clean" # to get dialogue_id (response_clean)
OUTPUT_FOLDER = r"C:/Users/Juan/Desktop/TFM/1000/out_profile_images_prompts/prompts_images"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# utilities
FNAME_RE = re.compile(r"^prompt_(\d+)\.txt$", re.IGNORECASE)

def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def extract_prompts(txt: str):
    """
    Extracts a_prompt and b_prompt from the text.
    Handles multiline prompts.
    Returns dict {'A': '...', 'B': '...'} or raises valueerror.
    """
    s = txt.strip()

    a_match = re.search(r"A_PROMPT:\s*(.+?)(?:\n\s*\n|$)", s, flags=re.DOTALL | re.IGNORECASE)
    b_match = re.search(r"B_PROMPT:\s*(.+?)(?:\n\s*\n|$)", s, flags=re.DOTALL | re.IGNORECASE)

    if not a_match or not b_match:
        raise ValueError("No se pudo extraer A_PROMPT y/o B_PROMPT.")

    a_prompt = a_match.group(1).strip()
    b_prompt = b_match.group(1).strip()

    if not a_prompt or not b_prompt:
        raise ValueError("A_PROMPT o B_PROMPT vacío.")

    return {"A": a_prompt, "B": b_prompt}


def dialogue_id_for_n(n: int) -> str | None:
    """
    Reads response_clean/prompt_n.json to find its dialogue_id.
    """
    json_name = f"prompt_{n}.json"
    json_path = os.path.join(EXTENDED_JSON_FOLDER, json_name)

    if not os.path.exists(json_path):
        return None

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        did = data.get("dialogue_id")
        return did if isinstance(did, str) and did.strip() else None
    except Exception:
        return None


def write_persona_json(out_path: str, persona_id: str, prompt_text: str):
    obj = {
        "persona_id": persona_id,
        "prompt": prompt_text
    }
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def main():
    files = [f for f in os.listdir(INPUT_TXT_FOLDER) if f.lower().endswith(".txt")]
    files = sorted(files, key=lambda x: (FNAME_RE.match(x) is None, x))  # sort by number inside filename

    total = 0
    skipped = []

    for fname in files:
        m = FNAME_RE.match(fname)
        if not m:
            # not in format prompt_n.txt -> skip
            skipped.append(fname)
            continue

        n = int(m.group(1))
        in_path = os.path.join(INPUT_TXT_FOLDER, fname)

        try:
            txt = read_text(in_path)
            prompts = extract_prompts(txt)

            # retrieve dialogue_id from the extended json
            did = dialogue_id_for_n(n)

            # if dialogue_id is missing, fallback to prompt_n_a
            pid_A = f"{did}_A" if did else f"prompt_{n}_A"
            pid_B = f"{did}_B" if did else f"prompt_{n}_B"

            # define output paths (prompt_n_a.json / prompt_n_b.json)
            # keeping file naming consistent with input number for traceability
            out_A = os.path.join(OUTPUT_FOLDER, f"prompt_{n}_A.json")
            out_B = os.path.join(OUTPUT_FOLDER, f"prompt_{n}_B.json")

            write_persona_json(out_A, pid_A, prompts["A"])
            write_persona_json(out_B, pid_B, prompts["B"])

            total += 2

        except Exception as e:
            print(f"[ERROR] {fname}: {e}")

    print(f"Generated {total} JSON files in '{OUTPUT_FOLDER}'.")
    if skipped:
        print(f"Alert: {len(skipped)} files ignored no 'prompt_N.txt'.")

if __name__ == "__main__":
    main()
