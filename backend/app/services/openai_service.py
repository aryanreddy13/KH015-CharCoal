import json
import logging
from typing import Any, Dict, Optional
import httpx

from app.config import settings

logger = logging.getLogger(__name__)

NEED_ASSESSMENT_PROMPT_VERSION = "1.0"

SYSTEM_PROMPT = """You are the Sanjivini Disaster Incident Understanding & Extraction Engine.
Your sole job is strict, factual extraction of what the citizen actually reported.

CRITICAL EXTRACTION RULES:
1. ONLY extract what is explicitly stated in the description. Do NOT extrapolate or guess.
2. MISSING VALUES: If a count is not explicitly specified (e.g. "several people hurt", "many trapped", "water everywhere"), set that count field to null. NEVER convert missing counts to 0 or invented numbers.
3. DISASTER TYPE: Identify the primary disaster type (e.g. FLOOD, FIRE, EARTHQUAKE, CYCLONE, LANDSLIDE, BUILDING_COLLAPSE, INDUSTRIAL_ACCIDENT, CHEMICAL_LEAK, ROAD_ACCIDENT, TSUNAMI, STORM). If completely unknown, set to null.
4. PEOPLE COUNTS: Extract only explicit non-negative integers:
   - affected: count of people affected or null
   - injured: count of people injured or null
   - trapped: count of people trapped or null
   - missing: count of people missing or null
   - casualties: count of deaths/fatalities or null
5. EXPLICIT NEEDS: Extract ONLY resource categories that the user explicitly mentions needing or requesting (e.g. "we need drinking water" -> "WATER": true, "need food" -> "FOOD": true, "need medicine" -> "MEDICINE": true, "need rescue boats" -> "RESCUE": true, "send an ambulance" -> "AMBULANCE": true).
   Do NOT infer needs from situation (e.g. do NOT set "AMBULANCE": true merely because someone is injured unless medical/ambulance is explicitly mentioned/requested).
6. EXPLICIT REQUESTS: If user specifies an explicit quantity for a resource (e.g. "need water for 20 people", "send 2 ambulances"), extract {"resource_type": "WATER", "quantity": 20}. Do NOT calculate or multiply quantities.
7. URGENCY KEYWORDS: Extract key urgent phrases used by the user (e.g. "trapped", "bleeding", "unconscious", "fire spreading", "cannot breathe", "building collapsing").
8. FACTS: Extract 1 to 5 concise factual bullet points directly supported by the text.
9. NO CONFIDENCE SCORES: Do NOT include confidence metrics anywhere.

OUTPUT JSON FORMAT ONLY:
{
  "disaster_type": "FLOOD" | null,
  "people": {
    "affected": int | null,
    "injured": int | null,
    "trapped": int | null,
    "missing": int | null,
    "casualties": int | null
  },
  "needs": {
    "FOOD": true | false,
    "WATER": true | false,
    "SHELTER": true | false,
    "MEDICINE": true | false,
    "RESCUE": true | false,
    "AMBULANCE": true | false
  },
  "explicit_requests": [
    {"resource_type": "WATER", "quantity": 20}
  ],
  "urgency_keywords": ["trapped", "unconscious"],
  "facts": [
    "Flood water has entered the house",
    "Three people are trapped upstairs"
  ]
}
"""


class OpenAIService:
    """
    Backend-only service for LLM-powered natural language extraction.
    Stateless, resilient, and non-blocking.
    """

    def __init__(self):
        self.api_url = "https://api.openai.com/v1/chat/completions"

    @property
    def api_key(self) -> str:
        return settings.OPENAI_API_KEY.strip() if settings.OPENAI_API_KEY else ""

    @property
    def model(self) -> str:
        return settings.OPENAI_MODEL or "gpt-4o-mini"

    def is_available(self) -> bool:
        return bool(self.api_key)

    def extract_incident_data(
        self,
        description: str,
        form_context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Calls OpenAI Chat Completions with strict JSON extraction prompt.
        Returns parsed dictionary or None if unavailable/failed.
        """
        if not self.is_available() or not description or not description.strip():
            return None

        user_content = f"CITIZEN INCIDENT DESCRIPTION:\n\"\"\"\n{description.strip()}\n\"\"\""
        if form_context:
            user_content += f"\n\nACCOMPANYING FORM DATA:\n{json.dumps(form_context, default=str)}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.0,
            "response_format": {"type": "json_object"},
        }

        try:
            with httpx.Client(timeout=8.0) as client:
                res = client.post(self.api_url, headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    choices = data.get("choices", [])
                    if choices:
                        content_str = choices[0].get("message", {}).get("content", "{}")
                        parsed = json.loads(content_str)
                        return parsed
                    else:
                        logger.warning("OpenAI response contained no choices.")
                else:
                    logger.warning(f"OpenAI API returned HTTP {res.status_code}: {res.text[:200]}")
        except Exception as e:
            logger.warning(f"OpenAI extraction call failed (graceful fallback): {e}")

        return None


openai_service = OpenAIService()
