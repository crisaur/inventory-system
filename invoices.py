import sys
import re
import pdfplumber
from database import upsert_product

def process_booker_invoice(pdf_path: str):
    print(f"Scanning {pdf_path}...")
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            words = page.extract_words()
            if not words:
                continue

            vat_anchors = [
                w for w in words
                if w["text"] in ("A", "B") and w["x0"] > 350
            ]
            vat_anchors.sort(key=lambda w: w["top"])

            for idx, anchor in enumerate(vat_anchors):
                y_min = anchor["top"] - 22 if idx == 0 else (vat_anchors[idx - 1]["top"] + anchor["top"]) / 2
                y_max = (anchor["top"] + vat_anchors[idx + 1]["top"]) / 2 if idx + 1 < len(vat_anchors) else anchor["top"] + 22

                band_words = [w for w in words if y_min <= w["top"] < y_max]

                left_words = sorted(
                    [w for w in band_words if w["x0"] < 340],
                    key=lambda w: (round(w["top"], 1), w["x0"])
                )
                right_words = sorted(
                    [w for w in band_words if w["x0"] >= 340],
                    key=lambda w: w["x0"]
                )

                left_text = " ".join(w["text"] for w in left_words)
                right_text = " ".join(w["text"] for w in right_words)

                if "VOID NOTE" in left_text or "SUB-TOTAL" in left_text:
                    continue
                if re.search(r"\b\d+-", right_text):
                    continue

                sku_match = re.search(r"\b(\d{6})\b", left_text)
                if not sku_match:
                    continue
                sku = int(sku_match.group(1))

                clean_name = re.sub(rf"\b{sku}\b", "", left_text).strip()
                clean_name = " ".join(clean_name.split())

                prices = re.findall(r"\b\d+\.\d{2}\b", right_text)
                if len(prices) < 3:
                    continue

                rrp = float(prices[-1])

                # Searches inventory.db -> updates if higher, skips if lower/equal, adds if new
                upsert_product(sku=sku, name=clean_name, price=rrp)

if __name__ == "__main__":
    # Allows running: python invoices.py new_invoice.pdf
    pdf_file = sys.argv[1] if len(sys.argv) > 1 else "Booker-Invoice-0425911.pdf"
    process_booker_invoice(pdf_file)