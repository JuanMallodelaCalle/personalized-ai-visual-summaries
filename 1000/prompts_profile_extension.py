import json
import os
import random
from typing import Any, Dict, List, Tuple

# paths
INPUT_FILE = "1000_Mallo.json"
OUTPUT_FOLDER = "out_profile_extension/prompts"
CONFIG_FILE = "config/demographics_config.json"
M49_MAP_FILE = "config/m49_by_region.json"
POP_FILE = "config/population_by_country.json"

# base prompt
PROMPT_BASE = """You are an expert in psychological inference and character profiling.

Your task is to extend the personality profiles of both speakers based on a single dialogue entry. The input below contains everything you need to perform a deep and creative expansion of each character's persona. 

Important constraints (read carefully):
- Do NOT infer attributes from the other speaker. Only use the character's own lines and original persona.
- If an attribute is NOT inferable, you MUST use the provided FALLBACK VALUES for that character.
- However, if a fallback value would directly CONTRADICT the character's own content (e.g., years of full-time work vs. age 14), you MUST ADJUST the fallback to the nearest coherent value that preserves the original information (adjust the fallback, not the original dialogue/persona).
- Keep labels clean and consistent. Avoid stereotypes.

Inference-first rule (CRITICAL):
- For EACH attribute in profile_struct, attempt to INFER it strictly from the character's OWN content (their persona sentences and their own spoken lines).
- “Inferable” means there is clear, direct evidence or an unambiguous implication in the character's own content.
- NEVER fabricate values outside the fallback when not inferable. Do not use “unknown”, “N/A”, ranges, or multiple options.
- Nationality and residence_country: only use an inferred country when it's explicitly stated or unambiguously implied in the character's own content. Otherwise, use the EXACT fallback value.
- Ethnicity: choose from the allowed labels only when clearly supported by the character's own content; otherwise, use the EXACT fallback label.
- Gender identity and sexual_orientation: only infer if explicitly stated or unambiguously implied; otherwise, use the EXACT fallback (with the minors rule below).

Nationality vs. Residence interpretation (HARD RULE):
- Employment, league membership (e.g., NBA), schooling, or current address imply RESIDENCE only.
- Change NATIONALITY only when the character explicitly self-identifies it (e.g., “I am American”, “I'm from Russia”, “born in X”, “my passport is X”).
- Otherwise, KEEP the fallback nationality exactly.

Minors rule (MANDATORY):
- If the final AGE < 13:
  - gender_identity MUST be either "male" or "female" (no non-binary or transgender labels below 13).
  - sexual_orientation MUST be "unspecified".
  - The narrative MUST avoid adult topics (e.g., long-term employment, explicit romance). Keep school-, family-, and hobby-centered contexts.
- If AGE is 13-17:
  - All gender_identity labels are allowed, but keep content age-appropriate.
  - sexual_orientation may be inferred cautiously if the text genuinely supports it; otherwise, use fallback. Do NOT sexualize minors.

Post-adjustment consistency pass (MANDATORY):
- If you adjusted AGE to ensure coherence, RE-APPLY the minors rule above.
- If final AGE ≥ 13, you MUST NOT output "unspecified" for sexual_orientation.
  * Prefer an orientation clearly supported by the character's own content.
  * Otherwise use the fallback orientation; BUT if the fallback is "unspecified", set sexual_orientation to "heterosexual" (unless the character's own content clearly supports another label).

Cultural-religious & context realism (guidance, not stereotypes):
- In visual_appearance and environment, reflect plausible cues given nationality and/or residence_country (e.g., climate, architecture, common garments, workspaces).
- When the country has strong religious or cultural norms around dress (e.g., hijab or modest wear), you may include such details ONLY if it fits plausibly with the character's own persona/lines and the narrative tone. Always avoid stereotypes and allow individual variation.

Mixed ancestry in narrative (optional, context-driven):
- You may enrich the narrative with mixed ancestry ONLY when it makes sense:
  * The character resides in a country different from nationality and the context suggests close cultural ties; OR
  * The residence_country is among commonly multicultural destinations (e.g., USA, Canada, UK, France, Germany, Spain, Italy, Australia, New Zealand, UAE, Qatar, Kuwait, Saudi Arabia, Singapore, Brazil, Argentina, Mexico, South Africa).
- DO NOT fabricate implausible combinations; keep it culturally and migrationally plausible (e.g., Japanese-Spanish in Spain; Filipino-UAE in UAE). This is a narrative nuance; the profile_struct still uses exactly one ethnicity label from the allowed list.
- Do not change ethnicity merely to mirror residence_country.

What You Receive:
A single JSON block with:
- dialogue_id
- persona: original persona sentences (speaker keys end with _A and _B)
- dialogue: list of turns with original persona_id and text fields (text_1, text_2, ...)

Speaker mapping:
- Treat the persona key ending in _A as Speaker "A"
- Treat the persona key ending in _B as Speaker "B"

You must generate a detailed personality profile using:
- The character's original persona sentences (you may rephrase or reassign them).
- The things each character says in the dialogue (do not infer from the other speaker's lines).
- Contextual clues from the conversation: reactions, behavior, self-descriptions, topics, values, tone, etc.
Important: You must ignore information about the character that is only mentioned by the other speaker. Only the character's own statements, behaviors, or reactions are valid for inference.

Profile Narrative Sections:
1. personal_data (Factual biographical sentences only.)
   - Full name (Choose a culturally plausible name consistent with NATIONALITY; a mixed-ancestry nuance is fine if the narrative supports it. Avoid mismatched names without support.)
   - Age
   - Gender identity
   - Ethnicity
   - Occupation
   - Country or city of residence
   - Relationship status
   - Education level (optional but recommended)

2. visual_appearance
   - Hair type and color
   - Skin tone
   - Eye color
   - Facial hair (if any)
   - Glasses or accessories (and their style)
   - Typical clothing
   - Height and body type (optional)

3. environment (Refer to plausible locations consistent with residence_country and city.)
   - Where and how the character lives (urban/rural, apartment/house, etc.)
   - Important objects, tools, or thematic items around them
   - Hints about climate, culture, or geography
   - Spaces tied to profession or hobbies (lab, kitchen, studio, gym, etc.)

4. personality_attitudes
   - Core personality traits (e.g. curious, reserved, energetic)
   - Hobbies and passions
   - Beliefs, values, or worldview
   - Social behaviors
   - Personal routines or goals

5. other_details (optional)
   - Memorable quirks or behaviors
   - Catchphrases, expressions, or habits
   - Backstory fragments or unusual facts
   - Extra flavor that enriches the character

Allowed labels (STRICT):
- Ethnicity (choose EXACTLY one of the following labels):
{VALID_ETHNICITIES}

- Gender identity (choose EXACTLY one):
{VALID_GENDER}

- Sexual orientation (choose EXACTLY one; if AGE<13, it MUST be "unspecified"):
{VALID_ORIENTATIONS}
(Allowed special value for minors <13: "unspecified")

- Nationality & residence_country:
  * Must be a SINGLE standard country name (ISO 3166 / UN M49 English short name).
  * Do NOT output cities, regions, provinces, or multiple values.
  * If NOT inferable from the character's own content, you MUST set it to EXACTLY the FALLBACK value provided for that character below.
  * residence_country may differ from nationality.

Coherence rule (MANDATORY):
- If a fallback conflicts with original content, adjust the fallback to the nearest coherent value (e.g., raise age; swap residence to match schooling/employment context; select a culturally plausible name).
- DO NOT alter the original dialogue, persona sentences, or keys. Only adjust the fallback-derived attribute to ensure consistency.

Requirements:
- Each section in each persona must contain at least 5 full sentences, written in first person, non-repetitive, and rich in detail.
- Preserve the exact dialogue_id and speaker IDs (*_A and *_B) as received.
- Avoid duplication: every sentence in a profile should add new detail.
- The output must be suitable for visual generation and storytelling applications.

What You Must Produce (STRICT JSON):
{{
  "dialogue_id": "<id>",
  "profiles": {{
    "A": {{
      "profile_struct": {{
        "age": <integer>,
        "gender_identity": "<one of the allowed Gender identity labels>",
        "sexual_orientation": "<one of the allowed Sexual orientation labels or 'unspecified' if AGE<13>",
        "ethnicity": "<one of the allowed Ethnicity labels>",
        "nationality": "<country>",
        "residence_country": "<country>"
      }},
      "profile_narrative": {{
        "personal_data": [ "..." ],
        "visual_appearance": [ "..." ],
        "environment": [ "..." ],
        "personality_attitudes": [ "..." ],
        "other_details": [ "..." ]
      }}
    }},
    "B": {{ ... same structure ... }}
  }}
}}

FALLBACK VALUES FOR SPEAKER A:
{FALLBACK_JSON_A}

FALLBACK VALUES FOR SPEAKER B:
{FALLBACK_JSON_B}

<INPUT JSON BEGINS — DO NOT ALTER KEYS OR FIELDS>
{INPUT_DIALOGUE_JSON}
"""

