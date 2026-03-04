import os
import re
import time
import json
import base64
import csv
from io import BytesIO
from typing import Optional, Tuple

from dotenv import load_dotenv
from openai import AzureOpenAI
from PIL import Image

# ============= CONFIG =============
load_dotenv()

AZURE_OPENAI_API_KEY   = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT  = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_VER   = os.getenv("AZURE_OPENAI_API_VERSION")
MODEL_DEPLOYMENT_NAME  = os.getenv("MODEL_DEPLOYMENT_NAME")

IMAGES_FOLDER = r"C:/Users/Juan/Desktop/TFM/1000/out_profile_images_prompts/images_with_ids"
OUTPUT_FOLDER = r"C:/Users/Juan/Desktop/TFM/1000/profile_eval_GPT"
DELAY_SECONDS = 0.6
MAX_RETRIES   = 3

# base prompt
PROMPT_BASE = (
    "You are an expert in demographic visual classification. Your task is to analyze the given "
    "profile portrait image and determine the following attributes based purely on visual cues "
    "(facial structure, skin tone, features, hairstyle, and apparent age):\n"
    "1) Ethnicity — select exactly one option from the predefined list below.\n"
    "2) Gender — choose exactly one: male, female, or other.\n"
    "3) Age — estimate an approximate age in whole years.\n"
    "Do not invent new categories. Do not output null or empty fields. If uncertain, choose the single closest option.\n"
    "---\n"
    "Ethnicity options:\n"
    "1. Sub-Saharan African (Nigeria, Kenya, Ethiopia, South Africa, etc.)\n"
    "2. North African & Middle Eastern (MENA) (Egypt, Morocco, Saudi Arabia, Iran, etc.)\n"
    "3. European (Southern / Mediterranean) (Italy, Spain, Greece, Portugal, etc.)\n"
    "4. European (Northern & Eastern) (Germany, Poland, Sweden, Russia, etc.)\n"
    "5. South Asian (India, Pakistan, Sri Lanka, Nepal, etc.)\n"
    "6. East Asian (China, Korea, Japan, Mongolia, etc.)\n"
    "7. Southeast Asian (Vietnam, Thailand, Philippines, Indonesia, etc.)\n"
    "8. North American (USA, Canada, Greenland, etc.)\n"
    "9. Central & South American (Mexico, Peru, Bolivia, Chile, etc.)\n"
    "10. Oceanian / Pacific Islander (Fiji, Samoa, Papua New Guinea, Hawaii, etc.)\n"
    "---\n"
    "Output format (return exactly this JSON object, no extra text):\n"
    '{ "ethnicity": "<exact label from the list>", "gender": "<male | female | other>", "age": <integer> }'
)

# mini few-shot to force format (model sees this as reference, not as current answer)
FEWSHOT_USER  = 'Classify the image using the rules. Return only the JSON object.'
FEWSHOT_ASSIST= '{ "ethnicity": "European (Northern & Eastern) (Germany, Poland, Sweden, Russia, etc.)", "gender": "male", "age": 32 }'

# ============= INIT CLIENT =============
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_version=AZURE_OPENAI_API_VER
)

# ============= HELPERS =============

def parse_dialogue_id_and_speaker(filename: str) -> Tuple[str, str]:
    base = os.path.splitext(filename)[0]
    m = re.match(r"(.+)_([ABab])$", base)
    if m:
        return m.group(1), m.group(2).upper()
    return base, "?"


def safe_json_load(s: str) -> Optional[dict]:
    try:
        return json.loads(s)
    except Exception:
        return None


def make_data_url_from_image(path: str, max_side: int = 768, jpeg_quality: int = 85) -> str:
    """
    Opens the image, converts to rgb, resizes if it exceeds max_side,
    re-encodes to jpeg with given quality, and returns a data url string.
    """
    with Image.open(path) as im:
        # convert to rgb (avoids png alpha issues)
        im = im.convert("RGB")
        w, h = im.size
        if max(w, h) > max_side:
            if w >= h:
                new_w = max_side
                new_h = int(h * (max_side / w))
            else:
                new_h = max_side
                new_w = int(w * (max_side / h))
            im = im.resize((new_w, new_h), Image.LANCZOS)

        buf = BytesIO()
        im.save(buf, format="JPEG", quality=jpeg_quality, optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        return f"data:image/jpeg;base64,{b64}"


def call_vision(image_data_url: str) -> str:
    """
    Calls the multimodal model with the prompt and image (as jpeg data url).
    Returns raw text content (expects json).
    """
    resp = client.chat.completions.create(
        model=MODEL_DEPLOYMENT_NAME,
        messages=[
            {
                "role": "system",
                "content": "You are a strict, deterministic computer vision analyst. Output only the requested JSON object; no extra text."
            },
            # few-shot helps strictly enforce json format
            {"role": "user", "content": FEWSHOT_USER},
            {"role": "assistant", "content": FEWSHOT_ASSIST},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPT_BASE},
                    {"type": "image_url", "image_url": {"url": image_data_url}}
                ]
            }
        ]
        # temperature is omitted to avoid errors on deployments that do not accept it
    )
    return resp.choices[0].message.content.strip()

