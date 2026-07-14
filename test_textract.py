"""
Test Textract OCR on a single prescription image.

Usage:
    python test_textract.py                          # runs on default image (1.jpeg)
    python test_textract.py path/to/image.jpeg       # runs on a specific image
"""

import sys
import os
from textract_service import extract_text_from_file

DATASET_DIR = "dataset/curated-handwritten-printed-dataset/Dataset/Dataset/images"


def test_single_image(image_path):
    """Run Textract on a single image and print the results."""
    print(f"\nImage: {image_path}")
    print("=" * 60)

    if not os.path.exists(image_path):
        print(f"[ERROR] File not found: {image_path}")
        return None

    text = extract_text_from_file(image_path)

    if text:
        print(f"\n--- Extracted Text ({len(text)} chars) ---")
        print(text)
        print("--- End ---\n")
    else:
        print("[WARNING] No text extracted from this image.")

    return text


if __name__ == "__main__":
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        image_path = os.path.join(DATASET_DIR, "1.jpeg")

    test_single_image(image_path)