# utilities

def read_json(path: str) -> Any:
    """Reads a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_text(path: str, text: str) -> None:
    """Writes text to a file, creating directories if necessary."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def rnd_choice_by_probs(probs: Dict[str, float], rng: random.Random) -> str:
    """Selects a key from a dictionary based on value probabilities."""
    keys = list(probs.keys())
    weights = [probs[k] for k in keys]
    return rng.choices(keys, weights=weights, k=1)[0]


def sample_age_from_group(group: str, rng: random.Random) -> int:
    """Samples an age based on the provided group range."""
    # We allow real minors (4–17) in <18. The threshold of 13 is applied in the prompt rules.
    ranges = {
        "<18": (4, 17),
        "18-29": (18, 29),
        "30-39": (30, 39),
        "40-49": (40, 49),
        "50-59": (50, 59),
        "60+": (60, 95)
    }
    lo, hi = ranges[group]
    if group == "60+":
        # Distribution biased towards common ages (60–85) 
        x = rng.random() ** 1.8   # exponent >1 = more weight to lower values
        return int(lo + (hi - lo) * x)
    return rng.randint(lo, hi)


def load_populations(path: str) -> Dict[str, int]:
    """Loads population data."""
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {str(k): int(v) for k, v in data.items() if isinstance(v, (int, float))}


