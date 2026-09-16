"""
Vehicle API Routes

Handles: vehicle lookup, scan, history, insurance verification, security status
"""
import logging
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from ..integration.mediator import Mediator
from ..integration.entity_resolver import normalize_plate
from ..detection.anpr_pipeline import ANPRPipeline

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/vehicle", tags=["vehicle"])

# Shared instances (initialized once)
_mediator: Optional[Mediator] = None
_anpr: Optional[ANPRPipeline] = None


def get_mediator() -> Mediator:
    global _mediator
    if _mediator is None:
        _mediator = Mediator()
    return _mediator


def get_anpr() -> ANPRPipeline:
    global _anpr
    if _anpr is None:
        _anpr = ANPRPipeline()
    return _anpr


# ─────────────────────────────────────────────────────────────────────────────
# Request/Response Models
# ─────────────────────────────────────────────────────────────────────────────
class ManualSearchRequest(BaseModel):
    registration_number: str


class ScanResponse(BaseModel):
    plate: Optional[str]
    raw_ocr: Optional[str]
    ocr_confidence: float
    vehicle_type: Optional[str]
    detected_color: Optional[str]
    detection_confidence: float
    is_valid_format: bool
    error: Optional[str]


# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/scan")
async def scan_vehicle(file: UploadFile = File(...)):
    """
    Upload an image for ANPR processing.
    Runs vehicle detection + plate detection + OCR + normalization.
    Returns the detected plate number for integration lookup.
    """
    contents = await file.read()
    anpr = get_anpr()
    result = anpr.process_image_bytes(contents)
    return result


@router.get("/{registration_number}")
async def get_vehicle(registration_number: str):
    """
    Get the complete integrated vehicle view.
    Queries all 5 independent data sources via the Mediator.
    """
    normalized = normalize_plate(registration_number)
    if not normalized:
        raise HTTPException(status_code=400, detail="Invalid registration number format")

    mediator = get_mediator()
    result = mediator.integrate(normalized)
    return result


@router.get("/{registration_number}/history")
async def get_vehicle_history(registration_number: str):
    """Get all capture events for a vehicle (camera history)."""
    normalized = normalize_plate(registration_number)
    mediator = get_mediator()
    captures = mediator.get_all_captures(normalized)
    return {"registration_number": normalized, "captures": captures, "count": len(captures)}


@router.get("/{registration_number}/insurance")
async def get_vehicle_insurance(registration_number: str):
    """Get all insurance policies (including historical) for a vehicle."""
    normalized = normalize_plate(registration_number)
    mediator = get_mediator()
    policies = mediator.get_all_policies(normalized)
    return {"registration_number": normalized, "policies": policies, "count": len(policies)}


@router.get("/{registration_number}/security")
async def get_vehicle_security(registration_number: str):
    """Get theft/security cases for a vehicle."""
    normalized = normalize_plate(registration_number)
    mediator = get_mediator()
    cases = mediator.get_all_security_cases(normalized)
    return {"registration_number": normalized, "cases": cases, "count": len(cases)}


@router.get("/{registration_number}/reports")
async def get_vehicle_reports(registration_number: str):
    """Get Ministry of Transportation reports for a vehicle."""
    normalized = normalize_plate(registration_number)
    mediator = get_mediator()
    reports = mediator.get_all_ministry_reports(normalized)
    return {"registration_number": normalized, "reports": reports, "count": len(reports)}


@router.post("/search")
async def search_vehicle(request: ManualSearchRequest):
    """
    Manual plate entry — search and integrate vehicle info.
    Used as fallback when OCR is unavailable.
    """
    normalized = normalize_plate(request.registration_number)
    if not normalized:
        raise HTTPException(status_code=400, detail="Invalid registration number")

    mediator = get_mediator()
    result = mediator.integrate(normalized)
    return result
