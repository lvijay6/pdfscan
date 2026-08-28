import pytesseract
import cv2
import numpy as np
from PIL import Image
import re

class OCREngine:
    @staticmethod
    def extract_text(img: np.ndarray) -> str:
        try:
            if len(img.shape) == 2:
                pil_img = Image.fromarray(img)
            else:
                pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            text = pytesseract.image_to_string(pil_img)
            return text.strip()
        except Exception as e:
            return f"[OCR Error: {str(e)}]"

    @staticmethod
    def extract_detailed_data(img: np.ndarray) -> dict:
        try:
            if len(img.shape) == 2:
                pil_img = Image.fromarray(img)
            else:
                pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            data = pytesseract.image_to_data(pil_img, output_type=pytesseract.Output.DICT)
            words = []
            n_boxes = len(data['text'])
            for i in range(n_boxes):
                text_item = data['text'][i].strip()
                if text_item:
                    words.append({
                        "text": text_item,
                        "left": data['left'][i],
                        "top": data['top'][i],
                        "width": data['width'][i],
                        "height": data['height'][i],
                        "confidence": float(data['conf'][i])
                    })
            return {"words": words}
        except Exception as e:
            return {"words": [], "error": str(e)}

    @staticmethod
    def classify_document(text: str) -> str:
        t = text.lower()
        if "gstin" in t or "gst bill" in t or ("tax invoice" in t and "gst" in t):
            return "GST Bill"
        elif "invoice" in t or "bill to" in t or "subtotal" in t:
            return "Invoice"
        elif "receipt" in t or "payment received" in t or "cashier" in t:
            return "Receipt"
        elif "passport" in t or "republic of" in t:
            return "Passport"
        elif "income tax department" in t or "permanent account number" in t or re.search(r'[A-Z]{5}[0-9]{4}[A-Z]{1}', text):
            return "PAN Card"
        elif "government of india" in t or "aadhaar" in t or re.search(r'\d{4}\s\d{4}\s\d{4}', text):
            return "Aadhaar Card"
        elif "identity card" in t or "id card" in t:
            return "ID Card"
        elif "agreement" in t or "contract" in t or "party of the first part" in t:
            return "Contract"
        return "General"
