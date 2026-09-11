import os
import uuid
import base64
import logging
from typing import Optional, Tuple
from pathlib import Path
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

class StorageService:
    @staticmethod
    def upload_photo(
        file_bytes: bytes,
        filename: str,
        content_type: str = "image/jpeg",
    ) -> Tuple[bool, str]:
        """
        Uploads an incident evidence photograph.
        Tries Supabase Storage bucket `incident-photos` first;
        Falls back to local static storage if Supabase credentials are not configured.
        Returns: (success: bool, url_or_path: str)
        """
        clean_ext = filename.split(".")[-1].lower() if "." in filename else "jpg"
        if clean_ext not in ["jpg", "jpeg", "png", "webp"]:
            clean_ext = "jpg"

        unique_name = f"incident_{uuid.uuid4().hex[:10]}.{clean_ext}"

        # 1. Try Supabase Storage if configured
        if settings.SUPABASE_URL and settings.SUPABASE_KEY:
            try:
                bucket = settings.SUPABASE_STORAGE_BUCKET or "incident-photos"
                storage_endpoint = f"{settings.SUPABASE_URL.rstrip('/')}/storage/v1/object/{bucket}/{unique_name}"
                headers = {
                    "Authorization": f"Bearer {settings.SUPABASE_KEY}",
                    "apikey": settings.SUPABASE_KEY,
                    "Content-Type": content_type,
                }
                with httpx.Client(timeout=10.0) as client:
                    resp = client.post(storage_endpoint, content=file_bytes, headers=headers)
                    if resp.status_code in (200, 201):
                        public_url = f"{settings.SUPABASE_URL.rstrip('/')}/storage/v1/object/public/{bucket}/{unique_name}"
                        logger.info(f"Photo uploaded to Supabase Storage: {public_url}")
                        return True, public_url
                    else:
                        logger.warning(f"Supabase Storage responded {resp.status_code}: {resp.text}. Using local fallback.")
            except Exception as e:
                logger.warning(f"Supabase Storage upload error: {e}. Using local storage fallback.")

        # 2. Local File Fallback
        try:
            local_path = UPLOAD_DIR / unique_name
            with open(local_path, "wb") as f:
                f.write(file_bytes)
            
            # Form standard local URL accessible via FastAPI static mount
            url = f"/static/uploads/{unique_name}"
            logger.info(f"Photo saved locally: {url}")
            return True, url
        except Exception as err:
            logger.error(f"Local photo save failed: {err}")
            return False, ""

    @staticmethod
    def get_image_bytes(photo_url: str) -> Optional[Tuple[bytes, str]]:
        """
        Retrieves raw image bytes and filename for email attachment.
        Supports both remote HTTP(S) URLs and local /static/ uploads.
        """
        if not photo_url:
            return None

        try:
            # Check local path
            if photo_url.startswith("/static/uploads/"):
                rel_name = photo_url.replace("/static/uploads/", "")
                local_path = UPLOAD_DIR / rel_name
                if local_path.exists():
                    with open(local_path, "rb") as f:
                        return f.read(), rel_name

            # Check remote HTTP URL
            if photo_url.startswith("http://") or photo_url.startswith("https://"):
                with httpx.Client(timeout=8.0) as client:
                    res = client.get(photo_url)
                    if res.status_code == 200:
                        filename = photo_url.split("/")[-1].split("?")[0]
                        if not filename or "." not in filename:
                            filename = "incident-photo.jpg"
                        return res.content, filename

            # Check base64 data URI
            if photo_url.startswith("data:image/"):
                header, encoded = photo_url.split(",", 1)
                data = base64.b64decode(encoded)
                return data, "incident-evidence.jpg"

        except Exception as e:
            logger.warning(f"Could not retrieve image bytes from {photo_url}: {e}")

        return None

storage_service = StorageService()
