import html
import streamlit as st
from io import BytesIO
from PIL import Image
from textract_service import initialize_textract_client, extract_text_from_bytes
from main import initialize_comprehend_client, extract_medical_insights

st.set_page_config(page_title="Prescription Parser", layout="centered")

# Modern light theme styling
st.markdown(
    """
    <style>
    .stApp {
        background-color: #fafafa;
    }
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        color: #1a1a2e;
        margin-bottom: 0.25rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #6b7280;
        margin-bottom: 2rem;
    }
    .section-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: #1a1a2e;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
    }
    .card {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .med-name {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 0.5rem;
    }
    .med-attr {
        font-size: 0.9rem;
        color: #475569;
        margin: 0.2rem 0;
    }
    .confidence-badge {
        display: inline-block;
        background-color: #ecfdf5;
        color: #065f46;
        font-size: 0.8rem;
        font-weight: 500;
        padding: 0.2rem 0.6rem;
        border-radius: 9999px;
        margin-left: 0.5rem;
    }
    .phi-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.6rem 0;
        border-bottom: 1px solid #f3f4f6;
    }
    .phi-row:last-child {
        border-bottom: none;
    }
    .phi-type {
        font-size: 0.85rem;
        font-weight: 500;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.025em;
    }
    .phi-value {
        font-size: 0.95rem;
        font-weight: 500;
        color: #1e293b;
    }
    .ocr-box {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1.25rem;
        font-family: 'SF Mono', 'Fira Code', monospace;
        font-size: 0.9rem;
        color: #374151;
        white-space: pre-wrap;
        line-height: 1.6;
    }
    .med-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.9rem;
    }
    .med-table thead th {
        text-align: left;
        padding: 0.75rem 0.75rem;
        font-weight: 600;
        color: #6b7280;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        border-bottom: 2px solid #e5e7eb;
    }
    .med-table tbody td {
        padding: 0.75rem 0.75rem;
        color: #1e293b;
        border-bottom: 1px solid #f3f4f6;
    }
    .med-table tbody tr:last-child td {
        border-bottom: none;
    }
    .med-table tbody tr:hover {
        background-color: #f9fafb;
    }
    .upload-area {
        background-color: #ffffff;
        border: 2px dashed #d1d5db;
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header
st.markdown('<div class="main-header">Prescription Parser</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Upload a prescription image to extract text and medical entities.</div>',
    unsafe_allow_html=True,
)

def render_entity_table(entities, title):
    if not entities:
        return
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)

    all_attr_keys = set()
    for e in entities:
        all_attr_keys.update(e.get("attributes", {}).keys())
    all_attr_keys = sorted(all_attr_keys)

    header = "<th>Entity</th><th>Type</th>"
    for key in all_attr_keys:
        header += f"<th>{key.replace('_', ' ').capitalize()}</th>"
    header += "<th>Traits</th><th>Confidence</th>"

    rows = ""
    for e in entities:
        attrs = e.get("attributes", {})
        traits = ", ".join(e.get("traits", [])) if e.get("traits") else "-"
        row = f"<td>{html.escape(e['text'])}</td><td>{html.escape(e.get('type', '-'))}</td>"
        for key in all_attr_keys:
            attr_val = attrs.get(key, {})
            val = attr_val.get('value', '-') if isinstance(attr_val, dict) else attr_val
            row += f"<td>{html.escape(str(val))}</td>"
        row += f"<td>{html.escape(traits)}</td>"
        row += f'<td><span class="confidence-badge">{e["confidence"]}%</span></td>'
        rows += f"<tr>{row}</tr>"

    st.markdown(
        f"""
        <div class="card" style="overflow-x: auto;">
            <table class="med-table">
                <thead><tr>{header}</tr></thead>
                <tbody>{rows}</tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )


# File upload
uploaded_file = st.file_uploader("Choose an image", type=["jpeg", "jpg", "png"], label_visibility="collapsed")

if uploaded_file is not None:
    st.image(uploaded_file, caption="Uploaded Image", width="stretch")

    if st.button("Analyze Prescription", use_container_width=True):
        # Convert uploaded image to JPEG bytes for Textract compatibility
        image = Image.open(uploaded_file)
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=95)
        image_bytes = buffer.getvalue()

        # Step 1: Textract OCR
        with st.spinner("Extracting text..."):
            textract_client = initialize_textract_client()
            if not textract_client:
                st.error("Failed to initialize Textract. Check your AWS credentials in .env.")
                st.stop()
            extracted_text = extract_text_from_bytes(textract_client, image_bytes)

        if not extracted_text:
            st.error("No text could be extracted from this image.")
            st.stop()

        # Display extracted text
        st.markdown('<div class="section-title">Extracted Text</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="ocr-box">{html.escape(extracted_text)}</div>', unsafe_allow_html=True)

        # Step 2: Comprehend Medical
        with st.spinner("Analyzing medical entities..."):
            comprehend_client = initialize_comprehend_client()
            if not comprehend_client:
                st.error("Failed to initialize Comprehend Medical. Check your AWS credentials in .env.")
                st.stop()
            insights = extract_medical_insights(comprehend_client, extracted_text)

        if not insights:
            st.warning("No medical insights returned.")
            st.stop()

        # Render all 7 categories
        render_entity_table(insights.get("medications", []), "Medications")
        render_entity_table(insights.get("medical_conditions", []), "Medical Conditions")
        render_entity_table(insights.get("test_treatment_procedures", []), "Tests, Treatments & Procedures")
        render_entity_table(insights.get("anatomy", []), "Anatomy")
        render_entity_table(insights.get("protected_health_information", []), "Protected Health Information")
        render_entity_table(insights.get("behavioral_environmental_social", []), "Behavioral, Environmental & Social")
        render_entity_table(insights.get("time_expressions", []), "Time Expressions")