def weighted_choice(countries: List[str], pops: Dict[str, int], rng: random.Random) -> str:
    """Chooses a country weighted by population (minimum weight 1 if missing)."""
    weights = []
    for c in countries:
        w = pops.get(c, 0)
        if w <= 0:
            w = 1
        weights.append(w)
    return rng.choices(countries, weights=weights, k=1)[0]


# M49 logic
def resolve_m49_regions(region_spec: str, m49: Dict[str, List[str]]) -> List[str]:
    """
    Parses region specifications.
    Examples: "M49: Northern Africa + Western Asia" | "M49: Sub-Saharan Africa" | "M49: ALL"
    Returns a list of countries (no duplicates).
    """
    spec = region_spec.replace("M49:", "").strip()
    if spec.upper() == "ALL":
        pool: List[str] = []
        for _, countries in m49.items():
            pool.extend(countries)
        return sorted(set(pool))

    regions = [r.strip() for r in spec.split("+")]
    pool: List[str] = []
    missing = []
    for r in regions:
        if r in m49:
            pool.extend(m49[r])
        else:
            missing.append(r)

    if missing:
        raise ValueError(f"M49 regions not found in {M49_MAP_FILE}: {missing}")
    return sorted(set(pool))


def ethnicity_to_country_pool(eth_label: str, cfg: Dict[str, Any], m49: Dict[str, List[str]]) -> List[str]:
    """Maps an ethnicity label to a list of potential countries using config."""
    region_spec = cfg["by_ethnicity_nationality"].get(eth_label, "")
    if not isinstance(region_spec, str) or not region_spec.startswith("M49:"):
        raise ValueError(f"Config for ethnicity must use 'M49:' spec, got: {region_spec} for {eth_label}")
    return resolve_m49_regions(region_spec, m49)


def sample_fallback(cfg: Dict[str, Any], m49: Dict[str, List[str]], pop_map: Dict[str, int], rng: random.Random) -> Dict[str, Any]:
    """Generates a complete fallback demographic profile."""    
    eth = rnd_choice_by_probs(cfg["ethnicity"], rng)
    nationality_pool = ethnicity_to_country_pool(eth, cfg, m49)
    if not nationality_pool:
        raise ValueError(f"No countries resolved for ethnicity: {eth}")

    nationality = weighted_choice(nationality_pool, pop_map, rng)

    same_prob = cfg["residence_migration_ratio"]["same_as_nationality"]
    if rng.random() < same_prob:
        residence = nationality
    else:
        all_countries = []
        for reg_countries in m49.values():
            all_countries.extend(reg_countries)
	# Create a global pool excluding current nationality
        global_pool = [c for c in set(all_countries) if c != nationality] or list(set(all_countries))
        residence = weighted_choice(global_pool, pop_map, rng)

    age_group = rnd_choice_by_probs(cfg["age_group"], rng)
    age = sample_age_from_group(age_group, rng)
    gender_identity = rnd_choice_by_probs(cfg["gender_identity"], rng)
    orient = rnd_choice_by_probs(cfg["sexual_orientation"], rng)

    # Hard constraint for very young characters
    if age < 13:
        gender_identity = random.choice(["male", "female"])
        orient = "unspecified"

    return {
        "age": age,
        "gender_identity": gender_identity,
        "sexual_orientation": orient,
        "ethnicity": eth,
        "nationality": nationality,
        "residence_country": residence
    }


