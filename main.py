import os
import sys
import json
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
from dotenv import load_dotenv

from textract_service import initialize_textract_client, extract_text_from_bytes

# Load credentials from .env file
load_dotenv()


def initialize_comprehend_client():
    """Initializes the AWS Comprehend Medical client."""
    try:
        comprehend_med = boto3.client('comprehendmedical')
        return comprehend_med
    except (NoCredentialsError, PartialCredentialsError):
        print("[ERROR] AWS Credentials not found. Please set your environment variables.")
        return None

COMPREHEND_MAX_CHARS = 20000


def _chunk_text(text, max_chars=COMPREHEND_MAX_CHARS):
    """Splits text into chunks that fit within Comprehend Medical's character limit."""
    return [text[i:i + max_chars] for i in range(0, len(text), max_chars)]


def extract_medical_insights(comprehend_client, raw_text):
    """Passes raw text to Comprehend Medical and organizes all detected entities."""
    try:
        print("[2/3] Analyzing text with Amazon Comprehend Medical...")

        structured_data = {
            "medications": [],
            "medical_conditions": [],
            "anatomy": [],
            "test_treatment_procedures": [],
            "protected_health_information": [],
            "behavioral_environmental_social": [],
            "time_expressions": [],
        }

        category_map = {
            'MEDICATION': "medications",
            'MEDICAL_CONDITION': "medical_conditions",
            'ANATOMY': "anatomy",
            'TEST_TREATMENT_PROCEDURE': "test_treatment_procedures",
            'PROTECTED_HEALTH_INFORMATION': "protected_health_information",
            'BEHAVIORAL_ENVIRONMENTAL_SOCIAL': "behavioral_environmental_social",
            'TIME_EXPRESSION': "time_expressions",
        }

        for chunk in _chunk_text(raw_text):
            response = comprehend_client.detect_entities_v2(Text=chunk)
            for entity in response.get('Entities', []):
                category = entity.get('Category')
                if category not in category_map:
                    continue
                base_info = {
                    "text": entity.get('Text'),
                    "type": entity.get('Type'),
                    "confidence": round(entity.get('Score', 0) * 100, 2),
                    "traits": [t.get('Name') for t in entity.get('Traits', [])],
                    "attributes": {}
                }
                for attr in entity.get('Attributes', []):
                    base_info["attributes"][attr['Type'].lower()] = {
                        "value": attr.get('Text'),
                        "confidence": round(attr.get('Score', 0) * 100, 2)
                    }
                structured_data[category_map[category]].append(base_info)

        return structured_data

    except ClientError as e:
        print(f"[ERROR] Comprehend Medical API call failed: {e.response['Error']['Message']}")
        return None

def run_prescription_pipeline(local_image_path):
    """Main execution block running the end-to-end extraction pipeline."""
    if not os.path.exists(local_image_path):
        print(f"[ERROR] Local file path does not exist: {local_image_path}")
        return

    # Initialize AWS clients
    textract = initialize_textract_client()
    comprehend = initialize_comprehend_client()
    if not textract or not comprehend:
        return

    # Read local image file as binary bytes
    with open(local_image_path, 'rb') as file:
        raw_image_bytes = file.read()

    # Run Step 1: Textract
    extracted_text = extract_text_from_bytes(textract, raw_image_bytes)
    if not extracted_text:
        print("[ERROR] Pipeline terminated during text extraction.")
        return

    print("\n--- Raw OCR Text Output ---")
    print(extracted_text)
    print("---------------------------\n")

    # Run Step 2: Comprehend Medical
    final_output = extract_medical_insights(comprehend, extracted_text)

    if final_output:
        print("[3/3] Pipeline complete! Structured Results:")
        print(json.dumps(final_output, indent=2))
        return final_output


DATASET_DIR = "dataset/test"

if __name__ == "__main__":
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        image_path = os.path.join(DATASET_DIR, "90.jpg")

    run_prescription_pipeline(image_path)
