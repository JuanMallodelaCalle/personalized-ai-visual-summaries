import os
import json
import re

# paths
RESPONSES_DIR = r"C:/Users/Juan/Desktop/TFM/1000/out_profile_extension/response_clean"
IMAGE_PROMPTS_DIR = r"C:/Users/Juan/Desktop/TFM/1000/out_profile_images_prompts/response"
DIALOGUES_FILE = r"C:/Users/Juan/Desktop/TFM/1000/1000_Mallo.json"
OUTPUT_DIR = r"C:/Users/Juan/Desktop/TFM/1000/out_visual_turns/dialogues"  # final folder for the 1000 prompt_N.txt files

os.makedirs(OUTPUT_DIR, exist_ok=True)


def read_json(path):
    """Reads a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def read_text(path):
    """Reads a text file."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def parse_ab_prompts(txt):
    """
    Extracts A_PROMPT and B_PROMPT from a .txt file. Supports multi-line.
    Expected format:
        A_PROMPT: <text...>
        (optional blank line)
        B_PROMPT: <text...>
        (optional multi-line rest)
    """
    # normalize newlines
    s = txt.replace("\r\n", "\n").replace("\r", "\n")
    
    # markers
    a_tag = "A_PROMPT:"
    b_tag = "B_PROMPT:"
    
    a_pos = s.find(a_tag)
    b_pos = s.find(b_tag)
    
    if a_pos == -1 or b_pos == -1:
        # Fallback if tags are missing (though previous steps should ensure they exist)
        # You might want to raise an error or return empty strings.
        # Here we raise for safety as requested by logic structure.
        # But if you prefer robustness, you could return "", ""
        raise ValueError("A_PROMPT and/or B_PROMPT not found in text.")

    if a_pos > b_pos:
        # swap if out of order for some reason
        a_pos, b_pos = b_pos, a_pos
        a_tag, b_tag = b_tag, a_tag

    a_text = s[a_pos + len(a_tag): b_pos].strip()
    b_text = s[b_pos + len(b_tag):].strip()

    # light cleanup: remove surrounding quotes if present
    def dequote(t):
        t = t.strip()
        if (t.startswith('"') and t.endswith('"')) or (t.startswith("'") and t.endswith("'")):
            return t[1:-1].strip()
        return t

    return dequote(a_text), dequote(b_text)


def build_index_by_id(dialogues_path):
    """Returns dict: dialogue_id -> {'dialogue': [...], 'persona': {...}, ...}"""
    data = read_json(dialogues_path)
    by_id = {}
    
    if isinstance(data, list):
        for item in data:
            did = item.get("dialogue_id")
            if did:
                by_id[did] = item
    elif isinstance(data, dict) and "items" in data:
        # just in case JSON is wrapped in {'items': [...]}
        for item in data["items"]:
            did = item.get("dialogue_id")
            if did:
                by_id[did] = item
    else:
        raise ValueError("Unexpected format in 1000_Mallo.json")
    
    return by_id


def main():
    by_id = build_index_by_id(DIALOGUES_FILE)

    # list prompt_###.json files in response_clean
    json_files = sorted([f for f in os.listdir(RESPONSES_DIR) if f.lower().endswith(".json") and f.lower().startswith("prompt_")])

    ok_count = 0
    miss_dialogue = []
    miss_image = []

    for fname in json_files:
        # extract number N from "prompt_N.json"
        n = os.path.splitext(fname)[0].split("_")[-1]
        
        response_path = os.path.join(RESPONSES_DIR, fname)
        imgprompts_path = os.path.join(IMAGE_PROMPTS_DIR, f"prompt_{n}.txt")

        # read clean extended profiles
        resp = read_json(response_path)
        did = resp.get("dialogue_id", "")
        
        if not did or did not in by_id:
            miss_dialogue.append((fname, did))
            # continue with empty dialogue list if ID not found
            dialogue_block = []
        else:
            dialogue_block = by_id[did].get("dialogue", [])

        # read A/B image prompts
        if not os.path.isfile(imgprompts_path):
            miss_image.append(f"prompt_{n}.txt")
            a_prompt, b_prompt = "", ""
        else:
            try:
                a_prompt, b_prompt = parse_ab_prompts(read_text(imgprompts_path))
            except ValueError:
                miss_image.append(f"prompt_{n}.txt (parse error)")
                a_prompt, b_prompt = "", ""

        # construct final object
        profiles = resp.get("profiles", {})
        merged_profiles = {}
        
        for who, pdata in profiles.items():
            pdata = dict(pdata) if isinstance(pdata, dict) else {}
            # insert correct profile_prompt
            if who == "A":
                pdata["profile_prompt"] = a_prompt
            elif who == "B":
                pdata["profile_prompt"] = b_prompt
            else:
                pdata["profile_prompt"] = ""
            
            merged_profiles[who] = pdata

        final_obj = {
            "dialogue_id": did,
            "profiles": merged_profiles,
            "dialogue": dialogue_block
        }

        # save as prompt_N.txt (pretty JSON content)
        out_path = os.path.join(OUTPUT_DIR, f"prompt_{n}.txt")
        with open(out_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(final_obj, ensure_ascii=False, indent=2))

        ok_count += 1

    print(f"Generated {ok_count} files in '{OUTPUT_DIR}'")
    
    if miss_dialogue:
        print("\n[WARN] dialogue_id not found in 1000_Mallo.json (first 5):")
        for item in miss_dialogue[:5]:
            print("   ", item)
            
    if miss_image:
        print("\n[WARN] Missing image prompts (first 5):")
        for item in miss_image[:5]:
            print("   ", item)


if __name__ == "__main__":
    main()
