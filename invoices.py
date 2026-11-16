import pdfplumber 

def extract_pdf_text(pdf_path: str) -> str:
    full_text = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            # layout=True preserves the visual column alignment of the invoice
            text = page.extract_text(layout=True)
            
            if text:
                full_text.append(f"--- PAGE {page_num} ---\n{text}")
            else:
                full_text.append(f"--- PAGE {page_num} (No selectable text found) ---")

    return "\n\n".join(full_text)

def parse_pdf_invoice(file_path):
    text = extract_pdf_text(file_path)
    print(text)  # For debugging purposes

if __name__ == "__main__":
    pdf_file = "invoice.pdf"
    extracted = extract_pdf_text(pdf_file)
    print(extracted)