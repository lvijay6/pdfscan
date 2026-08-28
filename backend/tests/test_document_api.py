import unittest
import cv2
import numpy as np
import io
import uuid
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.image_processor import ImageProcessor

class TestDocumentAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        uid = str(uuid.uuid4())[:8]
        email = f"doc_user_{uid}@example.com"
        res_u = cls.client.post("/api/v1/auth/signup", json={
            "name": "Doc User",
            "email": email,
            "password": "Password123!"
        })
        cls.user_id = res_u.json()["user"]["id"]

        img = np.ones((300, 300, 3), dtype=np.uint8) * 255
        cv2.putText(img, "INVOICE #9988", (30, 150), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)
        img_bytes = ImageProcessor.to_bytes(img, "PNG")

        files = {"file": ("test.png", io.BytesIO(img_bytes), "image/png")}
        res_proc = cls.client.post("/api/v1/scan/process-page", files=files)
        cls.session_id = res_proc.json()["session_id"]

    def test_save_list_search_export(self):
        res_save = self.client.post("/api/v1/documents/save", json={
            "user_id": self.user_id,
            "session_id": self.session_id,
            "name": "Acme Invoice 2026",
            "document_type": "Invoice"
        })
        self.assertEqual(res_save.status_code, 200)
        doc_id = res_save.json()["document_id"]

        res_list = self.client.get(f"/api/v1/documents/list/{self.user_id}")
        self.assertEqual(res_list.status_code, 200)
        self.assertEqual(len(res_list.json()["documents"]), 1)

        res_search = self.client.get(f"/api/v1/documents/list/{self.user_id}?search=INVOICE")
        self.assertEqual(res_search.status_code, 200)
        self.assertEqual(len(res_search.json()["documents"]), 1)

        res_detail = self.client.get(f"/api/v1/documents/detail/{doc_id}")
        self.assertEqual(res_detail.status_code, 200)
        self.assertEqual(len(res_detail.json()["pages"]), 1)

        res_export = self.client.post(f"/api/v1/documents/export/{doc_id}", json={
            "format": "searchable_pdf",
            "password": "secret_doc_pass",
            "compress": True
        })
        self.assertEqual(res_export.status_code, 200)
        self.assertEqual(res_export.headers["content-type"], "application/pdf")

if __name__ == "__main__":
    unittest.main()
