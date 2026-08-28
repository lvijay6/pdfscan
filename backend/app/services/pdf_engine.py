import fitz
import io
import cv2
import numpy as np
from PIL import Image

class PDFEngine:
    @staticmethod
    def images_to_pdf(image_list: list[np.ndarray]) -> bytes:
        doc = fitz.open()
        for img in image_list:
            if len(img.shape) == 2:
                pil_img = Image.fromarray(img)
            else:
                pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            img_buf = io.BytesIO()
            pil_img.save(img_buf, format="JPEG", quality=95)
            img_bytes = img_buf.getvalue()

            img_doc = fitz.open(stream=img_bytes, filetype="jpeg")
            rect = img_doc[0].rect
            page = doc.new_page(width=rect.width, height=rect.height)
            page.insert_image(rect, stream=img_bytes)
            img_doc.close()

        pdf_bytes = doc.tobytes()
        doc.close()
        return pdf_bytes

    @staticmethod
    def create_searchable_pdf(image_list: list[np.ndarray], ocr_texts: list[str]) -> bytes:
        doc = fitz.open()
        for img, text in zip(image_list, ocr_texts):
            if len(img.shape) == 2:
                pil_img = Image.fromarray(img)
            else:
                pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            img_buf = io.BytesIO()
            pil_img.save(img_buf, format="JPEG", quality=95)
            img_bytes = img_buf.getvalue()

            img_doc = fitz.open(stream=img_bytes, filetype="jpeg")
            rect = img_doc[0].rect
            page = doc.new_page(width=rect.width, height=rect.height)
            page.insert_image(rect, stream=img_bytes)

            if text:
                text_rect = fitz.Rect(10, rect.height - 30, rect.width - 10, rect.height - 5)
                page.insert_textbox(text_rect, text, fontsize=6, render_mode=3)
            img_doc.close()

        pdf_bytes = doc.tobytes()
        doc.close()
        return pdf_bytes

    @staticmethod
    def protect_pdf(pdf_bytes: bytes, user_password: str, owner_password: str = None) -> bytes:
        if not owner_password:
            owner_password = user_password
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        protected_bytes = doc.tobytes(
            encryption=fitz.PDF_ENCRYPT_AES_128,
            user_pw=user_password,
            owner_pw=owner_password,
            permissions=fitz.PDF_PERM_ACCESSIBILITY | fitz.PDF_PERM_PRINT
        )
        doc.close()
        return protected_bytes

    @staticmethod
    def compress_pdf(pdf_bytes: bytes, deflate: bool = True) -> bytes:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        compressed_bytes = doc.tobytes(
            garbage=4,
            deflate=deflate,
            clean=True
        )
        doc.close()
        return compressed_bytes

    @staticmethod
    def export_image(img: np.ndarray, format: str = "JPG") -> bytes:
        format_upper = format.upper()
        if format_upper == "JPG":
            format_upper = "JPEG"

        if len(img.shape) == 2:
            pil_img = Image.fromarray(img)
        else:
            pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

        buf = io.BytesIO()
        pil_img.save(buf, format=format_upper)
        return buf.getvalue()

    @staticmethod
    def merge_pdfs(pdf_list: list[bytes]) -> bytes:
        merged_doc = fitz.open()
        for pdf_bytes in pdf_list:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            merged_doc.insert_pdf(doc)
            doc.close()
        res = merged_doc.tobytes()
        merged_doc.close()
        return res

    @staticmethod
    def split_pdf(pdf_bytes: bytes, split_page_numbers: list[int]) -> list[bytes]:
        src_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        split_results = []
        for pg_no in split_page_numbers:
            if 0 <= pg_no < src_doc.page_count:
                new_doc = fitz.open()
                new_doc.insert_pdf(src_doc, from_page=pg_no, to_page=pg_no)
                split_results.append(new_doc.tobytes())
                new_doc.close()
        src_doc.close()
        return split_results
