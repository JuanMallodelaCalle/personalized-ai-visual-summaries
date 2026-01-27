import json
import os

# paths
INPUT_FOLDER = "C:/Users/Juan/Desktop/TFM/1000/out_profile_extension/response_clean"
OUTPUT_FOLDER = "C:/Users/Juan/Desktop/TFM/1000/out_profile_images_prompts/prompts"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# base prompt
PROMPT_BASE = """You are a visual description expert. Create two concise, photorealistic portrait prompts for an AI image model, one for Speaker A and one for Speaker B, using ONLY the provided extended profiles.
Do NOT invent facts beyond the profile. All visual details MUST be consistent with profile_struct (age, gender_identity, sexual_orientation, ethnicity, nationality, residence_country).
Each prompt should be fully self-contained and comprehensible on its own.

OUTPUT FORMAT (MANDATORY):
Return ONLY the two final prompts, nothing else, in exactly this format:
A_PROMPT: <prompt text for A>
B_PROMPT: <prompt text for B>

PROMPT CONTENT RULES:
- Third person. Start with identity basics: age, gender identity, ethnicity (single label).
- Portrait framing: centered upper-body or shoulders-up, square (1:1), neutral/soft lighting, photorealistic, sharp facial focus.
- Reflect key facial/clothing features and accessories; mention hair/skin/eyes where visible. If mandatory head coverings apply (see below), hair must NOT be visible.
- Background: softly blurred, realistic, with subtle hints inspired by the environment (no busy scenes).
- Keep the prompt under 300 words per character.
- Age-appropriate: minors (under 18) must be depicted in a non-sexualized, neutral style.

CULTURAL/LEGAL ATTIRE (APPLY STRICTLY TO FEMALE OR TRANSGENDER FEMALE WHEN SPECIFIED):
- If gender_identity is "female" OR "transgender female", AND residence_country is Iran → depict hijab (hair fully covered) and modest clothing.
- If gender_identity is "female" OR "transgender female", AND residence_country is Afghanistan → depict niqab/burka or at minimum a hijab, consistent with strict dress norms.
- If gender_identity is "female" OR "transgender female", AND residence_country is Saudi Arabia → use modest attire; abaya with headscarf is common and may be depicted, but it is not strictly mandatory. Prefer plausible social norms over stereotypes.

COHERENCE EXAMPLES:
- If the profile mentions hair color but a head covering is required, phrase it as “hair tucked under a hijab/niqab/abaya” without showing hair.
- Styling should be culturally plausible given nationality/residence; avoid clichés and stereotypes.

Now generate the two prompts based strictly on the following JSON profile:
""".strip()

def main():
    # only process prompt_*.json files
    json_files = [f for f in os.listdir(INPUT_FOLDER)
                  if f.lower().endswith(".json") and f.lower().startswith("prompt_")]

    count = 0
    for fname in sorted(json_files):
        in_path = os.path.join(INPUT_FOLDER, fname)

        with open(in_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # minimal structure check
        profiles = data.get("profiles", {})
        if not (isinstance(profiles, dict) and "A" in profiles and "B" in profiles):
            # if something is missing, we proceed anyway (the API might reject it, but we generate the file)
            pass

        # construct final payload to send to API (base prompt + JSON)
        payload = PROMPT_BASE + "\n" + json.dumps(data, ensure_ascii=False, indent=2)

        # write the .txt file
        out_name = os.path.splitext(fname)[0] + ".txt"  # prompt_123.txt
        out_path = os.path.join(OUTPUT_FOLDER, out_name)

        with open(out_path, "w", encoding="utf-8", newline="\n") as out_f:
            out_f.write(payload)

        count += 1

    print(f"Generated {count} .txt files in '{OUTPUT_FOLDER}'")

if __name__ == "__main__":
    main()
