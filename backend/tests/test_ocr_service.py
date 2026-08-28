import unittest
import numpy as np
import cv2
from backend.app.services.ocr_service import OCREngine

class TestOCREngine(unittest.TestCase):
    def setUp(self):
        self.img = np.ones((150, 500, 3), dtype=np.uint8) * 255
        cv2.putText(self.img, "INVOICE #10294", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 2)

    def test_extract_text(self):
        text = OCREngine.extract_text(self.img)
        self.assertIn("INVOICE", text.upper())

    def test_extract_detailed_data(self):
        data = OCREngine.extract_detailed_data(self.img)
        self.assertIn("words", data)
        self.assertTrue(len(data["words"]) > 0)

    def test_classify_document(self):
        self.assertEqual(OCREngine.classify_document("TAX INVOICE GSTIN: 27AAAAA0000A1Z5"), "GST Bill")
        self.assertEqual(OCREngine.classify_document("INVOICE Total Amount Due: $150"), "Invoice")
        self.assertEqual(OCREngine.classify_document("RECEIPT Payment Received Thank You"), "Receipt")
        self.assertEqual(OCREngine.classify_document("PASSPORT REPUBLIC OF INDIA"), "Passport")
        self.assertEqual(OCREngine.classify_document("INCOME TAX DEPARTMENT PERMANENT ACCOUNT NUMBER ABCDE1234F"), "PAN Card")
        self.assertEqual(OCREngine.classify_document("Random text sample"), "General")

if __name__ == "__main__":
    unittest.main()
