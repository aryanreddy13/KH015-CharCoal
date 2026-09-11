import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from app.services.storage_service import storage_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["Media & Photo Storage"])

@router.post("/photo")
async def upload_incident_photo(file: UploadFile = File(...)):
    """
    Accepts evidence photograph, stores it in Supabase Storage bucket `incident-photos`
    (or local static storage fallback), and returns the persistent photo URL.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be a valid image (JPEG, PNG, WEBP).",
        )

    # Max 5MB check
    file_bytes = await file.read()
    if len(file_bytes) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image size exceeds 5MB limit.",
        )

    success, url = storage_service.upload_photo(
        file_bytes=file_bytes,
        filename=file.filename or "incident.jpg",
        content_type=file.content_type,
    )

    if not success or not url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store incident photograph.",
        )

    return {
        "success": True,
        "photo_url": url,
        "filename": file.filename,
        "size_bytes": len(file_bytes),
    }
