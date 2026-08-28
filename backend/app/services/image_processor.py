import cv2
import numpy as np
from PIL import Image, ImageEnhance
import io

class ImageProcessor:
    @staticmethod
    def load_image_from_bytes(image_bytes: bytes) -> np.ndarray:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img

    @staticmethod
    def to_bytes(img: np.ndarray, format: str = "PNG") -> bytes:
        if len(img.shape) == 2:
            pil_img = Image.fromarray(img)
        else:
            pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        buf = io.BytesIO()
        pil_img.save(buf, format=format)
        return buf.getvalue()

    @staticmethod
    def detect_edges(img: np.ndarray):
        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edged = cv2.Canny(blurred, 50, 200)

        contours, _ = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]

        screen_cnt = None
        for c in contours:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            if len(approx) == 4:
                screen_cnt = approx
                break

        if screen_cnt is not None:
            pts = screen_cnt.reshape(4, 2).tolist()
        else:
            pts = [
                [int(w * 0.05), int(h * 0.05)],
                [int(w * 0.95), int(h * 0.05)],
                [int(w * 0.95), int(h * 0.95)],
                [int(w * 0.05), int(h * 0.95)]
            ]
        return pts

    @staticmethod
    def four_point_transform(img: np.ndarray, pts: list) -> np.ndarray:
        pts_np = np.array(pts, dtype="float32")
        rect = np.zeros((4, 2), dtype="float32")
        s = pts_np.sum(axis=1)
        rect[0] = pts_np[np.argmin(s)]
        rect[2] = pts_np[np.argmax(s)]

        diff = np.diff(pts_np, axis=1)
        rect[1] = pts_np[np.argmin(diff)]
        rect[3] = pts_np[np.argmax(diff)]

        (tl, tr, br, bl) = rect

        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))

        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))

        dst = np.array([
            [0, 0],
            [maxWidth - 1, 0],
            [maxWidth - 1, maxHeight - 1],
            [0, maxHeight - 1]], dtype="float32")

        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(img, M, (maxWidth, maxHeight))
        return warped

    @staticmethod
    def remove_shadows_and_cleanup(img: np.ndarray) -> np.ndarray:
        rgb_planes = cv2.split(img)
        result_norm_planes = []
        for plane in rgb_planes:
            dilated_img = cv2.dilate(plane, np.ones((7,7), np.uint8))
            bg_img = cv2.medianBlur(dilated_img, 21)
            diff_img = 255 - cv2.absdiff(plane, bg_img)
            norm_img = cv2.normalize(diff_img, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)
            result_norm_planes.append(norm_img)
        result = cv2.merge(result_norm_planes)
        return result

    @staticmethod
    def adjust_brightness_contrast(img: np.ndarray, brightness: float = 1.0, contrast: float = 1.0) -> np.ndarray:
        pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        if brightness != 1.0:
            enhancer = ImageEnhance.Brightness(pil_img)
            pil_img = enhancer.enhance(brightness)
        if contrast != 1.0:
            enhancer = ImageEnhance.Contrast(pil_img)
            pil_img = enhancer.enhance(contrast)
        res = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        return res

    @staticmethod
    def apply_filter(img: np.ndarray, filter_name: str) -> np.ndarray:
        filter_name = filter_name.lower()
        if filter_name == "grayscale":
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        elif filter_name in ["bw", "black_and_white"]:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            bw = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 10)
            return cv2.cvtColor(bw, cv2.COLOR_GRAY2BGR)
        elif filter_name == "magic":
            cleaned = ImageProcessor.remove_shadows_and_cleanup(img)
            boosted = ImageProcessor.adjust_brightness_contrast(cleaned, brightness=1.1, contrast=1.2)
            return boosted
        return img

    @staticmethod
    def rotate_image(img: np.ndarray, angle: int) -> np.ndarray:
        angle = angle % 360
        if angle == 90:
            return cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
        elif angle == 180:
            return cv2.rotate(img, cv2.ROTATE_180)
        elif angle == 270:
            return cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
        return img
