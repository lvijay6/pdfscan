import unittest
import cv2
import numpy as np
import io
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.image_processor import ImageProcessor

class TestScanAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        img = np.ones((300, 300, 3), dtype=np.uint8) * 255
        cv2.putText(img, "TEST SCAN", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)
        cls.img_bytes = ImageProcessor.to_bytes(img, "PNG")

    def test_detect_edges_and_process(self):
        files = {"file": ("test.png", io.BytesIO(self.img_bytes), "image/png")}
        res_detect = self.client.post("/api/v1/scan/detect-edges", files=files)
        self.assertEqual(res_detect.status_code, 200)
        self.assertIn("crop_pts", res_detect.json())

        files_proc = {"file": ("test.png", io.BytesIO(self.img_bytes), "image/png")}
        res_proc = self.client.post("/api/v1/scan/process-page", files=files_proc, data={"filter_name": "bw"})
        self.assertEqual(res_proc.status_code, 200)
        json_data = res_proc.json()
        self.assertIn("session_id", json_data)
        sid = json_data["session_id"]

        res_prev = self.client.get(f"/api/v1/scan/preview/{sid}")
        self.assertEqual(res_prev.status_code, 200)
        self.assertEqual(len(res_prev.json()["pages"]), 1)

    def test_edit_and_reorder(self):
        files = {"file": ("test.png", io.BytesIO(self.img_bytes), "image/png")}
        res_proc = self.client.post("/api/v1/scan/process-page", files=files)
        sid = res_proc.json()["session_id"]

        res_edit = self.client.post("/api/v1/scan/edit-page", json={
            "session_id": sid,
            "page_index": 0,
            "rotation": 90,
            "brightness": 1.1,
            "contrast": 1.2,
            "filter_name": "magic"
        })
        self.assertEqual(res_edit.status_code, 200)

if __name__ == "__main__":
    unittest.main()
