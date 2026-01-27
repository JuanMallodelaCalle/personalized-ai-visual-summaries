import os
import json
import time
import base64
import requests
from openai import AzureOpenAI
from dotenv import load_dotenv

# load env
load_dotenv()

AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
MODEL_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME")  # gpt-image-1

# config
INPUT_FOLDER = "out/prompts_images"     # folder with dialogue+prompts JSONs
OUTPUT_FOLDER = "out/dialogue_images"   # output folder for images
LOG_FILE = os.path.join(OUTPUT_FOLDER, "generation_log.txt")
DELAY_BETWEEN_REQUESTS = 1  # seconds
COST_PER_IMAGE_USD = 0.04

# init
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_version=API_VERSION
)


def download_image(url, output_path):
    try:
        r = requests.get(url, timeout=60)
        if r.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(r.content)
            print(f"Saved from URL: {output_path}")
        else:
            print(f"Failed to download from {url}: Status code {r.status_code}")
    except Exception as e:
        print(f"Error downloading image: {e}")


def save_base64_image(b64_data, output_path):
    try:
        image_data = base64.b64decode(b64_data)
        with open(output_path, "wb") as f:
            f.write(image_data)
        print(f"Saved from base64: {output_path}")
    except Exception as e:
        print(f"Error saving base64 image: {e}")


def numeric_key(filename: str) -> int:
    """Extracts integer N from 'prompt_N.json'; returns 0 if fails to preserve order."""
    name, _ = os.path.splitext(filename)
    digits = "".join(ch for ch in name if ch.isdigit())
    try:
        return int(digits) if digits else 0
    except:
        return 0


def build_full_prompt(prompt_A: str, prompt_B: str, scene_prompt: str, speaker_focus: str) -> str:
    """
    Builds the master prompt with clear priorities:
    - SCENE is strictly primary.
    - Character references A/B serve only for identity (face/hair/glasses/vibe).
    - In case of conflict, SCENE wins.
    """
    a_ref = f"[A_REFERENCE]\n{prompt_A}\n[/A_REFERENCE]" if speaker_focus in ("A", "both") else ""
    b_ref = f"[B_REFERENCE]\n{prompt_B}\n[/B_REFERENCE]" if speaker_focus in ("B", "both") else ""

    reference_block = "\n\n".join([b for b in (a_ref, b_ref) if b])

    full_prompt = (
        "You are generating ONE ultra-realistic 1024×1024 image for a fictional dialogue.\n\n"
        "PRIORITY ORDER (strict):\n"
        "1) SCENE is the primary instruction to render.\n"
        "2) Use CHARACTER REFERENCES only to maintain each character’s facial identity, approximate hair style/color, glasses, and general vibe.\n"
        "3) If any detail in CHARACTER REFERENCES conflicts with SCENE, FOLLOW THE SCENE and keep only identity-level features (face, hair color/length, glasses). "
        "Do NOT reintroduce portrait backgrounds or irrelevant props.\n\n"
        "COMPOSITION:\n"
        "- Respect speaker_focus: A, B, or both must be clearly dominant/visible in framing and expression.\n"
        "- For \"both\", show both characters in the same scene or split-screen if explicitly implied by SCENE.\n\n"
        "STYLE:\n"
        "- Ultra realistic, photographic, cinematic; square (1:1), sharp focus where appropriate; natural lighting unless SCENE specifies otherwise.\n\n"
        "NEGATIVE GUIDANCE (do not):\n"
        "- Do not restate or copy portrait backgrounds unless SCENE asks for them.\n"
        "- Do not mix attributes between A and B.\n"
        "- Do not invent ages/ethnicities; do not change baseline face identity.\n"
        "- Avoid text overlays or watermarks.\n\n"
        "[CHARACTER_REFERENCES]\n"
        f"{reference_block}\n\n"
        "[SCENE]\n"
        f"{scene_prompt}"
    )
    return full_prompt


# main loop
prompt_files = sorted(
    [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith(".json")],
    key=numeric_key
)
print(f"Found {len(prompt_files)} prompt files to process.\n")

total_cost = 0.0
log_entries = []

for idx, filename in enumerate(prompt_files, 1):
    input_path = os.path.join(INPUT_FOLDER, filename)
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        prompt_A = data["persona_prompt_A"]
        prompt_B = data["persona_prompt_B"]
        images = data["images"]
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        continue

    for entry in images:
        image_id = entry["image_id"]
        speaker_focus = entry["speaker_focus"]
        scene_prompt = entry["prompt"]

        # build prompt with clear priorities
        full_prompt = build_full_prompt(prompt_A, prompt_B, scene_prompt, speaker_focus)

        try:
            response = client.images.generate(
                model=MODEL_DEPLOYMENT_NAME,
                prompt=full_prompt,
                n=1,
                size="1024x1024"
            )
            image_data = response.data[0]
            output_image_path = os.path.join(OUTPUT_FOLDER, f"{image_id}.png")

            if hasattr(image_data, "url") and image_data.url:
                download_image(image_data.url, output_image_path)
                log_entries.append(f"{image_id}: URL OK - {image_data.url}")

            elif hasattr(image_data, "b64_json") and image_data.b64_json:
                save_base64_image(image_data.b64_json, output_image_path)
                log_entries.append(f"{image_id}: base64_json OK")

            elif hasattr(image_data, "image_base64") and image_data.image_base64:
                save_base64_image(image_data.image_base64, output_image_path)
                log_entries.append(f"{image_id}: image_base64 OK")

            else:
                print(f"No valid image found in response for {image_id}")
                log_entries.append(f"{image_id}: ERROR - No image found")

            total_cost += COST_PER_IMAGE_USD

        except Exception as e:
            print(f"Error generating {image_id}: {e}")
            log_entries.append(f"{image_id}: ERROR - {e}")

        print(f"Sleeping {DELAY_BETWEEN_REQUESTS} sec...\n")
        time.sleep(DELAY_BETWEEN_REQUESTS)

# final log
with open(LOG_FILE, "w", encoding="utf-8") as log_f:
    log_f.write("\n".join(log_entries))

print("\nAll done.")
print(f"Estimated total cost: ${total_cost:.2f}")
print(f"Log saved to: {LOG_FILE}")