def detect_AB_keys(persona_dict: Dict[str, List[str]]) -> Tuple[str, str]:
    """
    Detects which key corresponds to Speaker A and Speaker B.
    Does not transform the dialogue; strictly for mapping purposes in the prompt.
    """
    a_key = None
    b_key = None
    for k in persona_dict.keys():
        if str(k).endswith("_A"):
            a_key = k
        elif str(k).endswith("_B"):
            b_key = k

    if not a_key or not b_key:
        keys = sorted(persona_dict.keys())
        if len(keys) >= 2:
            a_key = a_key or keys[0]
            b_key = b_key or keys[1]
        elif len(keys) == 1:
            a_key = a_key or keys[0]
            b_key = b_key or keys[0]
        else:
            a_key, b_key = "A", "B"
    return a_key, b_key


def bullet_list(labels: List[str]) -> str:
    """Formats a list of strings into a bulleted string."""
    return "\\n".join([f"- {x}" for x in labels])


def main():
    # 1) Load Config and M49 (MANDATORY)
    if not os.path.exists(CONFIG_FILE):
        raise FileNotFoundError(f"Missing config file: {CONFIG_FILE}")
    if not os.path.exists(M49_MAP_FILE):
        raise FileNotFoundError(f"Missing M49 map file: {M49_MAP_FILE}")

    cfg = read_json(CONFIG_FILE)
    m49_map = read_json(M49_MAP_FILE)
    pop_map = load_populations(POP_FILE)

    rng = random.Random(cfg.get("seed", 42))
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    # 2) Read Dataset
    data = read_json(INPUT_FILE)
    if isinstance(data, dict) and "items" in data:
        items = data["items"]
    elif isinstance(data, list):
        items = data
    else:
        raise ValueError("Unrecognized input format for 1000_Mallo.json")

    valid_eth_labels = list(cfg["ethnicity"].keys())
    valid_gender_labels = list(cfg["gender_identity"].keys())
    valid_orientation_labels = list(cfg["sexual_orientation"].keys()) + ["unspecified"]  # for minors <13

    VALID_ETH = bullet_list(valid_eth_labels)
    VALID_GENDER = bullet_list(valid_gender_labels)
    VALID_ORI = bullet_list(valid_orientation_labels)

    # 3) Generate Prompts
    count = 0
    for idx, entry in enumerate(items, start=1):
        persona = entry.get("persona", {})
        _a_key, _b_key = detect_AB_keys(persona)

        # Sample independent fallbacks for A and B
        fb_A = sample_fallback(cfg, m49_map, pop_map, rng)
        fb_B = sample_fallback(cfg, m49_map, pop_map, rng)

        # Build prompt injecting the JSON exactly as is
        input_json_text = json.dumps(entry, ensure_ascii=False, indent=2)

        prompt_text = PROMPT_BASE \
            .replace("{VALID_ETHNICITIES}", VALID_ETH) \
            .replace("{VALID_GENDER}", VALID_GENDER) \
            .replace("{VALID_ORIENTATIONS}", VALID_ORI) \
            .replace("{FALLBACK_JSON_A}", json.dumps(fb_A, ensure_ascii=False, indent=2)) \
            .replace("{FALLBACK_JSON_B}", json.dumps(fb_B, ensure_ascii=False, indent=2)) \
            .replace("{INPUT_DIALOGUE_JSON}", input_json_text)

        out_path = os.path.join(OUTPUT_FOLDER, f"prompt_{idx}.txt")
        write_text(out_path, prompt_text)
        count += 1

    print(f"Generated {count} prompts in '{OUTPUT_FOLDER}'")

if __name__ == "__main__":
    main()
