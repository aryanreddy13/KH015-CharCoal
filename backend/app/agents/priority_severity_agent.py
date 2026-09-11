"""
Priority & Severity Scoring Agent
Stateless, deterministic, configuration-driven incident prioritization layer.
Calculates priority/severity scores and levels exclusively from the canonical IncidentAssessment.
Zero operational decisions, zero LLM calls, zero hallucinations.
"""

import math
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.config import settings
from app.schemas.schemas import (
    IncidentAssessment,
    PriorityAssessment,
    PriorityScoreComponents,
    PeopleScoreComponent,
    DisasterScoreComponent,
    UrgencyScoreComponent,
)

logger = logging.getLogger(__name__)

PRIORITY_SCORING_VERSION = "1.0"

# Application-level configurable scoring weights
DEFAULT_DISASTER_TYPE_SCORES: Dict[str, float] = {
    "EARTHQUAKE": 5.0,
    "BUILDING_COLLAPSE": 4.5,
    "TSUNAMI": 5.0,
    "FLOOD": 4.0,
    "FIRE": 4.0,
    "CYCLONE": 4.0,
    "LANDSLIDE": 3.5,
    "INDUSTRIAL_ACCIDENT": 3.5,
    "CHEMICAL_LEAK": 4.0,
    "STORM": 3.0,
    "ROAD_ACCIDENT": 2.5,
    "MEDICAL_EMERGENCY": 3.0,
    "UNKNOWN": 2.0,
}

DEFAULT_URGENCY_KEYWORD_SCORES: Dict[str, float] = {
    "dying": 3.0,
    "unconscious": 2.0,
    "critical": 2.0,
    "severely injured": 2.0,
    "trapped": 1.5,
    "collapsed": 1.5,
    "explosion": 2.0,
    "drowning": 2.0,
    "suffocating": 2.0,
    "cannot breathe": 2.0,
    "bleeding": 1.5,
    "severe bleeding": 2.0,
    "fire spreading": 1.5,
    "children trapped": 2.0,
    "under rubble": 2.0,
    "injured": 1.0,
    "missing": 1.0,
    "stranded": 1.0,
    "urgent": 0.8,
    "emergency": 0.8,
    "help": 0.5,
}

PRIORITY_LEVEL_RANKS: Dict[str, int] = {
    "CRITICAL": 4,
    "HIGH": 3,
    "MEDIUM": 2,
    "LOW": 1,
}


