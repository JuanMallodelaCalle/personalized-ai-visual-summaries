import os
import json

# paths
DIALOGUES_FOLDER     = r"C:/Users/Juan/Desktop/TFM/1000/out_visual_turns/dialogues"
VISUAL_TURNS_FOLDER  = r"C:/Users/Juan/Desktop/TFM/1000/out_visual_turns/response_clean"
OUTPUT_FOLDER        = r"C:/Users/Juan/Desktop/TFM/1000/out_visual_turns/prompts_images"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# 1) index all dialogues by dialogue_id -> (prompt_a, prompt_b) 
# and remember filename to map to n if pattern matches
id_to_portraits = {}
id_to_filename  = {}

for fname in os.listdir(DIALOGUES_FOLDER):
    if not fname.lower().endswith((".json", ".txt")):
        continue
    path = os.path.join(DIALOGUES_FOLDER, fname)
    try:
        data = load_json(path)
    except Exception:
        continue

    did = data.get("dialogue_id")
    if not did:
        continue

    # get portrait prompts from profiles
    profiles = data.get("profiles", {})
    A = profiles.get("A", {})
    B = profiles.get("B", {})

    # preferred field name
    promptA = A.get("profile_prompt") or A.get("persona_prompt") or data.get("persona_prompt_A")
    promptB = B.get("profile_prompt") or B.get("persona_prompt") or data.get("persona_prompt_B")

    if not (isinstance(promptA, str) and isinstance(promptB, str)):
        # if missing, try fallback (empty strings)
        promptA = promptA or ""
        promptB = promptB or ""

    id_to_portraits[did] = (promptA, promptB)
    id_to_filename[did]  = fname  # para intentar respetar numeración si coincide

# 2) iterate through visual_turns and build output
ok, miss_portraits, miss_visual = 0, [], []

# sort files numerically if possible
files = sorted([f for f in os.listdir(VISUAL_TURNS_FOLDER) if f.lower().endswith((".json", ".txt"))],
               key=lambda x: int(''.join(c for c in x if c.isdigit()) or 0))

for fname in files:
    vpath = os.path.join(VISUAL_TURNS_FOLDER, fname)
    try:
        vdata = load_json(vpath)
    except Exception:
        miss_visual.append(fname)
        continue

    did = vdata.get("dialogue_id")
    vturns = vdata.get("visual_turns", [])
    if not did or not isinstance(vturns, list):
        miss_visual.append(fname)
        continue

    if did not in id_to_portraits:
        miss_portraits.append((fname, did))
        # continue, but with empty strings to avoid breaking the pipeline
        promptA, promptB = "", ""
    else:
        promptA, promptB = id_to_portraits[did]

    # build list of images
    images = []
    for item in vturns:
        image_id = item.get("image_id", "")
        speaker_focus = item.get("speaker_focus", "")
        prompt = item.get("prompt", "")

        images.append({
            "image_id": image_id,
            "speaker_focus": speaker_focus,
            "prompt": prompt
        })

    out_obj = {
        "persona_prompt_A": promptA,
        "persona_prompt_B": promptB,
        "images": images
    }

    # output name: if files are numbered like prompt_n.json, respect that n
    # use the current file number if available; otherwise fallback to dialogue_id
    num = ''.join(c for c in fname if c.isdigit())
    if num:
        out_name = f"prompt_{num}.json"
    else:
        # fallback by id (sanitize special chars)
        safe_id = ''.join(ch if ch.isalnum() or ch in ('-', '_') else '_' for ch in did)
        out_name = f"{safe_id}.json"

    out_path = os.path.join(OUTPUT_FOLDER, out_name)
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out_obj, f, ensure_ascii=False, indent=2)

    ok += 1

print(f"Done. {ok} files generated in '{OUTPUT_FOLDER}'.")

if miss_portraits:
    print(f"Warning: {len(miss_portraits)} dialogues lacked portraits in 'dialogues' folder (left empty). Examples:")
    for fn, did in miss_portraits[:5]:
        print(" -", fn, "->", did)

if miss_visual:
    print(f"Problematic visual_turns files: {len(miss_visual)}. Examples:")
    for fn in miss_visual[:5]:
        print(" -", fn)
