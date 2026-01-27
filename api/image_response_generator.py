import os
import json
import time
import base64
import requests
from dotenv import load_dotenv
from openai import AzureOpenAI

# load env
load_dotenv()

AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
MODEL_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME")  # gpt-image-1

# config
INPUT_FOLDER = "out/prompts_images"
OUTPUT_FOLDER = "out/images"
LOG_FILE = os.path.join(OUTPUT_FOLDER, "generation_log.txt")

DELAY_BETWEEN_REQUESTS = 1  # seconds
COST_PER_IMAGE_USD = 0.04  # estimation

# prepare folders
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# initialize client
client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_version=API_VERSION
)


def download_image(url, output_path):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            print(f"Saved image from URL: {output_path}")
        else:
            print(f"Failed to download image from {url}: Status code {response.status_code}")
    except Exception as e:
        print(f"Error downloading image: {e}")


def save_base64_image(b64_data, output_path):
    try:
        image_data = base64.b64decode(b64_data)
        with open(output_path, "wb") as f:
            f.write(image_data)
        print(f"Saved image from base64: {output_path}")
    except Exception as e:
        print(f"Error saving base64 image: {e}")


# main loop
prompt_files = sorted([f for f in os.listdir(INPUT_FOLDER) if f.endswith(".json")])
print(f"Found {len(prompt_files)} prompt files to process.\n")

total_cost = 0.0
log_entries = []

for idx, prompt_file in enumerate(prompt_files, 1):
    input_path = os.path.join(INPUT_FOLDER, prompt_file)
    
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        persona_id = data["persona_id"]
        prompt_text = data["prompt"]

        print(f"[{idx}/{len(prompt_files)}] Generating image for: {prompt_file}")

        # api call
        response = client.images.generate(
            model=MODEL_DEPLOYMENT_NAME,
            prompt=prompt_text,
            n=1,
            size="1024x1024"
        )

        # handle response
        image_data_obj = response.data[0]

        if hasattr(image_data_obj, "url") and image_data_obj.url:
            image_url = image_data_obj.url
            output_image_path = os.path.join(OUTPUT_FOLDER, f"{prompt_file[:-5]}.png")
            download_image(image_url, output_image_path)
            log_entries.append(f"{prompt_file}: URL: {image_url}")

        elif hasattr(image_data_obj, "b64_json") and image_data_obj.b64_json:
            b64_image = image_data_obj.b64_json
            output_image_path = os.path.join(OUTPUT_FOLDER, f"{prompt_file[:-5]}.png")
            save_base64_image(b64_image, output_image_path)
            log_entries.append(f"{prompt_file}: base64 image saved")

        elif hasattr(image_data_obj, "image_base64") and image_data_obj.image_base64:
            b64_image = image_data_obj.image_base64
            output_image_path = os.path.join(OUTPUT_FOLDER, f"{prompt_file[:-5]}.png")
            save_base64_image(b64_image, output_image_path)
            log_entries.append(f"{prompt_file}: base64 image saved")

        else:
            print(f"No image found in response for {prompt_file}")
            log_entries.append(f"{prompt_file}: ERROR: No image found in response.")

        # update cost
        total_cost += COST_PER_IMAGE_USD

    except Exception as e:
        print(f"Error processing {prompt_file}: {e}")
        log_entries.append(f"{prompt_file}: ERROR: {e}")

    # wait between requests
    print(f"Sleeping {DELAY_BETWEEN_REQUESTS} seconds to respect rate limits...\n")
    time.sleep(DELAY_BETWEEN_REQUESTS)

# final log
with open(LOG_FILE, "w", encoding="utf-8") as log_f:
    log_f.write("\n".join(log_entries))

print("\nAll done.")
print(f"Total estimated cost: ${total_cost:.2f}")
print(f"Log saved to: {LOG_FILE}")
