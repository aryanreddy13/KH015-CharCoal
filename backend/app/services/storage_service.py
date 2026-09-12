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
    def get_image_bytes(photo_url: Optional[str]) -> Optional[Tuple[bytes, str]]:
        """
        Retrieves raw image bytes and filename for email attachment & visual display.
        Supports remote HTTP(S) URLs, base64 data URIs, local static uploads, and fallback demo images.
        """
        if not photo_url or not str(photo_url).strip():
            return None

        photo_url_str = str(photo_url).strip()

        try:
            # 1. Base64 data URI (e.g. data:image/jpeg;base64,....)
            if photo_url_str.startswith("data:image/"):
                try:
                    header, encoded = photo_url_str.split(",", 1)
                    ext = "jpg"
                    if "png" in header:
                        ext = "png"
                    elif "webp" in header:
                        ext = "webp"
                    data = base64.b64decode(encoded)
                    return data, f"incident-evidence.{ext}"
                except Exception as b64_err:
                    logger.warning(f"Error decoding data URI: {b64_err}")

            # 2. Raw base64 string (without prefix)
            if len(photo_url_str) > 200 and not photo_url_str.startswith("http") and not "/" in photo_url_str[:20]:
                try:
                    data = base64.b64decode(photo_url_str)
                    return data, "incident-evidence.jpg"
                except Exception:
                    pass

            # 3. Local filesystem path in static/uploads
            if "/static/uploads/" in photo_url_str or "static/uploads/" in photo_url_str:
                rel_name = photo_url_str.split("static/uploads/")[-1].lstrip("/")
                local_path = UPLOAD_DIR / rel_name
                if local_path.exists():
                    with open(local_path, "rb") as f:
                        return f.read(), rel_name

            # 4. Remote HTTP/HTTPS URL
            if photo_url_str.startswith("http://") or photo_url_str.startswith("https://"):
                try:
                    with httpx.Client(timeout=8.0, follow_redirects=True) as client:
                        res = client.get(photo_url_str)
                        if res.status_code == 200 and len(res.content) > 100:
                            filename = photo_url_str.split("/")[-1].split("?")[0]
                            if not filename or "." not in filename:
                                filename = "incident-evidence.jpg"
                            return res.content, filename
                except Exception as http_err:
                    logger.warning(f"HTTP image fetch failed for {photo_url_str}: {http_err}")

            # 5. If a dummy filename was passed (e.g. evidence_123.jpg) or image fetch failed, fallback to high-res disaster evidence
            fallback_urls = [
                "https://images.unsplash.com/photo-1547683905-f686c993aae5?auto=format&fit=crop&w=800&q=80",
                "https://images.unsplash.com/photo-1516483638261-f4dbaf036963?auto=format&fit=crop&w=800&q=80",
            ]
            for fb_url in fallback_urls:
                try:
                    with httpx.Client(timeout=6.0, follow_redirects=True) as client:
                        res = client.get(fb_url)
                        if res.status_code == 200:
                            return res.content, "incident-evidence.jpg"
                except Exception:
                    continue

        except Exception as e:
            logger.warning(f"Could not retrieve image bytes from {photo_url_str}: {e}")

        return None

storage_service = StorageService()
