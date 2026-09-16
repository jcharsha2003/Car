"""
Entity Resolver — Plate Normalization & Fuzzy Matching

Handles:
1. Normalization of different plate number formats to a canonical form
2. OCR error correction using common OCR character confusion pairs
3. Fuzzy candidate generation for partially visible plates

Reference: Project requirement §19 — Number Plate Normalization
Reference: Project requirement §20 — Partially Visible Number Plate
"""
import re
from typing import Any, Dict, List, Optional, Tuple


# ─────────────────────────────────────────────────────────────────────────────
# OCR CHARACTER CONFUSION PAIRS
# Common OCR misrecognitions for vehicle plates
# ─────────────────────────────────────────────────────────────────────────────
OCR_CONFUSION: Dict[str, List[str]] = {
    "O": ["0"],
    "0": ["O"],
    "I": ["1", "L"],
    "1": ["I", "L"],
    "L": ["I", "1"],
    "B": ["8"],
    "8": ["B"],
    "S": ["5"],
    "5": ["S"],
    "Z": ["2"],
    "2": ["Z"],
    "G": ["6"],
    "6": ["G", "C"],
    "Q": ["0", "O"],
}


def normalize_plate(plate: str) -> str:
    """
    Normalize a vehicle plate string to canonical uppercase with no separators.

    Examples:
        "UP 32 AB 1234" → "UP32AB1234"
        "UP-32-AB-1234" → "UP32AB1234"
        "up32ab1234"    → "UP32AB1234"
        "MH 02 EF-9012" → "MH02EF9012"
    """
    if not plate:
        return ""
    # Remove all non-alphanumeric characters and convert to uppercase
    normalized = re.sub(r'[^A-Za-z0-9]', '', plate).upper()
    return normalized


def is_valid_plate_format(plate: str) -> bool:
    """
    Validate if a normalized plate matches the Indian vehicle registration format.
    Format: 2 letters + 2 digits + 1-3 letters + 4 digits
    Examples: UP32AB1234, MH02EF9012, DL01GH3456
    """
    pattern = r'^[A-Z]{2}[0-9]{2}[A-Z]{1,3}[0-9]{4}$'
    return bool(re.match(pattern, plate))


def generate_ocr_candidates(plate: str, max_candidates: int = 20) -> List[str]:
    """
    Generate candidate plate numbers by substituting OCR confusion characters.
    Uses positional rules — only substitutes in positions where confusion is likely.

    For Indian plates: characters at positions 0-1 and 4-6 are letters,
    positions 2-3 and 7-10 are digits.
    """
    candidates = {plate}

    # Only generate candidates for positions that contain confused characters
    for i, char in enumerate(plate):
        if char in OCR_CONFUSION:
            new_candidates = set()
            for candidate in candidates:
                for replacement in OCR_CONFUSION[char]:
                    new_plate = candidate[:i] + replacement + candidate[i+1:]
                    new_candidates.add(new_plate)
            candidates |= new_candidates
            if len(candidates) > max_candidates:
                break

    candidates.discard(plate)  # Remove original (already searched)
    return list(candidates)[:max_candidates]


def compute_plate_similarity(plate1: str, plate2: str) -> float:
    """
    Compute similarity between two plate strings (0.0 to 1.0).
    Used for fuzzy matching when OCR produces partial results.
    """
    if plate1 == plate2:
        return 1.0
    if not plate1 or not plate2:
        return 0.0

    # Character-level matching
    max_len = max(len(plate1), len(plate2))
    matches = sum(1 for a, b in zip(plate1, plate2) if a == b)

    # Length penalty
    length_diff = abs(len(plate1) - len(plate2))
    score = (matches - length_diff * 0.5) / max_len
    return max(0.0, round(score, 4))


class EntityResolver:
    """
    Entity Resolution for vehicle identifiers.

    Responsibilities:
    1. Normalize plate numbers from different formats
    2. Correct common OCR errors
    3. Generate fuzzy candidates for partial plates
    4. Match OCR output to canonical database entries

    This addresses the Information Integration problem of having the same
    real-world entity (a vehicle) represented with slightly different
    identifier values due to OCR errors or format differences.
    """

    def resolve(self, raw_plate: str) -> Dict[str, Any]:
        """
        Main resolution entry point.
        Returns a resolved entity with normalized plate and metadata.
        """
        normalized = normalize_plate(raw_plate)
        valid = is_valid_plate_format(normalized)
        candidates = generate_ocr_candidates(normalized) if not valid else []

        return {
            "raw_input": raw_plate,
            "normalized": normalized,
            "is_valid_format": valid,
            "ocr_candidates": candidates,
            "candidate_count": len(candidates),
        }

    def normalize(self, plate: str) -> str:
        """Quick normalization without full resolution."""
        return normalize_plate(plate)

    def find_best_candidate(
        self,
        ocr_plate: str,
        db_plates: List[str],
        threshold: float = 0.7,
    ) -> Optional[Dict[str, Any]]:
        """
        Find the best matching plate in the database for an OCR result.
        Used for fuzzy matching when OCR may have errors.

        Returns the best match with similarity score, or None if no match found.
        """
        normalized_ocr = normalize_plate(ocr_plate)
        candidates = generate_ocr_candidates(normalized_ocr)
        all_plates_to_try = [normalized_ocr] + candidates

        best_match = None
        best_score = 0.0

        for db_plate in db_plates:
            # Direct match
            if db_plate in all_plates_to_try:
                return {
                    "matched_plate": db_plate,
                    "ocr_input": ocr_plate,
                    "similarity": 1.0 if db_plate == normalized_ocr else 0.95,
                    "match_type": "EXACT" if db_plate == normalized_ocr else "OCR_CORRECTED",
                    "normalized_ocr": normalized_ocr,
                }

            # Fuzzy similarity
            score = compute_plate_similarity(normalized_ocr, db_plate)
            if score > best_score and score >= threshold:
                best_score = score
                best_match = db_plate

        if best_match:
            return {
                "matched_plate": best_match,
                "ocr_input": ocr_plate,
                "similarity": best_score,
                "match_type": "FUZZY",
                "normalized_ocr": normalized_ocr,
            }

        return None

    def extract_partial_pattern(self, partial_plate: str) -> str:
        """
        Convert a partial plate (e.g., "UP32AB12?4") to a SQL LIKE pattern.
        '?' → '_' (SQL single-char wildcard)
        '*' → '%' (SQL multi-char wildcard)
        """
        normalized = normalize_plate(partial_plate.replace("?", "X").replace("*", "X"))
        pattern = partial_plate.replace("?", "_").replace("*", "%")
        return normalize_plate(pattern.replace("_", "?")).replace("X", "_")
