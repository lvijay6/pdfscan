import unittest
import numpy as np
import cv2
import fitz
from backend.app.services.pdf_engine import PDFEngine

class TestPDFEngine(unittest.TestCase):
    def setUp(self):
        self.img1 = np.ones((200, 200, 3), dtype=np.uint8) * 255
        cv2.putText(self.img1, "Page 1", (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)

        self.img2 = np.ones((200, 200, 3), dtype=np.uint8) * 200
        cv2.putText(self.img2, "Page 2", (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)

    def test_images_to_pdf(self):
        pdf_bytes = PDFEngine.images_to_pdf([self.img1, self.img2])
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        self.assertEqual(doc.page_count, 2)
        doc.close()

    def test_searchable_pdf(self):
        pdf_bytes = PDFEngine.create_searchable_pdf([self.img1], ["Searchable Text 123"])
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = doc[0].get_text()
        self.assertIn("Searchable Text 123", text)
        doc.close()

    def test_protect_pdf(self):
        pdf_bytes = PDFEngine.images_to_pdf([self.img1])
        protected = PDFEngine.protect_pdf(pdf_bytes, "secret123")
        doc = fitz.open(stream=protected, filetype="pdf")
        self.assertTrue(doc.is_encrypted)
        self.assertTrue(doc.authenticate("secret123"))
        doc.close()

    def test_export_image(self):
        jpg_b = PDFEngine.export_image(self.img1, "JPG")
        png_b = PDFEngine.export_image(self.img1, "PNG")
        webp_b = PDFEngine.export_image(self.img1, "WEBP")
        self.assertTrue(len(jpg_b) > 0 and len(png_b) > 0 and len(webp_b) > 0)

    def test_split_and_merge_pdf(self):
        pdf_bytes = PDFEngine.images_to_pdf([self.img1, self.img2])
        splits = PDFEngine.split_pdf(pdf_bytes, [0, 1])
        self.assertEqual(len(splits), 2)

        merged = PDFEngine.merge_pdfs(splits)
        doc = fitz.open(stream=merged, filetype="pdf")
        self.assertEqual(doc.page_count, 2)
        doc.close()

if __name__ == "__main__":
    unittest.main()
