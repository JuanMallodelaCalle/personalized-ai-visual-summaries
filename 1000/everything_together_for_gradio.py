import os
import re
import json
import time

# paths
DIALOGUES_FOLDER = r"C:/Users/Juan/Desktop/TFM/1000/out_visual_turns/dialogues"       # prompt_N.txt (JSON with profiles + dialogue)
VISUAL_TURNS_FOLDER = r"C:/Users/Juan/Desktop/TFM/1000/out_visual_turns/response_clean" # prompt_N.json (JSON with visual_turns)
OUTPUT_FOLDER = r"C:/Users/Juan/Desktop/TFM/1000/gradio"              # <dialogue_id>.json

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# utilities
DIGITS_RE = re.compile(r'(\d+)')


def num_key(fname: str) -> int:
    """Extracts the first integer found in the filename."""
    m = DIGITS_RE.search(fname)
    return int(m.group(1)) if m else 0


def read_json_file(path: str):
    """Reads and parses a json file, handling markdown fences if present."""
    with open(path, "r", encoding="utf-8") as f:
        txt = f.read().strip()
    # remove accidental markdown fences
    if txt.startswith("```"):
        txt = re.sub(r"^```(?:json)?\s*|\s*```$", "", txt, flags=re.IGNORECASE|re.MULTILINE).strip()

    # direct attempt
    try:
        return json.loads(txt)
    except Exception:
        # minimal recovery: grab from first '{' to last '}'
        s, e = txt.find("{"), txt.rfind("}")
        if s != -1 and e != -1 and e > s:
            return json.loads(txt[s:e+1])
        raise


def extract_turn_index(utterance: dict) -> int | None:
    """Extracts the integer index from keys like 'text_7'."""
    for k in utterance.keys():
        if k.startswith("text_"):
            try:
                return int(k.split("_", 1)[1])
            except Exception:
                return None
    return None


def parse_dialogue_indices(indices: list[str]) -> int:
    """Returns the max integer index from a list like ["text_5", "text_6"]."""
    max_idx = -1
    for t in indices:
        try:
            n = int(t.replace("text_", ""))
            if n > max_idx:
                max_idx = n
        except Exception:
            pass
    return max_idx


# list files sorted by number n
dialogue_files = sorted(
    [f for f in os.listdir(DIALOGUES_FOLDER) if f.lower().endswith(".txt")],
    key=num_key
)
vt_files = sorted(
    [f for f in os.listdir(VISUAL_TURNS_FOLDER) if f.lower().endswith(".json")],
    key=num_key
)

if len(dialogue_files) != len(vt_files):
    print(f"WARNING: file counts differ: dialogues={len(dialogue_files)} vs visual_turns={len(vt_files)}")

total = min(len(dialogue_files), len(vt_files))
print(f"Merging {total} dialogues… (1sec delay per file)")

ok = 0
for i in range(total):
    dname = dialogue_files[i]
    vname = vt_files[i]

    dpath = os.path.join(DIALOGUES_FOLDER, dname)
    vpath = os.path.join(VISUAL_TURNS_FOLDER, vname)

    # load jsons
    dialogue_obj = read_json_file(dpath)     # contains dialogue_id, profiles, dialogue
    vt_obj = read_json_file(vpath)           # contains dialogue_id, visual_turns

    did_d = dialogue_obj.get("dialogue_id")
    did_v = vt_obj.get("dialogue_id")

    if did_d != did_v:
        # mismatch warning, but proceed using the dialogue file's id
        print(f"  [WARN] dialogue_id mismatch: {dname} -> {did_d} vs {vname} -> {did_v}")

    dialogue_list = dialogue_obj.get("dialogue", [])
    visual_turns = vt_obj.get("visual_turns", [])

    # build map: max_turn_index -> [image_id, ...] (preserve order of visual_turns)
    insert_after = {}
    for vt in visual_turns:
        idx = parse_dialogue_indices(vt.get("dialogue_indices", []))
        if idx >= 0:
            insert_after.setdefault(idx, []).append(vt.get("image_id"))

    # traverse dialogue and build new one with interleaved image_ids
    merged_dialogue = []
    for utt in dialogue_list:
        merged_dialogue.append(utt)
        idx = extract_turn_index(utt)

	# check if we need to insert images after this turn
        if idx is not None and idx in insert_after:
            for img_id in insert_after[idx]:
                merged_dialogue.append({"image_id": img_id})

    # build final output object
    out_obj = {
        "dialogue_id": did_d,
        "profiles": dialogue_obj.get("profiles", {}),
        "dialogue": merged_dialogue
    }

    # output filename by dialogue_id
    out_name = f"{did_d}.json" if did_d else f"merged_{num_key(dname):04d}.json"
    out_path = os.path.join(OUTPUT_FOLDER, out_name)

    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out_obj, f, ensure_ascii=False, indent=2)

    ok += 1
    print(f"  ✔ {out_name}")
    time.sleep(1)

print(f"\nDone. {ok} files generated in: {OUTPUT_FOLDER}")
