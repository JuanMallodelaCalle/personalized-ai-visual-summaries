import os
import json
import re
from collections import Counter, defaultdict

# configuration
PROMPTS_FOLDER = "out_profile_extension/prompts"

def extract_fallbacks_from_prompt(text: str):
    """Extracts fallback JSONs for Speaker A and B from a prompt_N.txt file."""
    pattern = re.compile(
        r"FALLBACK VALUES FOR SPEAKER A:\s*(\{.*?\})\s*FALLBACK VALUES FOR SPEAKER B:\s*(\{.*?\})",
        re.S # re.S makes the dot match newlines (multiline match)
    )
    m = pattern.search(text)
    if not m:
        return None, None

    fb_a = json.loads(m.group(1))
    fb_b = json.loads(m.group(2))
    return fb_a, fb_b

def main():
    counters = defaultdict(Counter)
    total_prompts = 0

    for fname in sorted(os.listdir(PROMPTS_FOLDER)):
        if not fname.endswith(".txt"):
            continue
        path = os.path.join(PROMPTS_FOLDER, fname)
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        fb_a, fb_b = extract_fallbacks_from_prompt(text)
        if fb_a is None:
            print(f"[WARN] No fallbacks found in {fname}")
            continue

        total_prompts += 1
        for fb in (fb_a, fb_b):
            for key, val in fb.items():
                counters[key][str(val)] += 1

    print(f"Processed {total_prompts} prompts (x2 speakers = {total_prompts*2} fallbacks)")
    for key, counter in counters.items():
        print(f"\n=== {key.upper()} ===")
        total = sum(counter.values())
        for val, count in counter.most_common():
            perc = 100 * count / total
            print(f"{val:40} {count:5d}  ({perc:5.2f}%)")

if __name__ == "__main__":
    main()
