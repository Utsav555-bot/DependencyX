import streamlit as st
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
import requests
import io

# -------------------------------
# PAGE CONFIG
# -------------------------------
st.set_page_config(
    page_title="Azure Document Intelligence",
    page_icon="📄",
    layout="wide"
)

# -------------------------------
# CUSTOM CSS
# -------------------------------
st.markdown("""
<style>
.main {
    background-color: #f5f7fa;
}

.title {
    font-size: 38px;
    font-weight: bold;
    color: #0078D4;
}

.subtitle {
    font-size: 18px;
    color: gray;
}

.stButton>button {
    width: 100%;
    background-color: #0078D4;
    color: white;
    border-radius: 10px;
    height: 45px;
    font-size: 16px;
}

.result-box {
    background: white;
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0px 4px 15px rgba(0,0,0,0.1);
}
</style>
""", unsafe_allow_html=True)

# -------------------------------
# HEADER
# -------------------------------
st.markdown('<p class="title">📄 Azure Document Intelligence Dashboard</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Upload documents or analyze image URLs using Azure OCR</p>', unsafe_allow_html=True)

# -------------------------------
# SIDEBAR CONFIG
# -------------------------------
st.sidebar.header("🔐 Azure Credentials")

azure_key = st.sidebar.text_input(
    "Azure API Key",
    type="password"
)

endpoint = st.sidebar.text_input(
    "Azure Endpoint",
    placeholder="https://your-resource.cognitiveservices.azure.com/"
)

# -------------------------------
# FUNCTION
# -------------------------------
def analyze_document(client, document_data):
    try:
        poller = client.begin_analyze_document(
            "prebuilt-read",
            body=document_data
        )

        result = poller.result()

        extracted_text = ""

        if result.pages:
            for page in result.pages:
                for line in page.lines:
                    extracted_text += line.content + "\n"

        return extracted_text

    except Exception as e:
        return f"Error: {str(e)}"

# -------------------------------
# TABS
# -------------------------------
tab1, tab2 = st.tabs(["📁 Upload Document", "🌐 Analyze Image URL"])

# -------------------------------
# TAB 1 - FILE UPLOAD
# -------------------------------
with tab1:
    st.subheader("Upload a Document")

    uploaded_file = st.file_uploader(
        "Upload PDF or Image",
        type=["pdf", "png", "jpg", "jpeg", "bmp", "tiff"]
    )

    if st.button("Analyze Uploaded Document"):

        if not azure_key or not endpoint:
            st.error("Please enter Azure Key and Endpoint.")
        elif uploaded_file is None:
            st.warning("Please upload a document.")
        else:
            try:
                client = DocumentIntelligenceClient(
                    endpoint=endpoint,
                    credential=AzureKeyCredential(azure_key)
                )

                file_bytes = uploaded_file.read()

                with st.spinner("Analyzing document..."):
                    text = analyze_document(client, file_bytes)

                st.success("Analysis Complete")

                st.markdown("### Extracted Text")
                st.text_area(
                    "OCR Output",
                    text,
                    height=350
                )

                st.download_button(
                    "Download Text",
                    text,
                    file_name="extracted_text.txt"
                )

            except Exception as e:
                st.error(str(e))

# -------------------------------
# TAB 2 - URL ANALYSIS
# -------------------------------
with tab2:
    st.subheader("Analyze Image via URL")

    image_url = st.text_input(
        "Enter Image URL"
    )

    if st.button("Analyze Image URL"):

        if not azure_key or not endpoint:
            st.error("Please enter Azure Key and Endpoint.")
        elif not image_url:
            st.warning("Please enter an image URL.")
        else:
            try:
                client = DocumentIntelligenceClient(
                    endpoint=endpoint,
                    credential=AzureKeyCredential(azure_key)
                )

                response = requests.get(image_url)

                if response.status_code == 200:
                    image_bytes = response.content

                    with st.spinner("Analyzing image..."):
                        text = analyze_document(
                            client,
                            image_bytes
                        )

                    st.success("Analysis Complete")

                    st.image(
                        image_url,
                        caption="Input Image",
                        width=500
                    )

                    st.markdown("### Extracted Text")

                    st.text_area(
                        "OCR Output",
                        text,
                        height=350
                    )

                    st.download_button(
                        "Download Text",
                        text,
                        file_name="image_ocr.txt"
                    )

                else:
                    st.error("Unable to fetch image URL")

            except Exception as e:
                st.error(str(e))