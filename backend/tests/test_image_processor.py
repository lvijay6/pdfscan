import unittest
import numpy as np
import cv2
from backend.app.services.image_processor import ImageProcessor

class TestImageProcessor(unittest.TestCase):
    def setUp(self):
        self.img = np.ones((400, 300, 3), dtype=np.uint8) * 255
        cv2.rectangle(self.img, (50, 50), (250, 350), (0, 0, 0), -1)

    def test_detect_edges(self):
        pts = ImageProcessor.detect_edges(self.img)
        self.assertEqual(len(pts), 4)

    def test_four_point_transform(self):
        pts = [[50, 50], [250, 50], [250, 350], [50, 350]]
        warped = ImageProcessor.four_point_transform(self.img, pts)
        self.assertTrue(warped.shape[0] > 0 and warped.shape[1] > 0)

    def test_brightness_contrast(self):
        adjusted = ImageProcessor.adjust_brightness_contrast(self.img, brightness=1.2, contrast=1.5)
        self.assertEqual(adjusted.shape, self.img.shape)

    def test_apply_filters(self):
        for flt in ["original", "grayscale", "bw", "magic"]:
            filtered = ImageProcessor.apply_filter(self.img, flt)
            self.assertEqual(filtered.shape[:2], self.img.shape[:2])

    def test_rotate_image(self):
        rotated = ImageProcessor.rotate_image(self.img, 90)
        self.assertEqual(rotated.shape[0], 300)
        self.assertEqual(rotated.shape[1], 400)

if __name__ == "__main__":
    unittest.main()
