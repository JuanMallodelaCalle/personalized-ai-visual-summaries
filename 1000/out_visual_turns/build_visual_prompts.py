import os
import json

# paths
INPUT_FOLDER  = r"C:/Users/Juan/Desktop/TFM/1000/out_visual_turns/dialogues"
OUTPUT_FOLDER = r"C:/Users/Juan/Desktop/TFM/1000/out_visual_turns/prompts"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# base prompt
PROMPT_BASE = """You are a visual storytelling expert. Read one dialogue with two detailed character profiles. Your task is to identify the most visually meaningful moments and write cinematic, ultra-realistic image prompts for each one. Think as if you are storyboarding a short film — each image must capture a self-contained visual scene.

Take your time reading and reasoning through the content. Quality and depth matter more than brevity.

---

WHAT YOU RECEIVE
- dialogue_id
- profiles:
  - Each has:
    - profile_struct (age, gender_identity, sexual_orientation, ethnicity, nationality, residence_country)
    - profile_narrative (personal_data, visual_appearance, environment, personality_attitudes, other_details)
    - profile_prompt (portrait prompt already defining the character's baseline appearance)
- dialogue: list of turns with persona_id and text_X fields ("text_1", "text_2", ...)

---

WHAT YOU MUST OUTPUT
Return ONLY the following JSON:
{
  "dialogue_id": "<id>",
  "visual_turns": [
    {
      "image_id": "<dialogue_id>_img_1",
      "dialogue_indices": ["text_1","text_2"],      // exact ids from the dialogue; group consecutive lines if they form one scene
      "speaker_focus": "A" | "B" | "both",          // who is visually active or expressive in this image
      "scene_type": "shared" | "memory" | "imagined" | "cutaway" | "montage",
      "prompt": "<single, self-contained photorealistic prompt, ≤150 words>"
    }
  ]
}

---

YOUR TASK
Create a new structured field called "visual_turns" that identifies which parts of the dialogue should be represented visually (as standalone image scenes).

---

SELECTION & STRUCTURING RULES
- Choose all turns that add clear **visual or emotional meaning** (location, gesture, action, expression, emotion, visual change).
- Always include one early **shared** scene to ground both characters in the setting (or split-screen if remote).
- Merge consecutive lines when they show one continuous moment; include all their ids in dialogue_indices.
- Mark past scenes as 'memory'.
- Include visually rich or symbolic details even if brief.
- Typically 5-12 visual_turns per dialogue, but include any scene that adds visual meaning.
- Do not omit expressive, emotional, or dynamic lines.
- The resulting images should allow a viewer to understand the conversation visually.

---

SCENE_TYPE DICTIONARY (use ONLY these labels)
- shared: the ongoing present setting of the dialogue or its establishing shot (or split-screen if remote).
- memory: a recollection or past event from a speaker's life (calm or vivid).
- imagined: a non-real or hypothetical scene (dream, fantasy, or what-if).
- cutaway: a brief insert of an object, location, or visual metaphor relevant to the dialogue.
- montage: a short visual sequence of mini-moments showing progress or passage of time.

---

SPEAKER_FOCUS
- “A” if only A is visually central or active.
- “B” if only B is visually central or active.
- “both” if both characters appear or interact visually.
(Use “both” only if both are clearly visible or expressive in the same scene.)

---

CONSISTENCY WITH PROFILE PORTRAITS (CRUCIAL)
- Final rendering will combine: profile_prompt_A/profile_prompt_B (per speaker_focus) + your scene prompt.
- DO NOT restate base traits (age, ethnicity, gender_identity, etc.) that are already in the profile_prompt.
- Refer to characters **by name** (e.g., “Nikos” or “Alexei”) for clarity.
- Focus on what changes dynamically: pose, gesture, emotion, temporary outfit, props, environment, lighting, composition, and mood.
- Keep everything consistent with each character's profile_struct and narrative.

---

CULTURAL/LEGAL ATTIRE (MANDATORY WHEN APPLICABLE)
- If gender_identity is "female" AND residence_country is Iran → hijab & modest clothing (hair not visible).
- If gender_identity is "female" AND residence_country is Afghanistan → niqab/burka or at least hijab.
- If gender_identity is "female" AND residence_country is Saudi Arabia → abaya with headscarf (public setting).
(Do NOT apply these outside those countries. If hair was described elsewhere, phrase as “hair tucked under a hijab/headscarf.”)

---

PROMPT CONTENT REQUIREMENTS (for each visual_turn)
- Third-person cinematic description (avoid bullet lists or enumeration).
- Start naturally, using names or contextual cues, not lists of traits.
- Ultra realistic, photographic, cinematic; resolution target 1024x1024, square (1:1).
- Neutral or soft lighting unless the scene implies otherwise.
- Explicitly reflect **speaker_focus** in composition (who is centered, expressive, or dominant).
- Include: shot type (portrait, medium, wide), character posture, facial expression, relevant clothing or props, environment hints, and mood.
- Background: softly blurred but consistent with their environment and dialogue.
- Minors (<18): strictly neutral, non-sexualized.
- Prompts will be used directly for image generation, combined with each speaker's profile_prompt according to speaker_focus.

---

KNOWN PAST MISTAKES TO AVOID
- Do not miss unique or memorable visual content (e.g., scorpion hunting, ballroom dancing).
- Do not use "both" as speaker_focus unless both are visually active or expressive.
- Do not fail to mark "memory" for clearly past or distinct temporal scenes.
- Do not split connected utterances that belong to the same visual moment.

---

EXAMPLE OUTPUT SHAPE
{
  "dialogue_id": "persona_chat_7700",
  "visual_turns": [
    {
      "image_id": "persona_chat_7700_img_1",
      "dialogue_indices": ["text_1","text_2"],
      "speaker_focus": "both",
      "scene_type": "shared",
      "prompt": "..."
    },
    {
      "image_id": "persona_chat_7700_img_2",
      "dialogue_indices": ["text_5","text_6","text_7"],
      "speaker_focus": "B",
      "scene_type": "memory",
      "prompt": "..."
    }
    ...
  ]
}
"""

# prompt generation
files = sorted(
    [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith(".txt") or f.lower().endswith(".json")],
    key=lambda x: int(''.join(c for c in x if c.isdigit()) or '0')
)

print(f"Generating prompts for {len(files)} dialogues...")

for idx, filename in enumerate(files, 1):
    in_path  = os.path.join(INPUT_FOLDER, filename)
    out_name = f"prompt_{idx}.txt"
    out_path = os.path.join(OUTPUT_FOLDER, out_name)

    # read input json
    with open(in_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # write final prompt file
    with open(out_path, "w", encoding="utf-8", newline="\n") as out_f:
        out_f.write(PROMPT_BASE)
        out_f.write("\n\n---\n\n")
        json.dump(data, out_f, indent=2, ensure_ascii=False)

    print(f"  • {out_name} ready")

print(f"\nFinished: {len(files)} prompts in '{OUTPUT_FOLDER}'")
