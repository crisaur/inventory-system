import sys
import re
import numpy as np
from PIL import Image, ImageOps, ImageEnhance
from rapidocr_onnxruntime import RapidOCR
import pdfplumber
from database import upsert_product

ocr_engine = RapidOCR(
    limit_side_len=1440,
    unclip_ratio=1.9,
    box_tresh=0.4,
    text_score=0.45,
    use_angle_cls=False,
)

def preprocess_invoice_image(image_source) -> np.ndarray:
    img = Image.open(image_source)
    img = ImageOps.exif_transpose(img)
    img = img.convert("L").convert("RGB")
    img = ImageEnhance.Contrast(img).enhance(1.4)
    img = ImageEnhance.Sharpness(img).enhance(1.5)
    return np.array(img)

def clean_sku_digits(token: str) -> str:
    t = token.strip().upper()
    return (
        t.replace("O", "0").replace("Q", "0")
         .replace("I", "1").replace("L", "1")
         .replace("S", "5").replace("B", "8")
    )

def normalise_photo_row(left_words: list[dict], right_words: list[dict]) -> dict | None:
    left_text = " ".join(w["text"] for w in left_words)
    right_text = " ".join(w["text"] for w in right_words)

    if "SUB-TOTAL" in left_text.upper() or "VOID" in left_text.upper():
        return None
    if re.search(r"\b\d+-", right_text):
        return None

    sku = None
    for token in left_text.split():
        fixed = clean_sku_digits(token)
        if re.fullmatch(r"\d{6}", fixed):
            sku = int(fixed)
            break

    if not sku:
        return None

    clean_name = re.sub(r"\b[0-9OQILSB]{6}\b", "", left_text, count=1, flags=re.IGNORECASE)
    clean_name = re.sub(r"-{2,}", "", clean_name)
    clean_name = " ".join(clean_name.split()).strip()

    # RRP is the last 2-decimal number on the right: [PRICE, VALUE, RRP]
    prices = re.findall(r"\b\d+\.\d{2}\b", right_text.replace(",", "."))
    if len(prices) < 3:
        return None

    return {
        "sku": sku,
        "name": clean_name,
        "price": float(prices[-1]),
    }

def process_invoice_photo(image_source, return_debug: bool = False):
    img_np = preprocess_invoice_image(image_source)
    img_width = img_np.shape[1]

    ocr_result, _ = ocr_engine(img_np)
    if not ocr_result:
        return ([], []) if return_debug else []

    words = []
    for box, text, score in ocr_result:
        x0 = min(pt[0] for pt in box)
        top = sum(pt[1] for pt in box) / 4
        words.append({"text": text.strip(), "x0": round(x0, 1), "top": round(top, 1), "score": round(score, 2)})

    # Anchor on VAT flag ("A" or "B") on the right side of the page
    vat_anchors = sorted(
        [w for w in words if w["text"] in ("A", "B") and w["x0"] > img_width * 0.55],
        key=lambda w: w["top"],
    )

    results = []
    split_x = img_width * 0.45

    for idx, anchor in enumerate(vat_anchors):
        y_min = anchor["top"] - 45 if idx == 0 else (vat_anchors[idx - 1]["top"] + anchor["top"]) / 2
        y_max = (anchor["top"] + vat_anchors[idx + 1]["top"]) / 2 if idx + 1 < len(vat_anchors) else anchor["top"] + 45

        band_words = [w for w in words if y_min <= w["top"] < y_max]

        left_words = sorted([w for w in band_words if w["x0"] < split_x], key=lambda w: (round(w["top"] / 15), w["x0"]))
        right_words = sorted([w for w in band_words if w["x0"] >= split_x], key=lambda w: w["x0"])

        product = normalise_photo_row(left_words, right_words)
        if not product:
            continue

        results.append(upsert_product(**product))

    return (results, words) if return_debug else results

def process_booker_invoice(pdf_source) -> list[dict]:
    results = []
    with pdfplumber.open(pdf_source) as pdf:
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
                status_log = upsert_product(sku=sku, name=clean_name, price=rrp)
                results.append(status_log)
    return results

if __name__ == "__main__":
    # Allows running: python invoices.py new_invoice.pdf
    pdf_file = sys.argv[1] if len(sys.argv) > 1 else "Booker-Invoice-0425911.pdf"
    process_booker_invoice(pdf_file)