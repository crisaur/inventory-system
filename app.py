import streamlit as st
from sqlalchemy import select
from database import engine, inventory_table
from invoices import process_booker_invoice
from invoices import process_invoice_photo

def render_markdown_table(rows: list[dict]):
    """Renders a list of dicts as a clean Markdown table without pandas/pyarrow."""
    if not rows:
        return

    headers = list(rows[0].keys())
    header_line = "| " + " | ".join(str(h) for h in headers) + " |"
    separator_line = "| " + " | ".join("---" for _ in headers) + " |"

    body_lines = []
    for row in rows:
        cells = []
        for h in headers:
            val = row[h]
            if isinstance(val, float):
                cells.append(f"£{val:.2f}")
            elif val is None:
                cells.append("-")
            else:
                # Escape pipe characters so product names don't split columns
                cells.append(str(val).replace("|", "/"))
        body_lines.append("| " + " | ".join(cells) + " |")

    st.markdown("\n".join([header_line, separator_line] + body_lines))    

st.title("Invoice Price Updater")

# 1. File Uploader
uploaded_file = st.file_uploader("Upload Booker PDF Invoice", type=["pdf"])
camera_photo = st.camera_input("Or take a photo of the invoice")
uploaded_photo = st.file_uploader("Or upload a photo of the invoice", type=["jpg", "jpeg", "png"])
show_debug = st.checkbox("Show raw OCR words detected", value=False)

image = camera_photo or uploaded_photo

if image is not None:
    with st.spinner("Scanning invoice with RapidOCR..."):
        logs, raw_words = process_invoice_photo(image, return_debug=True)

    if logs:
        st.success(f"Matched {len(logs)} invoice rows.")
        render_markdown_table(logs)
    else:
        st.warning("No valid SKU/RRP rows matched. Check 'Show raw OCR words detected' below to see what the camera read.")

    if show_debug and raw_words:
        st.subheader("Raw OCR Words Detected")
        render_markdown_table(raw_words)

if uploaded_file is not None:
    if st.button("Process Invoice"):
        logs = process_booker_invoice(uploaded_file)
        st.success(f"Processed {len(logs)} items from invoice.")
        render_markdown_table(logs)

st.subheader("Current Inventory Database")
with engine.connect() as conn:
    rows = conn.execute(select(inventory_table)).mappings().all()
    st.markdown(rows)