"""
ANPR Pipeline — Automatic Number Plate Recognition

Full pipeline:
  Image → Vehicle Detection (YOLOv8) → Plate Detection → Crop → OCR → Normalize

Falls back gracefully at each stage if ML models are unavailable.
"""
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# Try to import OpenCV
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.warning("OpenCV not available.")

# Try to import YOLO
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    logger.warning("Ultralytics YOLO not available.")

from .ocr_engine import read_plate_text, EASYOCR_AVAILABLE
from ..integration.entity_resolver import normalize_plate, is_valid_plate_format


class ANPRPipeline:
    """
    Automatic Number Plate Recognition Pipeline.

    Stages:
    1. Load image
    2. Vehicle detection (YOLOv8n — optional)
    3. Plate region detection (heuristic or YOLO)
    4. OCR (EasyOCR)
    5. Plate normalization (EntityResolver)
    6. Fuzzy candidate generation for partial plates
    """

    def __init__(self):
        self.vehicle_model = None
        self._load_models()

    def _load_models(self):
        """Lazy-load YOLO model."""
        if YOLO_AVAILABLE:
            try:
                self.vehicle_model = YOLO("yolov8n.pt")
                logger.info("YOLOv8n loaded successfully.")
            except Exception as e:
                logger.warning(f"Could not load YOLOv8n: {e}")
                self.vehicle_model = None

    def _detect_vehicles(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect vehicles using YOLOv8."""
        if not YOLO_AVAILABLE or self.vehicle_model is None:
            return []

        vehicle_classes = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}
        results = self.vehicle_model(image, verbose=False)
        detections = []

        for result in results:
            for box in result.boxes:
                cls_id = int(box.cls[0])
                if cls_id in vehicle_classes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = float(box.conf[0])
                    detections.append({
                        "class": vehicle_classes[cls_id],
                        "confidence": conf,
                        "bbox": [x1, y1, x2, y2],
                    })

        return detections

    def _detect_plate_region(self, vehicle_img: np.ndarray) -> Optional[np.ndarray]:
        """
        Detect the number plate region within a vehicle image.
        Uses edge detection + contour analysis as a heuristic fallback.
        """
        if not CV2_AVAILABLE:
            return vehicle_img  # Return full image as fallback

        gray = cv2.cvtColor(vehicle_img, cv2.COLOR_BGR2GRAY) if len(vehicle_img.shape) == 3 else vehicle_img
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        plate_candidates = []
        h, w = vehicle_img.shape[:2]

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 500:
                continue
            rect = cv2.minAreaRect(contour)
            box_w, box_h = rect[1]
            if box_h == 0:
                continue
            aspect = box_w / box_h if box_w > box_h else box_h / box_w
            # License plates typically have 2:1 to 5:1 aspect ratio
            if 1.5 <= aspect <= 6.0:
                x, y, rw, rh = cv2.boundingRect(contour)
                # Must be in lower 2/3 of vehicle image (plates are below)
                if y > h * 0.2:
                    plate_candidates.append((area, x, y, rw, rh))

        if not plate_candidates:
            return vehicle_img

        # Take largest candidate
        plate_candidates.sort(key=lambda x: x[0], reverse=True)
        _, px, py, pw, ph = plate_candidates[0]
        # Add padding
        pad = 5
        px = max(0, px - pad)
        py = max(0, py - pad)
        pw = min(w - px, pw + 2 * pad)
        ph = min(h - py, ph + 2 * pad)
        return vehicle_img[py:py+ph, px:px+pw]

    def process_image_bytes(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Process an uploaded image and run the full ANPR pipeline.

        Returns a dict with:
            - plate: detected plate string (normalized)
            - raw_ocr: raw OCR output before normalization
            - ocr_confidence: OCR confidence score
            - vehicle_type: detected vehicle class
            - detected_color: color (heuristic)
            - detection_confidence: vehicle detection confidence
            - pipeline_stages: detailed stage-by-stage results
        """
        result = {
            "plate": None,
            "raw_ocr": None,
            "ocr_confidence": 0.0,
            "vehicle_type": None,
            "detected_color": None,
            "detection_confidence": 0.0,
            "is_valid_format": False,
            "pipeline_stages": {},
            "error": None,
        }

        if not CV2_AVAILABLE:
            result["error"] = "OpenCV not available. Please enter plate manually."
            return result

        try:
            # Stage 1: Decode image
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if image is None:
                result["error"] = "Could not decode image."
                return result
            result["pipeline_stages"]["image_loaded"] = True

            # Stage 2: Vehicle detection
            vehicles = self._detect_vehicles(image)
            if vehicles:
                best_vehicle = max(vehicles, key=lambda x: x["confidence"])
                result["vehicle_type"] = best_vehicle["class"]
                result["detection_confidence"] = best_vehicle["confidence"]
                x1, y1, x2, y2 = best_vehicle["bbox"]
                vehicle_crop = image[y1:y2, x1:x2]
                result["pipeline_stages"]["vehicle_detected"] = True
            else:
                vehicle_crop = image
                result["pipeline_stages"]["vehicle_detected"] = False

            # Stage 3: Color detection (simple dominant color)
            result["detected_color"] = self._detect_dominant_color(vehicle_crop)
            result["pipeline_stages"]["color_detected"] = True

            # Stage 4: Plate region detection
            plate_img = self._detect_plate_region(vehicle_crop)
            result["pipeline_stages"]["plate_region_detected"] = plate_img is not vehicle_crop

            # Stage 5: OCR
            raw_text, confidence = read_plate_text(plate_img)
            result["raw_ocr"] = raw_text
            result["ocr_confidence"] = confidence
            result["pipeline_stages"]["ocr_run"] = True

            # Stage 6: Normalize
            if raw_text:
                normalized = normalize_plate(raw_text)
                result["plate"] = normalized
                result["is_valid_format"] = is_valid_plate_format(normalized)
                result["pipeline_stages"]["normalized"] = True

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"ANPR pipeline error: {e}")

        return result

    def _detect_dominant_color(self, image: np.ndarray) -> Optional[str]:
        """Simple dominant color detection using HSV color space."""
        if not CV2_AVAILABLE or image is None or image.size == 0:
            return None

        try:
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            h, s, v = cv2.split(hsv)
            avg_h = float(np.mean(h))
            avg_s = float(np.mean(s))
            avg_v = float(np.mean(v))

            if avg_s < 30 and avg_v > 200:
                return "WHITE"
            elif avg_s < 30 and avg_v < 80:
                return "BLACK"
            elif avg_s < 50 and avg_v < 150:
                return "SILVER"
            elif avg_h < 15 or avg_h > 165:
                return "RED"
            elif 100 <= avg_h <= 130:
                return "BLUE"
            elif 35 <= avg_h <= 85:
                return "GREEN"
            elif 15 <= avg_h <= 35:
                return "YELLOW"
            else:
                return "OTHER"
        except Exception:
            return None
