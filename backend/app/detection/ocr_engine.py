"""
OCR Engine — Plate Text Recognition

Attempts to read the plate text from a preprocessed image using EasyOCR.
Falls back gracefully if EasyOCR is unavailable.
"""
import logging
import re
from typing import Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# Try to import EasyOCR
try:
    import easyocr
    _reader = None  # Lazy-load to avoid slow startup

    def _get_reader():
        global _reader
        if _reader is None:
            logger.info("Loading EasyOCR reader (first call — may take a moment)...")
            _reader = easyocr.Reader(['en'], gpu=False, verbose=False)
        return _reader

    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    logger.warning("EasyOCR not available. OCR will use fallback.")

# ─────────────────────────────────────────────────────────────────────────────
# Indian license plate patterns
# Format examples: MH02EF9012, UP32AB1234, DL01GH3456, KA03IJ7890
# Pattern: 2 letters + 2 digits + 1-3 letters + 4 digits  (most common)
# Also handles: 2 letters + 2 digits + 4 digits (older plates)
# ─────────────────────────────────────────────────────────────────────────────
_PLATE_PATTERNS = [
    re.compile(r'^[A-Z]{2}\d{1,2}[A-Z]{1,3}\d{4}$'),   # standard: MH02EF9012
    re.compile(r'^[A-Z]{2}\d{2}\d{4}$'),                  # older: MH029012
    re.compile(r'^[A-Z]{2}\d{1,2}[A-Z]{2}\d{4}$'),       # 2-letter suffix variant
]


def _is_plate_format(text: str) -> bool:
    """Return True if `text` looks like an Indian vehicle registration number."""
    cleaned = re.sub(r'[^A-Z0-9]', '', text.upper())
    for pattern in _PLATE_PATTERNS:
        if pattern.match(cleaned):
            return True
    return False


def preprocess_plate_image(image: np.ndarray) -> np.ndarray:
    """
    Preprocess a plate image for better OCR accuracy.
    Steps: grayscale -> resize -> denoise -> threshold
    """
    import cv2
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    # Resize to a standard height
    h, w = gray.shape
    target_height = 64
    scale = target_height / h
    resized = cv2.resize(gray, (int(w * scale), target_height))
    # Denoise
    denoised = cv2.fastNlMeansDenoising(resized, h=10)
    # Threshold
    _, thresholded = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresholded


def read_plate_text(image: np.ndarray) -> Tuple[Optional[str], float]:
    """
    Run OCR on a plate image and return ONLY the license plate text.

    Strategy:
    1. Run EasyOCR with the alphanumeric allowlist.
    2. Among all detected text regions, prefer any that match an Indian
       license plate format (2-letter state code + digits + letters + digits).
    3. If multiple plate-format candidates exist, pick the highest confidence.
    4. If none match the plate format, try concatenating all pieces (plate
       may be split across regions e.g. 'MH02' + 'EF9012').
    5. True fallback: return highest-confidence single result.

    Returns: (plate_text, confidence)
    """
    if not EASYOCR_AVAILABLE:
        return None, 0.0

    try:
        reader = _get_reader()
        processed = preprocess_plate_image(image)
        results = reader.readtext(
            processed,
            allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -',
            paragraph=False,       # keep individual text boxes separate
            detail=1,
        )

        if not results:
            return None, 0.0

        # Clean each result and check plate format
        candidates = []
        fallback_candidates = []

        for (_, text, conf) in results:
            cleaned = re.sub(r'[^A-Z0-9]', '', text.upper())
            if not cleaned:
                continue
            if _is_plate_format(cleaned):
                candidates.append((cleaned, float(conf)))
            else:
                fallback_candidates.append((cleaned, float(conf)))

        # Prefer plate-format matches (direct hit — OCR read the full plate cleanly)
        if candidates:
            candidates.sort(key=lambda x: x[1], reverse=True)
            best_text, best_conf = candidates[0]
            logger.info(f"Plate-format OCR match: '{best_text}' (conf={best_conf:.2f})")
            return best_text, best_conf

        # Try concatenating all pieces — plate may be split across regions
        if fallback_candidates:
            # Sort by confidence and join
            joined_pieces = ''.join(
                t for t, _ in sorted(fallback_candidates, key=lambda x: x[1], reverse=True)
            )
            joined_cleaned = re.sub(r'[^A-Z0-9]', '', joined_pieces.upper())
            avg_conf = sum(c for _, c in fallback_candidates) / len(fallback_candidates)

            if _is_plate_format(joined_cleaned):
                logger.info(f"Joined OCR match: '{joined_cleaned}' (conf={avg_conf:.2f})")
                return joined_cleaned, avg_conf

            # True fallback: highest-confidence single result
            fallback_candidates.sort(key=lambda x: x[1], reverse=True)
            best_text, best_conf = fallback_candidates[0]
            logger.warning(
                f"No plate-format match; using top-confidence fallback: '{best_text}' (conf={best_conf:.2f})"
            )
            return best_text, best_conf

        return None, 0.0

    except Exception as e:
        logger.error(f"OCR error: {e}")
        return None, 0.0
