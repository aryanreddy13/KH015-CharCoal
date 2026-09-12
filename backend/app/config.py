import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Locate .env in current dir, backend dir, or root
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir.parent
root_dir = backend_dir.parent

env_paths = [
    backend_dir / ".env",
    root_dir / ".env",
    current_dir / ".env",
    Path(".env"),
    Path("backend/.env"),
]

for p in env_paths:
    if p.exists():
        load_dotenv(p, override=True)
        break

class Settings(BaseSettings):
    PROJECT_NAME: str = "Sanjivani - Agentic Disaster Relief & Emergency Resource Coordinator"
    API_V1_STR: str = "/api"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./disaster.db")
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "*"
    ]
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # OpenAI Intelligence Integration (Backend-only)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # Resend Emergency Email
    ENABLE_RESEND: bool = os.getenv("ENABLE_RESEND", "false").lower() in ("true", "1", "yes")
    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "")
    RESEND_FROM_EMAIL: str = os.getenv("RESEND_FROM_EMAIL", "emergency-alerts@sanjivani-relief.gov")

    # PagerDuty Emergency Escalation
    ENABLE_PAGERDUTY: bool = os.getenv("ENABLE_PAGERDUTY", "false").lower() in ("true", "1", "yes")
    PAGERDUTY_API_KEY: str = os.getenv("PAGERDUTY_API_KEY", "")
    PAGERDUTY_ROUTING_KEY: str = os.getenv("PAGERDUTY_ROUTING_KEY", "")

    # Supabase Storage
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    SUPABASE_STORAGE_BUCKET: str = os.getenv("SUPABASE_STORAGE_BUCKET", "incident-photos")

    # Priority & Severity Scoring Configuration
    PRIORITY_WEIGHT_A: float = float(os.getenv("PRIORITY_WEIGHT_A", "1.0"))
    PRIORITY_MAX_URGENCY_SCORE: float = float(os.getenv("PRIORITY_MAX_URGENCY_SCORE", "10.0"))
    PRIORITY_FALLBACK_AFFECTED: int = int(os.getenv("PRIORITY_FALLBACK_AFFECTED", "1"))
    PRIORITY_THRESHOLD_LOW: float = float(os.getenv("PRIORITY_THRESHOLD_LOW", "3.0"))
    PRIORITY_THRESHOLD_MEDIUM: float = float(os.getenv("PRIORITY_THRESHOLD_MEDIUM", "6.0"))
    PRIORITY_THRESHOLD_HIGH: float = float(os.getenv("PRIORITY_THRESHOLD_HIGH", "8.0"))
    PRIORITY_THRESHOLD_CRITICAL: float = float(os.getenv("PRIORITY_THRESHOLD_CRITICAL", "9.0"))

    # Emergency Service Provider Contacts (No police phone number)
    NGO_EMERGENCY_NUMBER: str = os.getenv("NGO_EMERGENCY_NUMBER", "7977661625")
    FIRE_EMERGENCY_NUMBER: str = os.getenv("FIRE_EMERGENCY_NUMBER", "865247769")
    MEDICAL_EMERGENCY_NUMBER: str = os.getenv("MEDICAL_EMERGENCY_NUMBER", "9833259238")

    # Emergency Service Email Recipients (No police email)
    NGO_EMERGENCY_EMAIL: str = os.getenv("NGO_EMERGENCY_EMAIL", "aryanreddy2006@gmail.com")
    FIRE_EMERGENCY_EMAIL: str = os.getenv("FIRE_EMERGENCY_EMAIL", "danishsjain@gmail.com")
    MEDICAL_EMERGENCY_EMAIL: str = os.getenv("MEDICAL_EMERGENCY_EMAIL", "nairanikait7@gmail.com")

    # OpenStreetMap (OSM) & Routing Engine Config
    OSM_MAP_TILE_URL: str = os.getenv("OSM_MAP_TILE_URL", "https://tile.openstreetmap.org/{z}/{x}/{y}.png")
    OSRM_ROUTING_URL: str = os.getenv("OSRM_ROUTING_URL", "https://router.project-osrm.org/route/v1/driving")
    OVERPASS_API_URL: str = os.getenv("OVERPASS_API_URL", "https://overpass-api.de/api/interpreter")
    NOMINATIM_API_URL: str = os.getenv("NOMINATIM_API_URL", "https://nominatim.openstreetmap.org/search")

    # TomTom Maps & Routing API (Optional / Legacy)
    TOMTOM_API_KEY: str = os.getenv("TOMTOM_API_KEY", "")

    class Config:
        case_sensitive = True
        extra = "allow"

settings = Settings()
