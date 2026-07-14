# AWS Textract POC

A proof-of-concept pipeline that extracts text from medical prescription images using Amazon Textract and analyzes the extracted text with Amazon Comprehend Medical to identify medications, dosages, and protected health information.

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Add your AWS credentials to a `.env` file:
   ```
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_DEFAULT_REGION=us-east-1
   ```

## Usage

Run the Streamlit UI:
```
streamlit run app.py
```

Or run the pipeline from the command line:
```
python main.py path/to/prescription_image.jpeg
```

## Project Structure

- `app.py` - Streamlit frontend
- `main.py` - End-to-end pipeline (Textract + Comprehend Medical)
- `textract_service.py` - Textract OCR extraction logic
- `test_textract.py` - Standalone Textract testing script
