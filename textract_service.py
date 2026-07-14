import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()


def initialize_textract_client():
    """Initializes the AWS Textract client using the environment's configuration."""
    try:
        textract = boto3.client('textract')
        return textract
    except (NoCredentialsError, PartialCredentialsError):
        print("[ERROR] AWS Credentials not found. Please check your .env file.")
        return None


def extract_text_from_bytes(textract_client, image_bytes):
    """Passes raw image bytes to Textract and rebuilds the text block."""
    try:
        print("[Textract] Sending image bytes to Amazon Textract...")
        response = textract_client.detect_document_text(
            Document={'Bytes': image_bytes}
        )

        # Stitch individual text lines back together with line breaks
        extracted_lines = []
        for block in response.get('Blocks', []):
            if block['BlockType'] == 'LINE':
                extracted_lines.append(block['Text'])

        full_text = "\n".join(extracted_lines)
        return full_text

    except ClientError as e:
        print(f"[ERROR] Textract API call failed: {e.response['Error']['Message']}")
        return None


def extract_text_from_file(image_path):
    """Convenience function: reads a local image file and extracts text via Textract."""
    client = initialize_textract_client()
    if not client:
        return None

    with open(image_path, 'rb') as f:
        image_bytes = f.read()

    return extract_text_from_bytes(client, image_bytes)