class PrioritySeverityAgent:
    """
    Stateless Priority & Severity Scoring Agent.
    Consumes IncidentAssessment -> produces PriorityAssessment.
    Answers: 'How urgent and severe is this incident based on current information?'
    """

    def __init__(
        self,
        disaster_type_scores: Optional[Dict[str, float]] = None,
        urgency_keyword_scores: Optional[Dict[str, float]] = None,
    ):
        self.disaster_type_scores = disaster_type_scores or dict(DEFAULT_DISASTER_TYPE_SCORES)
        self.urgency_keyword_scores = urgency_keyword_scores or dict(DEFAULT_URGENCY_KEYWORD_SCORES)

    def score_incident(
        self,
        assessment: IncidentAssessment,
    ) -> PriorityAssessment:
        """
        Calculates deterministic priority and severity score from canonical IncidentAssessment.
        Stateless: does not mutate or query database.
        """
        try:
            fallbacks_used: List[str] = []

            # 1. People Affected Component
            people_score, people_val, people_src, used_ppl_fb = self._calculate_people_score(assessment)
            if used_ppl_fb:
                fallbacks_used.append("affected_people")

            # 2. Disaster Type Component
            disaster_score, disaster_val, disaster_src, used_dst_fb = self._calculate_disaster_score(assessment)
            if used_dst_fb:
                fallbacks_used.append("disaster_type")

            # 3. Urgency Keywords Component
            urgency_score, matched_keywords = self._calculate_urgency_score(assessment)

            # 4. Total Zone Score
            # zone_score = log10(affected + 1) * weight_A + disaster_score + urgency_score
            raw_zone_score = people_score + disaster_score + urgency_score
            zone_score = round(raw_zone_score, 2)

            # 5. Priority Level Classification
            priority_level = self._classify_priority_level(zone_score)

            incident_id = getattr(assessment, "incident_id", None)
            logger.info(
                f"[PRIORITY_AGENT] incident_id={incident_id} status=SUCCESS score={zone_score} priority={priority_level} fallbacks={fallbacks_used}"
            )

            return PriorityAssessment(
                incident_id=incident_id,
                zone_score=zone_score,
                priority_level=priority_level,
                components=PriorityScoreComponents(
                    affected_people=PeopleScoreComponent(
                        value=people_val,
                        score=round(people_score, 2),
                        source=people_src,
                    ),
                    disaster_type=DisasterScoreComponent(
                        value=disaster_val,
                        score=round(disaster_score, 2),
                        source=disaster_src,
                    ),
                    urgency_keywords=UrgencyScoreComponent(
                        matched=matched_keywords,
                        score=round(urgency_score, 2),
                        source="NEED_ASSESSMENT",
                    ),
                ),
                fallbacks_used=fallbacks_used,
                scoring_version=PRIORITY_SCORING_VERSION,
                processed_at=datetime.utcnow().isoformat() + "Z",
            )
        except Exception as e:
            logger.error(f"[PRIORITY_AGENT] Scoring error: {e}", exc_info=True)
            # Safe baseline priority fallback - never crash intake
            return self._fallback_priority_assessment(assessment, str(e))

    def _calculate_people_score(
        self,
        assessment: IncidentAssessment,
    ) -> Tuple[float, Optional[int], str, bool]:
        """
        people_score = log10(scoring_affected_value + 1) * weight_A
        Preserves original null in assessment, using fallback for scoring calculation only.
        """
        weight_a = getattr(settings, "PRIORITY_WEIGHT_A", 1.0)
        fallback_affected = getattr(settings, "PRIORITY_FALLBACK_AFFECTED", 1)

        raw_affected = None
        source = "UNKNOWN"

        if assessment and assessment.people and assessment.people.affected:
            raw_affected = assessment.people.affected.value
            source = assessment.people.affected.source or "UNKNOWN"

        if raw_affected is not None and raw_affected >= 0:
            scoring_val = raw_affected
            used_fallback = False
            reported_val = raw_affected
        else:
            # Fallback for scoring only; reported_val remains None
            scoring_val = fallback_affected
            source = "SYSTEM_FALLBACK"
            used_fallback = True
            reported_val = None

        # log10(scoring_val + 1) * weight_A
        score = math.log10(scoring_val + 1) * weight_a
        return score, reported_val, source, used_fallback

    def _calculate_disaster_score(
        self,
        assessment: IncidentAssessment,
    ) -> Tuple[float, Optional[str], str, bool]:
        """
        Disaster type scoring via configurable mapping.
        """
        raw_type = None
        source = "UNKNOWN"

        if assessment and assessment.disaster:
            raw_type = assessment.disaster.type
            source = assessment.disaster.source or "UNKNOWN"

        if raw_type and str(raw_type).strip():
            norm_type = str(raw_type).strip().upper()
            if norm_type in self.disaster_type_scores:
                return self.disaster_type_scores[norm_type], norm_type, source, False
            else:
                # Type given but unrecognized
                return self.disaster_type_scores.get("UNKNOWN", 2.0), norm_type, source, True
        else:
            # Type is null/unspecified
            return self.disaster_type_scores.get("UNKNOWN", 2.0), None, "UNKNOWN", True

    def _calculate_urgency_score(
        self,
        assessment: IncidentAssessment,
    ) -> Tuple[float, List[str]]:
        """
        Aggregates matched urgency keywords up to PRIORITY_MAX_URGENCY_SCORE.
        Deterministic and case-insensitive.
        """
        max_urgency = getattr(settings, "PRIORITY_MAX_URGENCY_SCORE", 10.0)
        keywords = getattr(assessment, "urgency_keywords", []) or []

        if not keywords:
            return 0.0, []

        matched: List[str] = []
        total_score = 0.0
        seen_matched = set()

        for kw in keywords:
            if not kw or not isinstance(kw, str):
                continue
            norm_kw = kw.strip().lower()
            if not norm_kw:
                continue

            # Exact or substring match in dictionary
            matched_score = None
            if norm_kw in self.urgency_keyword_scores:
                matched_score = self.urgency_keyword_scores[norm_kw]
            else:
                # Check for partial multi-word match
                for dict_kw, d_score in self.urgency_keyword_scores.items():
                    if dict_kw in norm_kw or norm_kw in dict_kw:
                        matched_score = d_score
                        break

            if matched_score is not None and norm_kw not in seen_matched:
                matched.append(norm_kw)
                seen_matched.add(norm_kw)
                total_score += matched_score

        capped_score = min(total_score, max_urgency)
        return capped_score, matched

    def _classify_priority_level(self, score: float) -> str:
        """
        Maps numerical zone_score to priority level: LOW, MEDIUM, HIGH, CRITICAL.
        """
        th_crit = getattr(settings, "PRIORITY_THRESHOLD_CRITICAL", 9.0)
        th_high = getattr(settings, "PRIORITY_THRESHOLD_HIGH", 8.0)
        th_med = getattr(settings, "PRIORITY_THRESHOLD_MEDIUM", 6.0)

        if score >= th_crit:
            return "CRITICAL"
        elif score >= th_high:
            return "HIGH"
        elif score >= th_med:
            return "MEDIUM"
        else:
            return "LOW"

    def _fallback_priority_assessment(
        self,
        assessment: Optional[IncidentAssessment],
        error_msg: str,
    ) -> PriorityAssessment:
        incident_id = getattr(assessment, "incident_id", None) if assessment else None
        return PriorityAssessment(
            incident_id=incident_id,
            zone_score=3.0,
            priority_level="LOW",
            components=PriorityScoreComponents(
                affected_people=PeopleScoreComponent(
                    value=None,
                    score=0.3,
                    source="SYSTEM_FALLBACK",
                ),
                disaster_type=DisasterScoreComponent(
                    value="UNKNOWN",
                    score=2.0,
                    source="SYSTEM_FALLBACK",
                ),
                urgency_keywords=UrgencyScoreComponent(
                    matched=[],
                    score=0.0,
                    source="SYSTEM_FALLBACK",
                ),
            ),
            fallbacks_used=["scoring_error_fallback"],
            scoring_version=PRIORITY_SCORING_VERSION,
            processed_at=datetime.utcnow().isoformat() + "Z",
        )

    def sort_by_priority(self, incidents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Ranks incidents by priority level (CRITICAL > HIGH > MEDIUM > LOW),
        then zone_score descending, then timestamp.
        """
        def rank_key(item: Dict[str, Any]):
            level = item.get("priority_level") or "LOW"
            level_rank = PRIORITY_LEVEL_RANKS.get(level.upper(), 0)
            score = float(item.get("priority_score") or item.get("zone_score") or 0.0)
            created_at = item.get("created_at") or ""
            return (level_rank, score, created_at)

        return sorted(incidents, key=rank_key, reverse=True)


priority_severity_agent = PrioritySeverityAgent()
