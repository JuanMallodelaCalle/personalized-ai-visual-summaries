import os
import json
import re

# paths
INPUT_FOLDER  = r"C:/Users/Juan/Desktop/TFM/1000/out_visual_turns/response"
OUTPUT_FOLDER = r"C:/Users/Juan/Desktop/TFM/1000/out_visual_turns/response_clean"
ERROR_FOLDER  = r"C:/Users/Juan/Desktop/TFM/1000/out_visual_turns/errors_response"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(ERROR_FOLDER, exist_ok=True)

# utility to clean markdown code blocks
FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)


def strip_fences(s: str) -> str:
    return FENCE_RE.sub("", s).strip()


def extract_json_block(text: str):
    """Attempts to find a valid json block within the text."""
    text = strip_fences(text)
    # 1) if it is already valid json:
    try:
        return json.loads(text)
    except Exception:
        pass

    # 2) find first '{' and last '}' and try with that snippet:
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        snippet = text[start:end+1]
        try:
            return json.loads(snippet)
        except Exception:
            return None
    return None


def clean_json_content(raw_text: str) -> str:
    """Fixes common formatting errors and returns indented json text."""
    fixed = raw_text.replace('\r', '')  # normalize CRLF
    fixed = fixed.strip()

    before = None
    # apply regex in a loop until text stabilizes
    while before != fixed:
        before = fixed

        # A) typical case: comma after string and right before closing object -> remove it
        #    ... "prompt":"text",}
        fixed = re.sub(r'("\s*),\s*}', r'\1}', fixed)

        # B) variant: comma + "" right before closing } or ]
        fixed = re.sub(r',\s*""\s*([\]}])', r'\1', fixed)

        # C) hanging commas right before ']' or '}' (trailing commas)
        fixed = re.sub(r',\s*([\]}])', r'\1', fixed)

        # D) hanging comma at end of file
        fixed = re.sub(r',\s*$', '', fixed)

    return fixed


def main():
    files = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith((".json", ".txt"))]
    print(f"Processing {len(files)} files...")

    ok, fail = 0, 0
    for fname in files:
        in_path = os.path.join(INPUT_FOLDER, fname)
        out_path = os.path.join(OUTPUT_FOLDER, os.path.splitext(fname)[0] + ".json")
        err_path = os.path.join(ERROR_FOLDER, fname)

        with open(in_path, "r", encoding="utf-8", errors="replace") as fh:
            raw = fh.read()

        raw = clean_json_content(raw)
        data = extract_json_block(raw)

        if data is None:
            fail += 1
            with open(err_path, "w", encoding="utf-8") as ef:
                ef.write(raw)
            continue

        # save correctly formatted json
        with open(out_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        ok += 1

    print(f"Done. {ok} files cleaned successfully, {fail} failed.")
    if fail > 0:
        print(f"Problematic files are in: {ERROR_FOLDER}")

if __name__ == "__main__":
    main()