# ============= MAIN =============
def main():
    files = [f for f in os.listdir(IMAGES_FOLDER) if f.lower().endswith(".png")]
    files.sort()

    results_csv_path   = os.path.join(OUTPUT_FOLDER, "results.csv")
    results_jsonl_path = os.path.join(OUTPUT_FOLDER, "results.jsonl")

    with open(results_csv_path, "w", newline="", encoding="utf-8") as cf:
        writer = csv.writer(cf)
        writer.writerow(["filename", "dialogue_id", "speaker", "ethnicity", "gender", "age"])

    open(results_jsonl_path, "w", encoding="utf-8").close()

    ok, fail = 0, 0

    for idx, fname in enumerate(files, start=1):
        img_path = os.path.join(IMAGES_FOLDER, fname)
        dialogue_id, speaker = parse_dialogue_id_and_speaker(fname)

        print(f"[{idx}/{len(files)}] {fname}  (dialogue_id={dialogue_id}, speaker={speaker})")

        # robust data url (compressed jpeg)
        data_url = make_data_url_from_image(img_path, max_side=768, jpeg_quality=85)

        response_text = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response_text = call_vision(data_url)
                break
            except Exception as e:
                print(f"  Attempt {attempt} error: {e}")
                time.sleep(1.5)

        if response_text is None:
            print("  ERROR: no response after retries.")
            fail += 1
            time.sleep(DELAY_SECONDS)
            continue

        candidate = response_text.strip()
        # remove fences if returned with markdown code blocks
        candidate = re.sub(r"^```(?:json)?\s*|\s*```$", "", candidate,
                           flags=re.IGNORECASE | re.MULTILINE).strip()

        data = safe_json_load(candidate)
        if data is None:
            start, end = candidate.find("{"), candidate.rfind("}")
            if start != -1 and end != -1 and end > start:
                data = safe_json_load(candidate[start:end+1])

	# validation
        valid = (
            isinstance(data, dict) and
            all(k in data for k in ("ethnicity", "gender", "age")) and
            data["ethnicity"] not in (None, "", "null") and
            data["gender"]    not in (None, "", "null") and
            data["age"]       not in (None, "", "null")
        )

        if not valid:
            print("  ERROR: invalid or null JSON output -> saving raw for inspection.")
            raw_out = os.path.join(OUTPUT_FOLDER, f"{os.path.splitext(fname)[0]}_raw.txt")
            with open(raw_out, "w", encoding="utf-8") as rf:
                rf.write(response_text)
            fail += 1
            time.sleep(DELAY_SECONDS)
            continue

        out_json_path = os.path.join(OUTPUT_FOLDER, f"{os.path.splitext(fname)[0]}.json")
        with open(out_json_path, "w", encoding="utf-8") as jf:
            json.dump({
                "filename": fname,
                "dialogue_id": dialogue_id,
                "speaker": speaker,
                "ethnicity": data["ethnicity"],
                "gender": data["gender"],
                "age": data["age"],
            }, jf, ensure_ascii=False, indent=2)

	# append to csv
        with open(results_csv_path, "a", newline="", encoding="utf-8") as cf:
            writer = csv.writer(cf)
            writer.writerow([fname, dialogue_id, speaker, data["ethnicity"], data["gender"], data["age"]])

	# append to jsonl
        with open(results_jsonl_path, "a", encoding="utf-8") as jf:
            jf.write(json.dumps({
                "filename": fname,
                "dialogue_id": dialogue_id,
                "speaker": speaker,
                "ethnicity": data["ethnicity"],
                "gender": data["gender"],
                "age": data["age"],
            }, ensure_ascii=False) + "\n")

        ok += 1
        time.sleep(DELAY_SECONDS)

    print(f"\nDone. OK: {ok} | FAIL: {fail}")
    print(f"Per-image JSON & aggregated CSV/JSONL saved in: {OUTPUT_FOLDER}")

if __name__ == "__main__":
    main()
