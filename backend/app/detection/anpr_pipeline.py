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
        """Lazy-load YOLO models."""
        if YOLO_AVAILABLE:
            try:
                # We load both the general vehicle detector and the specialized plate detector
                self.vehicle_model = YOLO("yolov8n.pt")
                plate_model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "plate_model.pt")
                if os.path.exists(plate_model_path):
                    self.plate_model = YOLO(plate_model_path)
                    logger.info("YOLOv8 vehicle & plate models loaded successfully.")
                else:
                    self.plate_model = None
                    logger.warning(f"Plate model not found at {plate_model_path}")
            except Exception as e:
                logger.warning(f"Could not load YOLO models: {e}")
                self.vehicle_model = None
                self.plate_model = None

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

    def _detect_plate_candidates(self, vehicle_img: np.ndarray) -> List[np.ndarray]:
        """
        Detect number plate region using a state-of-the-art YOLOv8 license plate model.
        Returns a list of candidate plate crops (best first) + fallbacks.
        """
        candidates = []
        
        # ─── PRIMARY METHOD: YOLOv8 Plate Detection ───
        if YOLO_AVAILABLE and hasattr(self, 'plate_model') and self.plate_model is not None:
            results = self.plate_model(vehicle_img, verbose=False)
            plate_detections = []
            
            for result in results:
                for box in result.boxes:
                    # Collect all detections (license plate class is usually 0)
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = float(box.conf[0])
                    plate_detections.append({
                        "bbox": [x1, y1, x2, y2],
                        "confidence": conf
                    })
            
            # Sort by confidence
            plate_detections.sort(key=lambda x: x["confidence"], reverse=True)
            
            for det in plate_detections:
                x1, y1, x2, y2 = det["bbox"]
                # Add generous padding so edge characters (like 'H') are not clipped
                pad = 10
                h, w = vehicle_img.shape[:2]
                x1 = max(0, x1 - pad)
                y1 = max(0, y1 - pad)
                x2 = min(w, x2 + pad)
                y2 = min(h, y2 + pad)
                
                plate_crop = vehicle_img[y1:y2, x1:x2]
                if plate_crop.size > 0:
                    candidates.append(plate_crop)
                    # Also add a 2x upscaled version for better OCR on small/blurry plates
                    upscaled = cv2.resize(plate_crop, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
                    candidates.append(upscaled)
                    logger.info(f"YOLO Plate Crop: {x2-x1}x{y2-y1} px, conf={det['confidence']:.2f}")

        # ─── FALLBACK 1: Lower third of vehicle (plates are always at the bottom) ───
        h, w = vehicle_img.shape[:2]
        lower_third = vehicle_img[int(h * 0.55):h, :]
        if lower_third.size > 0:
            candidates.append(lower_third)

        # ─── FALLBACK 2: Full image ───
        candidates.append(vehicle_img)

        logger.info(f"Total plate candidates: {len(candidates)}")
        return candidates

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

            # Stage 2: Vehicle detection (YOLO)
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

            # Stage 3: Color detection
            result["detected_color"] = self._detect_dominant_color(vehicle_crop)
            result["pipeline_stages"]["color_detected"] = True

            # Stage 4: Plate region detection — returns ranked candidates
            plate_candidates = self._detect_plate_candidates(vehicle_crop)
            result["pipeline_stages"]["plate_region_detected"] = len(plate_candidates) > 1

            # Stage 5: Multi-pass OCR — try each candidate until we get a valid plate
            # Also try an upscaled version of each candidate for small/blurry plates
            best_text, best_conf = None, 0.0
            for candidate in plate_candidates:
                # Try original size
                text, conf = read_plate_text(candidate)
                if text and conf > best_conf:
                    best_text, best_conf = text, conf
                    if is_valid_plate_format(normalize_plate(text)):
                        break  # Found a valid format — stop searching

                # Try 2x upscaled (helps with small plates)
                if candidate.shape[0] < 80:
                    upscaled = cv2.resize(candidate, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
                    text2, conf2 = read_plate_text(upscaled)
                    if text2 and conf2 > best_conf:
                        best_text, best_conf = text2, conf2
                        if is_valid_plate_format(normalize_plate(text2)):
                            break

            result["raw_ocr"] = best_text
            result["ocr_confidence"] = best_conf
            result["pipeline_stages"]["ocr_run"] = True

            # Stage 6: Normalize
            if best_text:
                normalized = normalize_plate(best_text)
                result["plate"] = normalized
                result["is_valid_format"] = is_valid_plate_format(normalized)
                result["pipeline_stages"]["normalized"] = True

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"ANPR pipeline error: {e}", exc_info=True)

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
