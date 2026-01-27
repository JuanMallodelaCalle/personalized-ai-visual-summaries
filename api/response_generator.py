import os
import json
import time
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

# configuration
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
MODEL_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME")

# paths
BASE_DIR = "out"
PROMPTS_DIR = os.path.join(BASE_DIR, "prompts")
BATCH_INPUT_FILE = "tmp/batch_input.jsonl"
BATCH_OUTPUT_FILE = "tmp/batch_output.jsonl"


def create_batch_input_file():
    # list prompt files
    prompt_files = [
        f for f in os.listdir(PROMPTS_DIR)
        if f.startswith("prompt_") and f.endswith(".txt")
    ]

    with open(BATCH_INPUT_FILE, "w", encoding="utf-8") as outfile:
        for prompt_file in prompt_files:
            # extract id from filename
            prompt_id = prompt_file[len("prompt_"):-len(".txt")]
            prompt_file_path = os.path.join(PROMPTS_DIR, prompt_file)

            with open(prompt_file_path, "r", encoding="utf-8") as pf:
                prompt_text = pf.read().strip()

            # build request body
            body = {
                "model": MODEL_DEPLOYMENT_NAME,
                "messages": [
                    {"role": "system", "content": "You are an AI assistant."},
                    {"role": "user", "content": prompt_text}
                ]
            }

            # construct batch object
            batch_obj = {
                "custom_id": f"prompt_{prompt_id}",
                "method": "POST",
                "url": "/chat/completions",
                "body": body
            }
            outfile.write(json.dumps(batch_obj) + "\n")

    print(f"Batch input file '{BATCH_INPUT_FILE}' created.")


def download_file(client, file_id, output_filename):
    # retrieve file content
    file_response = client.files.content(file_id)
    raw_responses = file_response.text.strip().split('\n')

    os.makedirs(os.path.join(BASE_DIR, 'response'), exist_ok=True)

    for raw_response in raw_responses:
        json_response = json.loads(raw_response)
        prompt_id = json_response['custom_id']
        response = json_response['response']['body']['choices'][0]['message']['content']

        # save individual response
        output_file_path = os.path.join(BASE_DIR, 'response', f"{prompt_id}.txt")
        with open(output_file_path, "w", encoding="utf-8") as output_file:
            output_file.write(response)

    # save full batch log
    with open(output_filename, "w", encoding="utf-8") as output_file:
        for raw_response in raw_responses:
            output_file.write(raw_response + "\n")

    print(f"Batch output file '{output_filename}' downloaded and saved to '{os.path.join(BASE_DIR, 'response')}'.")


def main():
    # step 1: create input file
    create_batch_input_file()

    # step 2: init client
    client = AzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_version=API_VERSION
    )

    # step 3: upload file
    with open(BATCH_INPUT_FILE, "rb") as f:
        file_upload = client.files.create(file=f, purpose="batch")
    file_id = file_upload.id
    print(f"Batch input file uploaded. File ID: {file_id}")

    # step 4: create batch job
    batch_response = client.batches.create(
        input_file_id=file_id,
        endpoint="/chat/completions",
        completion_window="24h"
    )
    batch_id = batch_response.id
    print(f"Batch job created. Batch ID: {batch_id}")

    # save batch id
    with open("tmp/batch_id.txt", "w", encoding="utf-8") as f:
        f.write(batch_id)

    # step 5: poll status
    status = batch_response.status
    print(f"Initial batch status: {status}")

    while status not in ("completed", "failed", "cancelled"):
        time.sleep(120)
        batch_response = client.batches.retrieve(batch_id)
        status = batch_response.status
        print(f"Batch ID: {batch_id}, Status: {status}")

    if status == "failed":
        print("Batch job failed:")
        if batch_response.errors:
            for error in batch_response.errors:
                print(f"Error code {error.get('code')}: {error.get('message')}")
        return
    elif status == "cancelled":
        print("Batch job was cancelled.")
        return
    else:
        print("Batch job completed successfully.")

    # step 6: retrieve output
    output_file_id = batch_response.output_file_id
    if output_file_id:
        download_file(client, output_file_id, BATCH_OUTPUT_FILE)
    else:
        print("No output file found in the batch response.")


if __name__ == "__main__":
    main()
