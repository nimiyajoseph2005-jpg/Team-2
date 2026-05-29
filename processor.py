import pdfplumber

def extract_text_from_pdf(file_bytes):
    """
    Extract text from a PDF file using pdfplumber.
    """
    text = ""
    try:
        with pdfplumber.open(file_bytes) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return text
