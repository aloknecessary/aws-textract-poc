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

def extract_medical_insights(comprehend_client, raw_text):
    """Passes raw text to Comprehend Medical and organizes all detected entities."""
    try:
        print("[2/3] Analyzing text with Amazon Comprehend Medical...")
        response = comprehend_client.detect_entities_v2(Text=raw_text)

        structured_data = {
            "medications": [],
            "medical_conditions": [],
            "anatomy": [],
            "test_treatment_procedures": [],
            "protected_health_information": [],
            "behavioral_environmental_social": [],
            "time_expressions": [],
        }

        for entity in response.get('Entities', []):
            category = entity.get('Category')
            base_info = {
                "text": entity.get('Text'),
                "type": entity.get('Type'),
                "confidence": round(entity.get('Score', 0) * 100, 2),
                "traits": [t.get('Name') for t in entity.get('Traits', [])],
                "attributes": {}
            }
            for attr in entity.get('Attributes', []):
                attr_type = attr['Type'].lower()
                base_info["attributes"][attr_type] = {
                    "value": attr.get('Text'),
                    "confidence": round(attr.get('Score', 0) * 100, 2)
                }

            if category == 'MEDICATION':
                structured_data["medications"].append(base_info)

            elif category == 'MEDICAL_CONDITION':
                structured_data["medical_conditions"].append(base_info)

            elif category == 'ANATOMY':
                structured_data["anatomy"].append(base_info)

            elif category == 'TEST_TREATMENT_PROCEDURE':
                structured_data["test_treatment_procedures"].append(base_info)

            elif category == 'PROTECTED_HEALTH_INFORMATION':
                structured_data["protected_health_information"].append(base_info)

            elif category == 'BEHAVIORAL_ENVIRONMENTAL_SOCIAL':
                structured_data["behavioral_environmental_social"].append(base_info)

            elif category == 'TIME_EXPRESSION':
                structured_data["time_expressions"].append(base_info)

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
        image_path = os.path.join(DATASET_DIR, "1.jpeg")

    run_prescription_pipeline(image_path)
