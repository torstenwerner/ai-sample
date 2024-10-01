import PyPDF2

def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a PDF file.

    Args:
        pdf_path (str): Path to the PDF file.

    Returns:
        str: Extracted text.
    """
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                else:
                    print(f"Warning: No text found on page {page_num + 1}.")
    except Exception as e:
        print(f"Error reading PDF file: {e}")
    return text

# Example usage
pdf_path = 'SAFE_Verzeichnisdienst_V1_5.pdf'
pdf_text = extract_text_from_pdf(pdf_path)
print(pdf_text)
