"""
Need & Assessment Agent
System's Incident Understanding and Normalization Layer.
Transforms raw citizen input into clean, structured, validated canonical incident JSON.
Stateless and pure: answers "What did the citizen tell us?" without making operational decisions.
"""

import re
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.schemas.schemas import (
    IncidentAssessment,
    DisasterAssessment,
    PeopleAssessment,
    FactualNumber,
    ExplicitResourceRequest,
    ExtractionMetadata,
)
from app.config import settings

logger = logging.getLogger(__name__)

NEED_ASSESSMENT_PROMPT_VERSION = "1.0"


class NeedAssessmentAgent:
    """
    Stateless Need & Assessment Agent.
    Converts raw citizen report or SOS into canonical IncidentAssessment.
    Answers: 'What did the citizen tell us?'
    Does NOT calculate severity, priority, resource counts, or dispatches.
    """

    SUPPORTED_DISASTER_TYPES = [
        "FLOOD",
        "FIRE",
        "EARTHQUAKE",
        "CYCLONE",
        "LANDSLIDE",
        "BUILDING_COLLAPSE",
        "INDUSTRIAL_ACCIDENT",
        "CHEMICAL_LEAK",
        "ROAD_ACCIDENT",
        "HEATWAVE",
        "TSUNAMI",
        "STORM",
    ]

    URGENCY_PATTERN = re.compile(
        r"\b(trapped|unconscious|severe bleeding|bleeding|collapse|collapsing|critical|drowning|choking|suffocating|cannot breathe|burning|smoke|fire spreading|children trapped|infant|pregnant|heart attack|buried|under rubble|emergency|immediate help|life threatening)\b",
        re.IGNORECASE,
    )

    def assess_incident(
        self,
        incident_data: Dict[str, Any],
        input_mode: Optional[str] = None,
    ) -> IncidentAssessment:
        """
        Main entry point for incident understanding and normalization.
        Stateless: does not mutate or query database directly.
        """
        # 1. Determine input mode
        mode = (input_mode or incident_data.get("input_mode") or "REPORT").upper()
        if "SOS" in mode:
            mode = "SOS"
        else:
            mode = "REPORT"

        incident_id = incident_data.get("incident_id") or incident_data.get("id")
        lat = float(incident_data.get("latitude", 0.0))
        lon = float(incident_data.get("longitude", 0.0))
        location = {"latitude": lat, "longitude": lon}

        description = (incident_data.get("description") or "").strip()

        # Check if description is trivial/default SOS signal
        is_default_sos_desc = description.upper() in (
            "",
            "EMERGENCY SOS TRIGGERED",
            "SOS ACTIVATED",
            "CITIZEN SOS BEACON",
        )

        # 2. Mode B: One-Tap SOS (GPS-only with no descriptive natural language)
        if mode == "SOS" and is_default_sos_desc and not self._has_explicit_form_counts(incident_data):
            logger.info(f"[NEED_ASSESSMENT] incident_id={incident_id} input_mode=SOS source=SYSTEM status=SUCCESS")
            return IncidentAssessment(
                incident_id=incident_id,
                input_mode="SOS",
                location=location,
                disaster=DisasterAssessment(type=None, source="UNKNOWN"),
                people=PeopleAssessment(
                    affected=FactualNumber(value=None, source="UNKNOWN"),
                    injured=FactualNumber(value=None, source="UNKNOWN"),
                    trapped=FactualNumber(value=None, source="UNKNOWN"),
                    missing=FactualNumber(value=None, source="UNKNOWN"),
                    casualties=FactualNumber(value=None, source="UNKNOWN"),
                ),
                needs={
                    "FOOD": False,
                    "WATER": False,
                    "SHELTER": False,
                    "MEDICINE": False,
                    "RESCUE": False,
                    "AMBULANCE": False,
                },
                explicit_requests=[],
                urgency_keywords=[],
                facts=[],
                extraction_metadata=ExtractionMetadata(
                    agent="NEED_ASSESSMENT",
                    source="SYSTEM",
                    version="1.0",
                    prompt_version=NEED_ASSESSMENT_PROMPT_VERSION,
                    model=None,
                    processed_at=datetime.utcnow().isoformat() + "Z",
                ),
            )

        # 3. Mode A: Detailed Report or SOS with description
        # Step A: Authoritative Form Inputs
        form_disaster, form_disaster_source = self._extract_form_disaster(incident_data)
        form_people = self._extract_form_people(incident_data)
        form_needs, form_requests = self._extract_form_needs_and_requests(incident_data)

        # Step B: Natural Language Extraction from description
        llm_extracted: Optional[Dict[str, Any]] = None
        extraction_source = "SYSTEM"

        if description and not is_default_sos_desc:
            # Try OpenAI Extraction
            try:
                from app.services.openai_service import openai_service
                llm_extracted = openai_service.extract_incident_data(
                    description=description,
                    form_context={
                        "disaster_type": form_disaster,
                        "people": {k: v[0] for k, v in form_people.items() if v[0] is not None},
                    },
                )
                if isinstance(llm_extracted, dict):
                    extraction_source = "OPENAI"
                else:
                    llm_extracted = None
            except Exception as e:
                logger.warning(f"OpenAI service failed during need assessment: {e}")
                llm_extracted = None

            # If OpenAI unavailable, failed, or returned invalid non-dict, use deterministic fallback
            if not isinstance(llm_extracted, dict):
                llm_extracted = self._deterministic_fallback_extraction(description)
                extraction_source = "DETERMINISTIC_FALLBACK"

        # Step C: Merge according to strict Information Precedence
        # 1. Structured Form Input (Authoritative)
        # 2. LLM Extracted from user description
        # 3. Missing stays null

        final_disaster, disaster_src = self._resolve_disaster_type(
            form_disaster=form_disaster,
            form_source=form_disaster_source,
            llm_disaster=llm_extracted.get("disaster_type") if llm_extracted else None,
            extraction_source=extraction_source,
        )

        final_people = self._resolve_people(
            form_people=form_people,
            llm_people=llm_extracted.get("people") if llm_extracted else None,
            extraction_source=extraction_source,
        )

        final_needs = self._resolve_needs(
            form_needs=form_needs,
            llm_needs=llm_extracted.get("needs") if llm_extracted else None,
        )

        final_requests = self._resolve_explicit_requests(
            form_requests=form_requests,
            llm_requests=llm_extracted.get("explicit_requests") if llm_extracted else None,
            extraction_source=extraction_source,
        )

        # Facts & Urgency
        urgency_keywords = self._extract_urgency_keywords(description, llm_extracted)
        facts = self._extract_facts(description, llm_extracted, form_disaster, final_disaster)

        meta_status = "SUCCESS" if extraction_source != "DETERMINISTIC_FALLBACK" else "FALLBACK"
        logger.info(
            f"[NEED_ASSESSMENT] incident_id={incident_id} input_mode={mode} source={extraction_source} status={meta_status}"
        )

        return IncidentAssessment(
            incident_id=incident_id,
            input_mode=mode,
            location=location,
            disaster=DisasterAssessment(type=final_disaster, source=disaster_src),
            people=final_people,
            needs=final_needs,
            explicit_requests=final_requests,
            urgency_keywords=urgency_keywords,
            facts=facts,
            extraction_metadata=ExtractionMetadata(
                agent="NEED_ASSESSMENT",
                source=extraction_source,
                version="1.0",
                prompt_version=NEED_ASSESSMENT_PROMPT_VERSION,
                model=settings.OPENAI_MODEL if extraction_source == "OPENAI" else None,
                processed_at=datetime.utcnow().isoformat() + "Z",
            ),
        )

    def _has_explicit_form_counts(self, data: Dict[str, Any]) -> bool:
        keys = ["people_affected", "people_injured", "injured_people", "people_trapped", "people_missing", "missing_people", "casualties"]
        return any(data.get(k) is not None for k in keys)

    def _extract_form_disaster(self, data: Dict[str, Any]) -> Tuple[Optional[str], str]:
        raw = data.get("disaster_type")
        if raw and str(raw).strip() and str(raw).upper() != "NONE":
            norm = str(raw).strip().upper()
            return norm, "USER_FORM"
        return None, "UNKNOWN"

    def _extract_form_people(self, data: Dict[str, Any]) -> Dict[str, Tuple[Optional[int], str]]:
        def get_valid_int(val: Any) -> Optional[int]:
            if val is None:
                return None
            try:
                i = int(val)
                return i if i >= 0 else None
            except (ValueError, TypeError):
                return None

        affected = get_valid_int(data.get("people_affected"))
        injured = get_valid_int(data.get("people_injured") if data.get("people_injured") is not None else data.get("injured_people"))
        trapped = get_valid_int(data.get("people_trapped"))
        missing = get_valid_int(data.get("people_missing") if data.get("people_missing") is not None else data.get("missing_people"))
        casualties = get_valid_int(data.get("casualties"))

        return {
            "affected": (affected, "USER_FORM" if affected is not None else "UNKNOWN"),
            "injured": (injured, "USER_FORM" if injured is not None else "UNKNOWN"),
            "trapped": (trapped, "USER_FORM" if trapped is not None else "UNKNOWN"),
            "missing": (missing, "USER_FORM" if missing is not None else "UNKNOWN"),
            "casualties": (casualties, "USER_FORM" if casualties is not None else "UNKNOWN"),
        }

    def _extract_form_needs_and_requests(self, data: Dict[str, Any]) -> Tuple[Dict[str, bool], List[ExplicitResourceRequest]]:
        needs: Dict[str, bool] = {}
        requests: List[ExplicitResourceRequest] = []

        mapping = [
            ("food_required", "food_quantity", "FOOD"),
            ("water_required", "water_quantity", "WATER"),
            ("shelter_required", "shelter_quantity", "SHELTER"),
            ("medicine_required", "medicine_quantity", "MEDICINE"),
            ("rescue_required", "rescue_units_required", "RESCUE"),
            ("ambulance_required", "ambulances_required", "AMBULANCE"),
        ]

        for req_key, qty_key, res_type in mapping:
            is_req = bool(data.get(req_key, False))
            qty = data.get(qty_key)
            valid_qty = None
            if qty is not None:
                try:
                    q = int(qty)
                    if q > 0:
                        valid_qty = q
                except (ValueError, TypeError):
                    pass

            if is_req or valid_qty is not None:
                needs[res_type] = True
                if valid_qty is not None:
                    requests.append(
                        ExplicitResourceRequest(
                            resource_type=res_type,
                            quantity=valid_qty,
                            source="USER_FORM",
                        )
                    )

        # Also check required_resources list
        req_list = data.get("required_resources") or []
        for r in req_list:
            r_upper = str(r).strip().upper()
            if "FOOD" in r_upper:
                needs["FOOD"] = True
            elif "WATER" in r_upper:
                needs["WATER"] = True
            elif "SHELTER" in r_upper:
                needs["SHELTER"] = True
            elif "MEDIC" in r_upper:
                needs["MEDICINE"] = True
            elif "RESCUE" in r_upper:
                needs["RESCUE"] = True
            elif "AMBULANCE" in r_upper:
                needs["AMBULANCE"] = True

        return needs, requests

    def _resolve_disaster_type(
        self,
        form_disaster: Optional[str],
        form_source: str,
        llm_disaster: Optional[str],
        extraction_source: str,
    ) -> Tuple[Optional[str], str]:
        # Form wins if provided
        if form_disaster:
            return form_disaster, "USER_FORM"

        if llm_disaster:
            norm = str(llm_disaster).strip().upper()
            if norm and norm != "NONE" and norm != "UNKNOWN":
                return norm, "LLM_EXTRACTED" if extraction_source == "OPENAI" else "DETERMINISTIC_FALLBACK"

        return None, "UNKNOWN"

    def _resolve_people(
        self,
        form_people: Dict[str, Tuple[Optional[int], str]],
        llm_people: Optional[Dict[str, Any]],
        extraction_source: str,
    ) -> PeopleAssessment:
        result = {}
        llm_p = llm_people or {}

        def get_valid_int(val: Any) -> Optional[int]:
            if val is None:
                return None
            try:
                i = int(val)
                return i if i >= 0 else None
            except (ValueError, TypeError):
                return None

        fields = ["affected", "injured", "trapped", "missing", "casualties"]
        for field in fields:
            form_val, form_src = form_people[field]
            if form_val is not None:
                result[field] = FactualNumber(value=form_val, source="USER_FORM")
            else:
                raw_llm_val = llm_p.get(field)
                if isinstance(raw_llm_val, dict):
                    raw_llm_val = raw_llm_val.get("value")
                llm_val = get_valid_int(raw_llm_val)
                if llm_val is not None:
                    src = "LLM_EXTRACTED" if extraction_source == "OPENAI" else "DETERMINISTIC_FALLBACK"
                    result[field] = FactualNumber(value=llm_val, source=src)
                else:
                    result[field] = FactualNumber(value=None, source="UNKNOWN")

        return PeopleAssessment(**result)

    def _resolve_needs(
        self,
        form_needs: Dict[str, bool],
        llm_needs: Optional[Dict[str, Any]],
    ) -> Dict[str, bool]:
        combined: Dict[str, bool] = {
            "FOOD": False,
            "WATER": False,
            "SHELTER": False,
            "MEDICINE": False,
            "RESCUE": False,
            "AMBULANCE": False,
        }
        for k, v in form_needs.items():
            if bool(v) is True:
                combined[str(k).upper()] = True

        if llm_needs and isinstance(llm_needs, dict):
            for k, v in llm_needs.items():
                if bool(v) is True:
                    combined[str(k).upper()] = True
        return combined

    def _resolve_explicit_requests(
        self,
        form_requests: List[ExplicitResourceRequest],
        llm_requests: Optional[List[Dict[str, Any]]],
        extraction_source: str,
    ) -> List[ExplicitResourceRequest]:
        requests = list(form_requests)
        existing_types = {r.resource_type for r in requests}

        if llm_requests and isinstance(llm_requests, list):
            for req in llm_requests:
                if isinstance(req, dict):
                    rtype = str(req.get("resource_type", "")).strip().upper()
                    raw_qty = req.get("quantity")
                    qty = None
                    if raw_qty is not None:
                        try:
                            q = int(raw_qty)
                            if q > 0:
                                qty = q
                        except (ValueError, TypeError):
                            pass

                    if rtype and rtype not in existing_types and qty is not None:
                        requests.append(
                            ExplicitResourceRequest(
                                resource_type=rtype,
                                quantity=qty,
                                source="LLM_EXTRACTED" if extraction_source == "OPENAI" else "USER_DESCRIPTION",
                            )
                        )
                        existing_types.add(rtype)

        return requests

    def _extract_urgency_keywords(
        self,
        description: str,
        llm_extracted: Optional[Dict[str, Any]],
    ) -> List[str]:
        keywords_set = set()
        if llm_extracted and isinstance(llm_extracted.get("urgency_keywords"), list):
            for kw in llm_extracted["urgency_keywords"]:
                if kw and isinstance(kw, str) and kw.strip():
                    keywords_set.add(kw.strip().lower())

        if description:
            matches = self.URGENCY_PATTERN.findall(description)
            for m in matches:
                keywords_set.add(m.strip().lower())

        return sorted(list(keywords_set))

    def _extract_facts(
        self,
        description: str,
        llm_extracted: Optional[Dict[str, Any]],
        form_disaster: Optional[str],
        final_disaster: Optional[str],
    ) -> List[str]:
        facts = []
        if llm_extracted and isinstance(llm_extracted.get("facts"), list):
            for f in llm_extracted["facts"]:
                if f and isinstance(f, str) and f.strip():
                    facts.append(f.strip())

        if not facts and description:
            # Fallback: split sentences into concise facts
            sentences = [s.strip() for s in re.split(r"[.!?\n]+", description) if s.strip()]
            facts.extend(sentences[:4])

        # If there is a secondary situation mentioned in description that differs from form disaster
        if description and form_disaster:
            desc_upper = description.upper()
            for d in self.SUPPORTED_DISASTER_TYPES:
                if d != form_disaster and d in desc_upper:
                    mention_fact = f"{d.title()} reported in description/vicinity"
                    if not any(d.lower() in f.lower() for f in facts):
                        facts.append(mention_fact)

        return facts[:6]

    def _deterministic_fallback_extraction(self, description: str) -> Dict[str, Any]:
        """
        Regex and keyword-based fallback when OpenAI is offline or unavailable.
        Strictly factual with no hallucinated counts.
        """
        desc_lower = description.lower()

        # 1. Identify disaster type from keywords
        disaster_type = None
        for dtype in self.SUPPORTED_DISASTER_TYPES:
            terms = [dtype.lower(), dtype.replace("_", " ").lower()]
            if any(t in desc_lower for t in terms):
                disaster_type = dtype
                break

        # 2. Extract numbers associated with specific people states
        # e.g., "3 people are trapped", "two injured", "10 trapped"
        num_word_map = {
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
            "twenty": 20, "thirty": 30, "fifty": 50, "hundred": 100
        }

        def parse_num(val_str: str) -> Optional[int]:
            val_str = val_str.strip().lower()
            if val_str.isdigit():
                return int(val_str)
            return num_word_map.get(val_str)

        trapped = None
        m_trapped = re.search(r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+(?:people\s+)?(?:are\s+)?trapped\b", desc_lower)
        if m_trapped:
            trapped = parse_num(m_trapped.group(1))

        injured = None
        m_injured = re.search(r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+(?:people\s+)?(?:are\s+)?(?:injured|hurt)\b", desc_lower)
        if m_injured:
            injured = parse_num(m_injured.group(1))

        missing = None
        m_missing = re.search(r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+(?:people\s+)?(?:are\s+)?missing\b", desc_lower)
        if m_missing:
            missing = parse_num(m_missing.group(1))

        affected = None
        m_affected = re.search(r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+(?:people\s+)?(?:are\s+)?affected\b", desc_lower)
        if m_affected:
            affected = parse_num(m_affected.group(1))

        casualties = None
        m_dead = re.search(r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+(?:people\s+)?(?:dead|killed|casualties)\b", desc_lower)
        if m_dead:
            casualties = parse_num(m_dead.group(1))

        # 3. Explicit needs & requests
        needs: Dict[str, bool] = {}
        requests: List[Dict[str, Any]] = []

        if re.search(r"\b(need|require|want|send)\s+(?:drinking\s+|clean\s+)?water\b", desc_lower) or "no drinking water" in desc_lower or "no clean water" in desc_lower:
            needs["WATER"] = True
            m_wqty = re.search(r"\bwater\s+for\s+(\d+)\b", desc_lower)
            if m_wqty:
                requests.append({"resource_type": "WATER", "quantity": int(m_wqty.group(1))})

        if re.search(r"\b(need|require|want|send)\s+food\b", desc_lower) or "no food" in desc_lower or "food shortage" in desc_lower:
            needs["FOOD"] = True
            m_fqty = re.search(r"\bfood\s+for\s+(\d+)\b", desc_lower)
            if m_fqty:
                requests.append({"resource_type": "FOOD", "quantity": int(m_fqty.group(1))})

        if re.search(r"\b(need|require|want|send)\s+shelter\b", desc_lower) or "homeless" in desc_lower:
            needs["SHELTER"] = True

        if re.search(r"\b(need|require|want|send)\s+(?:medicine|medical\s+help|first\s+aid)\b", desc_lower):
            needs["MEDICINE"] = True

        if re.search(r"\b(need|send)\s+(?:rescue|boats?)\b", desc_lower):
            needs["RESCUE"] = True

        if re.search(r"\b(need|send)\s+ambulance\b", desc_lower):
            needs["AMBULANCE"] = True
            m_aqty = re.search(r"(\d+)\s+ambulances?", desc_lower)
            if m_aqty:
                requests.append({"resource_type": "AMBULANCE", "quantity": int(m_aqty.group(1))})

        # 4. Urgency keywords
        urgency_matches = self.URGENCY_PATTERN.findall(description)

        # 5. Facts
        facts = [s.strip() for s in re.split(r"[.!?\n]+", description) if s.strip()][:3]

        return {
            "disaster_type": disaster_type,
            "people": {
                "affected": affected,
                "injured": injured,
                "trapped": trapped,
                "missing": missing,
                "casualties": casualties,
            },
            "needs": needs,
            "explicit_requests": requests,
            "urgency_keywords": list(set(m.lower() for m in urgency_matches)),
            "facts": facts,
        }


need_assessment_agent = NeedAssessmentAgent()
